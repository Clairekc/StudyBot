# ============================================================
#  StudyBot — scheduler.py  (version finale)
#  Autonomer Hintergrund-Scheduler
# ============================================================

import threading
import time
import json
import os
import sys
from datetime import datetime, timedelta

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE_DIR, "python"))

TASKS_DIR    = os.path.join(BASE_DIR, "daten", "tasks")
PROFILE_DIR  = os.path.join(BASE_DIR, "daten", "profile")
LOG_FILE     = os.path.join(BASE_DIR, "daten", "scheduler_log.json")
CHECK_INTERVAL = 30
TOLERANZ_SEK   = 90  # 90 secondes de tolérance

_scheduler_aktiv = threading.Event()
_scheduler_aktiv.set()


def _log(nachricht, typ="info"):
    eintrag = {"zeit": str(datetime.now()), "typ": typ, "nachricht": nachricht}
    log = []
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, "r", encoding="utf-8") as f:
                log = json.load(f)
        except Exception:
            log = []
    log.append(eintrag)
    log = log[-100:]
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    try:
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            json.dump(log, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def _ist_jetzt(ziel_zeit_str):
    try:
        ziel = datetime.fromisoformat(ziel_zeit_str)
        jetzt = datetime.now()
        diff = abs((ziel - jetzt).total_seconds())
        return diff <= TOLERANZ_SEK
    except Exception:
        return False


def _arduino_signal_senden(titel, prioritaet):
    try:
        import arduino_control
        verbindung = arduino_control.arduino_verbinden()
        arduino_control.vollstaendiger_erinnerungs_zyklus(verbindung, titel, prioritaet)
        _log(f"Arduino-Signal gesendet: '{titel}' ({prioritaet})", "signal")
    except Exception as e:
        _log(f"Arduino-Fehler: {e}", "fehler")


def _anwesenheit_pruefen(nutzer_id):
    """
    Prüft ob die richtige Person vor der Kamera ist.
    Gibt True zurück nur wenn die Person erkannt wird.
    Gibt False zurück wenn jemand anderes oder niemand erkannt wird.
    """
    try:
        import cv2
        from face_recognition_module import nutzer_erkennen

        kamera = cv2.VideoCapture(0)
        if not kamera.isOpened():
            # Kamera nicht verfügbar — trotzdem senden
            _log("Kamera nicht verfügbar, Signal trotzdem senden", "warnung")
            return True

        frame = None
        for _ in range(5):
            ret, frame = kamera.read()
        kamera.release()
        cv2.destroyAllWindows()

        if not ret or frame is None:
            _log("Kein Frame von Kamera, Signal trotzdem senden", "warnung")
            return True

        erkannt_id, konfidenz, _ = nutzer_erkennen(frame, [nutzer_id], schwellenwert=90)

        if erkannt_id == nutzer_id:
            _log(f"Anwesenheit bestaetigt: {nutzer_id} ({konfidenz}%)", "anwesenheit")
            return True
        else:
            _log(f"Falsche Person oder niemand erkannt — warte auf richtigen Nutzer", "warnung")
            return False

    except Exception as e:
        _log(f"Anwesenheitsfehler: {e} — Signal trotzdem senden", "warnung")
        return True


def _alle_erinnerungen_pruefen():
    if not os.path.exists(TASKS_DIR):
        return
    for datei in os.listdir(TASKS_DIR):
        if not datei.endswith("_erinnerungen.json"):
            continue
        pfad = os.path.join(TASKS_DIR, datei)
        try:
            with open(pfad, "r", encoding="utf-8") as f:
                daten = json.load(f)
        except Exception:
            continue
        nutzer_id = daten.get("nutzer_id")
        geaendert = False
        for erinnerung in daten.get("erinnerungen", []):
            if erinnerung.get("gesendet"):
                continue
            if not _ist_jetzt(erinnerung["zeit"]):
                continue
            titel = erinnerung["titel"]
            prioritaet = erinnerung["prioritaet"]
            erinnerungs_zeit = erinnerung["zeit"]
            _log(f"Erinnerung faellig: '{titel}' ({prioritaet})")

            anwesend = _anwesenheit_pruefen(nutzer_id)

            if anwesend:
                # Person da → Arduino + Audio
                _arduino_signal_senden(titel, prioritaet)
                audio_alarm_speichern(titel, prioritaet, erinnerungs_zeit)
                _log(f"Signal gesendet: '{titel}'", "signal")
            else:
                # Person nicht da → Email senden
                _email_alarm_senden(nutzer_id, titel, prioritaet, erinnerungs_zeit)

            erinnerung["gesendet"] = True
            erinnerung["gesendet_am"] = str(datetime.now())
            erinnerung["per_email"] = not anwesend
            geaendert = True
        if geaendert:
            with open(pfad, "w", encoding="utf-8") as f:
                json.dump(daten, f, ensure_ascii=False, indent=2)


def scheduler_loop():
    _log("Scheduler gestartet", "system")
    print("[Scheduler] Hintergrund-Scheduler aktiv (alle 30 Sek.)")
    while _scheduler_aktiv.is_set():
        try:
            _alle_erinnerungen_pruefen()
        except Exception as e:
            _log(f"Scheduler-Fehler: {e}", "fehler")
        time.sleep(CHECK_INTERVAL)
    _log("Scheduler gestoppt", "system")


def scheduler_starten():
    thread = threading.Thread(target=scheduler_loop, daemon=True, name="StudyBot-Scheduler")
    thread.start()
    return thread


def scheduler_stoppen():
    _scheduler_aktiv.clear()


def _zeitpunkte_berechnen(faellig_datum, prioritaet, optimale_stunde, faellig_minute=0, faellig_stunde=23):
    """
    Berechnet alle Erinnerungszeitpunkte.

    ABSOLUT VERBOTEN:
    - Kein Zeitpunkt in der Vergangenheit
    - Kein Zeitpunkt nach der Deadline

    DEADLINE HEUTE (intelligente Kurzerinnerungen in Minuten):
    - Mehr als 2h:    1h vor, 30min vor, 15min vor
    - 1h bis 2h:     30min vor, 15min vor, 5min vor
    - 30min bis 1h:  15min vor, 5min vor, 3min vor
    - 10min bis 30min: 5min vor, 3min vor
    - 3min bis 10min: 3min vor
    - Weniger als 3min oder vorbei: keine Erinnerungen

    DEADLINE IN DER ZUKUNFT:
    - Ab J-5: morgens (9h) UND abends (optimale NN-Zeit)
    - Davor: je nach Prioritaet
    """
    from datetime import date as date_type

    jetzt = datetime.now()
    heute = date_type.today()
    tage_gesamt = (faellig_datum - heute).days

    deadline_dt = datetime(
        faellig_datum.year, faellig_datum.month, faellig_datum.day,
        faellig_stunde, faellig_minute, 0
    )

    # Deadline bereits vorbei
    if deadline_dt <= jetzt:
        return []

    zeitpunkte = []

    def add(dt):
        """Nur hinzufuegen wenn Zukunft UND vor Deadline."""
        dt = dt.replace(second=0, microsecond=0)
        if jetzt < dt < deadline_dt:
            zeitpunkte.append(dt)

    # FALL 1: Deadline heute
    if tage_gesamt == 0:
        minuten = (deadline_dt - jetzt).total_seconds() / 60
        if minuten > 120:
            add(deadline_dt - timedelta(hours=1))
            add(deadline_dt - timedelta(minutes=30))
            add(deadline_dt - timedelta(minutes=15))
        elif minuten > 60:
            add(deadline_dt - timedelta(minutes=30))
            add(deadline_dt - timedelta(minutes=15))
            add(deadline_dt - timedelta(minutes=5))
        elif minuten > 30:
            add(deadline_dt - timedelta(minutes=15))
            add(deadline_dt - timedelta(minutes=5))
            add(deadline_dt - timedelta(minutes=3))
        elif minuten > 10:
            add(deadline_dt - timedelta(minutes=5))
            add(deadline_dt - timedelta(minutes=3))
        elif minuten > 3:
            add(deadline_dt - timedelta(minutes=3))
        return sorted(set(zeitpunkte))

    # FALL 2: Deadline in der Zukunft
    MORGEN = 9
    ABEND = optimale_stunde

    def add_tag(tage_vor, stunde):
        datum = faellig_datum - timedelta(days=tage_vor)
        dt = datetime(datum.year, datum.month, datum.day, stunde, 0, 0)
        add(dt)

    # Ab J-5: taeglich morgens + abends
    for tag in range(0, min(6, tage_gesamt + 1)):
        add_tag(tag, MORGEN)
        add_tag(tag, ABEND)

    # Davor: je nach Prioritaet
    if tage_gesamt > 5:
        if prioritaet == "kritisch":
            for tag in range(6, min(11, tage_gesamt + 1)):
                add_tag(tag, MORGEN)
            tag = max(tage_gesamt, 10)
            while tag > 10:
                add_tag(tag, MORGEN)
                tag -= 2
        elif prioritaet == "hoch":
            for tag in range(6, min(8, tage_gesamt + 1)):
                add_tag(tag, MORGEN)
            tag = max(tage_gesamt, 7)
            while tag > 7:
                add_tag(tag, MORGEN)
                tag -= 2
        elif prioritaet == "mittel":
            tag = tage_gesamt
            while tag > 5:
                add_tag(tag, MORGEN)
                tag -= 2
        else:
            if tage_gesamt > 6:
                add_tag(tage_gesamt, MORGEN)

    return sorted(set(zeitpunkte))


def erinnerungen_planen(nutzer_id, aufgabe_titel, faellig_datum,
                         prioritaet, optimale_stunde, faellig_stunde=23,
                         faellig_minute=0):
    """Plant alle Erinnerungen. Gibt leere Liste zurueck wenn Deadline vorbei."""
    zeitpunkte = _zeitpunkte_berechnen(
        faellig_datum, prioritaet, optimale_stunde, faellig_minute, faellig_stunde
    )

    erinnerungen = []
    gesehene = set()

    for dt in zeitpunkte:
        zeit_str = str(dt.replace(second=0, microsecond=0))
        if zeit_str in gesehene:
            continue
        gesehene.add(zeit_str)
        erinnerungen.append({
            "titel": aufgabe_titel,
            "prioritaet": prioritaet,
            "zeit": zeit_str,
            "gesendet": False,
            "gesendet_am": None
        })

    os.makedirs(TASKS_DIR, exist_ok=True)
    pfad = os.path.join(TASKS_DIR, f"{nutzer_id}_erinnerungen.json")
    bestehende = {"nutzer_id": nutzer_id, "erinnerungen": []}
    if os.path.exists(pfad):
        try:
            with open(pfad, "r", encoding="utf-8") as f:
                bestehende = json.load(f)
        except Exception:
            pass

    bestehende["erinnerungen"].extend(erinnerungen)
    with open(pfad, "w", encoding="utf-8") as f:
        json.dump(bestehende, f, ensure_ascii=False, indent=2)

    _log(f"Geplant: '{aufgabe_titel}' ({prioritaet}) -> {len(erinnerungen)} Erinnerungen", "planung")
    return erinnerungen


def log_lesen(max_eintraege=20):
    if not os.path.exists(LOG_FILE):
        return []
    try:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            log = json.load(f)
        return list(reversed(log[-max_eintraege:]))
    except Exception:
        return []


def _email_alarm_senden(nutzer_id, titel, prioritaet, erinnerungs_zeit):
    """
    Sendet einen Email-Alarm wenn der Nutzer nicht vor der Kamera ist.
    Lädt das Profil um die Email-Adresse zu holen.
    """
    try:
        import sys
        sys.path.insert(0, os.path.join(BASE_DIR, "python"))
        from audio_service import nachricht_generieren
        from email_service import _email_senden

        # Profil laden für Email-Adresse
        email_adresse = None
        for datei in os.listdir(PROFILE_DIR):
            if not datei.endswith(".json"):
                continue
            try:
                with open(os.path.join(PROFILE_DIR, datei), encoding="utf-8") as f:
                    p = json.load(f)
                if p.get("nutzer_id", "").startswith(nutzer_id.rsplit("_", 1)[0]) or \
                   nutzer_id.startswith(p.get("nutzer_id", "").rsplit("_", 1)[0]):
                    email_adresse = p.get("email")
                    vorname = p.get("vorname", "")
                    break
            except Exception:
                continue

        if not email_adresse:
            _log(f"Keine Email-Adresse für {nutzer_id} gefunden", "fehler")
            return

        nachricht = nachricht_generieren(titel, prioritaet, erinnerungs_zeit)

        prio_emoji = {"kritisch": "🔴", "hoch": "🟠", "mittel": "🟢", "niedrig": "🔵"}
        emoji = prio_emoji.get(prioritaet, "🔔")

        inhalt = f"""
        <div style="font-family:Arial,sans-serif;max-width:500px;margin:auto;
                    background:white;border-radius:16px;padding:28px;
                    box-shadow:0 4px 20px rgba(0,0,0,0.08);">
            <h2 style="color:#2E3A5C;margin-top:0;">{emoji} StudyBot Erinnerung</h2>
            <p style="color:#4A5A80;font-size:16px;line-height:1.6;">
                Hallo {vorname}!<br><br>
                Du warst nicht vor der Kamera, aber dein Erinnerungszeitpunkt ist erreicht:
            </p>
            <div style="background:#F5F7FF;border-radius:12px;padding:20px;
                        border-left:4px solid #667eea;margin:20px 0;">
                <p style="font-size:18px;font-weight:700;color:#2E3A5C;margin:0;">
                    {titel}
                </p>
                <p style="color:#9AA5BD;font-size:13px;margin:6px 0 0;">
                    Priorität: {prioritaet.upper()}
                </p>
            </div>
            <p style="color:#4A5A80;font-size:14px;">{nachricht}</p>
            <p style="color:#9AA5BD;font-size:12px;margin-top:20px;">
                Bitte bestätige diese Erinnerung wenn du sie gesehen hast.
            </p>
            <div style="text-align:center;margin:24px 0;">
                <a href="http://192.168.0.64:8501"
                   style="background:linear-gradient(135deg,#667eea,#764ba2);
                          color:white;padding:14px 32px;border-radius:12px;
                          text-decoration:none;font-weight:700;font-size:15px;
                          display:inline-block;">
                    ✓ Erinnerung bestätigen in StudyBot
                </a>
            </div>
            <p style="color:#9AA5BD;font-size:11px;text-align:center;">
                Klicke den Button um StudyBot zu öffnen und die Erinnerung zu bestätigen.
            </p>
        </div>
        """

        betreff = f"{emoji} StudyBot: Erinnerung an '{titel}'"
        ok = _email_senden(email_adresse, betreff, inhalt)
        if ok:
            _log(f"Email-Alarm gesendet an {email_adresse}: '{titel}'", "email")
        else:
            _log(f"Email-Versand fehlgeschlagen für '{titel}'", "fehler")

    except Exception as e:
        _log(f"Email-Alarm Fehler: {e}", "fehler")


def audio_alarm_speichern(titel, prioritaet, erinnerungs_zeit, deadline_zeit=None):
    """
    Speichert einen Audio-Alarm in einer JSON-Datei.
    Streamlit liest diese Datei und spielt den Alarm im Browser ab.
    """
    alarm_datei = os.path.join(BASE_DIR, "daten", "audio_alarm.json")
    alarm = {
        "titel": titel,
        "prioritaet": prioritaet,
        "erinnerungs_zeit": str(erinnerungs_zeit),
        "deadline_zeit": str(deadline_zeit) if deadline_zeit else None,
        "abgespielt": False,
        "erstellt_am": str(datetime.now())
    }
    os.makedirs(os.path.dirname(alarm_datei), exist_ok=True)
    with open(alarm_datei, "w", encoding="utf-8") as f:
        json.dump(alarm, f, ensure_ascii=False, indent=2)
    _log(f"Audio-Alarm gespeichert: '{titel}'", "audio")
