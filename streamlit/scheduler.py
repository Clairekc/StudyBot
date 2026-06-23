# ============================================================
#  StudyBot — scheduler.py
#  Hintergrund-Scheduler: läuft als Thread INNERHALB von Streamlit
#
#  KONZEPT:
#  - Der Nutzer gibt nur Titel + Fälligkeitsdatum ein
#  - Das System berechnet automatisch 3 gestaffelte Erinnerungs-
#    zeitpunkte (abhängig von der Priorität aus Naive Bayes)
#  - Ein Hintergrund-Thread prüft alle 30 Sekunden, ob ein
#    Erinnerungszeitpunkt erreicht ist, und löst dann SELBST
#    das Arduino-Signal aus — ohne Nutzeraktion.
#
#  WICHTIG: Läuft als Python-Thread im selben Prozess wie
#  Streamlit. Wird beim ersten Laden der App einmalig gestartet
#  und läuft danach dauerhaft im Hintergrund weiter.
# ============================================================

import threading
import time
import json
import os
from datetime import datetime, timedelta

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TASKS_DIR = os.path.join(BASE_DIR, "..", "daten", "tasks")
SCHEDULE_DIR = os.path.join(BASE_DIR, "..", "daten", "schedule")
os.makedirs(SCHEDULE_DIR, exist_ok=True)

PRUEF_INTERVALL_SEK = 30  # wie oft der Scheduler nachschaut

# Anteil der verbleibenden Zeit, NACH der jeweiligen Stufe erinnert wird.
# Beispiel "kritisch": bei 0.5 → Erinnerung nach der Hälfte der Wartezeit,
# bei 0.8 → nach 80% der Wartezeit (also näher am Fälligkeitsdatum).
STAFFELUNG = {
    "kritisch": [0.5, 0.8],   # + Tag selbst = 3 Erinnerungen
    "hoch":     [0.6, 0.85],
    "mittel":   [0.7, 0.9],
    "niedrig":  [0.8, 0.95],
}


def erinnerungszeitpunkte_berechnen(erstellt_am, faellig_am, prioritaet, beste_stunde):
    """
    Berechnet 3 gestaffelte Erinnerungszeitpunkte zwischen Erstellung
    und Fälligkeit der Aufgabe — abhängig von der ML-Priorität.

    erstellt_am, faellig_am: datetime-Objekte
    prioritaet: "kritisch" | "hoch" | "mittel" | "niedrig"
    beste_stunde: int (0-23) — aus dem Neuronalen Netz, für die Uhrzeit
    """
    gesamtdauer = faellig_am - erstellt_am
    anteile = STAFFELUNG.get(prioritaet, STAFFELUNG["mittel"])

    zeitpunkte = []
    for anteil in anteile:
        zeitpunkt = erstellt_am + gesamtdauer * anteil
        # Uhrzeit auf die vom NN berechnete optimale Stunde setzen
        zeitpunkt = zeitpunkt.replace(hour=beste_stunde, minute=0, second=0, microsecond=0)
        zeitpunkte.append(zeitpunkt)

    # Letzte Erinnerung: am Fälligkeitstag selbst, zur optimalen Stunde
    tag_selbst = faellig_am.replace(hour=beste_stunde, minute=0, second=0, microsecond=0)
    zeitpunkte.append(tag_selbst)

    return sorted(zeitpunkte)


def aufgabe_zum_zeitplan_hinzufuegen(nutzer_id, aufgabe_id, titel, prioritaet,
                                       erstellt_am, faellig_am, beste_stunde):
    """Speichert die berechneten Erinnerungszeitpunkte für eine Aufgabe."""
    zeitpunkte = erinnerungszeitpunkte_berechnen(erstellt_am, faellig_am, prioritaet, beste_stunde)

    eintrag = {
        "aufgabe_id": aufgabe_id,
        "nutzer_id": nutzer_id,
        "titel": titel,
        "prioritaet": prioritaet,
        "erinnerungen": [
            {"zeitpunkt": z.isoformat(), "ausgeloest": False} for z in zeitpunkte
        ]
    }

    pfad = os.path.join(SCHEDULE_DIR, f"{nutzer_id}_schedule.json")
    alle = []
    if os.path.exists(pfad):
        with open(pfad, "r", encoding="utf-8") as f:
            alle = json.load(f)

    alle.append(eintrag)
    with open(pfad, "w", encoding="utf-8") as f:
        json.dump(alle, f, ensure_ascii=False, indent=2)

    return eintrag


def _faellige_erinnerungen_holen():
    """
    Durchsucht alle Zeitpläne aller Nutzer und gibt alle Erinnerungen
    zurück, deren Zeitpunkt erreicht (oder überschritten) ist und die
    noch nicht ausgelöst wurden.
    """
    faellig = []
    if not os.path.exists(SCHEDULE_DIR):
        return faellig

    jetzt = datetime.now()

    for dateiname in os.listdir(SCHEDULE_DIR):
        if not dateiname.endswith("_schedule.json"):
            continue
        pfad = os.path.join(SCHEDULE_DIR, dateiname)
        with open(pfad, "r", encoding="utf-8") as f:
            aufgaben = json.load(f)

        geaendert = False
        for aufgabe in aufgaben:
            for erinnerung in aufgabe["erinnerungen"]:
                if erinnerung["ausgeloest"]:
                    continue
                zeitpunkt = datetime.fromisoformat(erinnerung["zeitpunkt"])
                if zeitpunkt <= jetzt:
                    faellig.append({
                        "nutzer_id": aufgabe["nutzer_id"],
                        "titel": aufgabe["titel"],
                        "prioritaet": aufgabe["prioritaet"],
                    })
                    erinnerung["ausgeloest"] = True
                    geaendert = True

        if geaendert:
            with open(pfad, "w", encoding="utf-8") as f:
                json.dump(aufgaben, f, ensure_ascii=False, indent=2)

    return faellig


def _scheduler_schleife():
    """Läuft endlos im Hintergrund-Thread. Prüft alle 30 Sekunden."""
    import sys
    python_dir = os.path.join(BASE_DIR, "..", "python")
    sys.path.insert(0, python_dir)
    import arduino_control

    verbindung = arduino_control.arduino_verbinden()

    while True:
        try:
            faellige = _faellige_erinnerungen_holen()
            for eintrag in faellige:
                print(f"[Scheduler] ⏰ Auslösung: '{eintrag['titel']}' ({eintrag['prioritaet']})")
                arduino_control.vollstaendiger_erinnerungs_zyklus(
                    verbindung, eintrag["titel"], eintrag["prioritaet"]
                )
        except Exception as e:
            print(f"[Scheduler] Fehler: {e}")

        time.sleep(PRUEF_INTERVALL_SEK)


_scheduler_gestartet = False
_lock = threading.Lock()


def scheduler_starten_falls_noetig():
    """
    Startet den Hintergrund-Thread genau EINMAL pro Streamlit-Prozess.
    Wird beim Laden von app.py aufgerufen — dank Lock + Flag sicher
    auch bei mehreren Streamlit-Reruns.
    """
    global _scheduler_gestartet
    with _lock:
        if not _scheduler_gestartet:
            thread = threading.Thread(target=_scheduler_schleife, daemon=True)
            thread.start()
            _scheduler_gestartet = True
            print("[Scheduler] Hintergrund-Überwachung gestartet (prüft alle 30s).")
