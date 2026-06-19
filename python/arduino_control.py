# ============================================================
#  StudyBot — arduino_control.py
#  Serielle Kommunikation mit dem ELEGOO UNO R3
#
#  PROTOKOLL: Einfache Textbefehle über Serial, getrennt durch \n
#  Beispiel: "LED:rot:5000\n"  →  rote LED für 5000ms
#            "BUZZ:hoch\n"     →  Buzzer-Pattern für hohe Priorität
#            "WAIT_BUTTON\n"   →  wartet auf Knopfdruck (Bestätigung)
# ============================================================

import serial
import serial.tools.list_ports
import time
import json
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_PFAD = os.path.join(BASE_DIR, "daten", "models", "arduino_log.json")

ARDUINO_BAUD = 9600
ARDUINO_TIMEOUT = 2


def arduino_port_finden():
    """Sucht automatisch nach einem angeschlossenen Arduino."""
    ports = serial.tools.list_ports.comports()
    for port in ports:
        if "Arduino" in port.description or "CH340" in port.description or "USB" in port.description:
            return port.device
    return None


def arduino_verbinden(port=None):
    """
    Stellt eine serielle Verbindung zum Arduino her.
    Gibt None zurück (Demo-Modus) falls kein Arduino gefunden wird —
    das Programm funktioniert dann trotzdem, gibt nur Konsolen-Meldungen aus.
    """
    if port is None:
        port = arduino_port_finden()

    if port is None:
        print("[Arduino] Kein Arduino gefunden → Demo-Modus aktiv.")
        return None

    try:
        verbindung = serial.Serial(port, ARDUINO_BAUD, timeout=ARDUINO_TIMEOUT)
        time.sleep(2)  # Arduino startet nach Verbindung neu
        print(f"[Arduino] ✓ Verbunden auf {port}")
        return verbindung
    except serial.SerialException as e:
        print(f"[Arduino] Verbindungsfehler: {e} → Demo-Modus aktiv.")
        return None


def _senden(verbindung, befehl):
    """Sendet einen Textbefehl an den Arduino."""
    if verbindung is None:
        print(f"[Arduino DEMO] → {befehl}")
        return

    verbindung.write(f"{befehl}\n".encode("utf-8"))
    time.sleep(0.05)


def prioritaet_signal_senden(verbindung, prioritaet, aufgaben_titel=""):
    """
    Sendet das passende LED + Buzzer Signal je nach Priorität.

    kritisch → Rot,   Buzzer brutal (schnell, laut, wiederholt)
    hoch     → Gelb,  Buzzer mittel
    mittel   → Grün,  Buzzer leicht
    niedrig  → Blau,  kein Buzzer
    """
    konfiguration = {
        "kritisch": {"farbe": "rot",  "buzzer": "brutal"},
        "hoch":     {"farbe": "gelb", "buzzer": "mittel"},
        "mittel":   {"farbe": "gruen","buzzer": "leicht"},
        "niedrig":  {"farbe": "blau", "buzzer": "aus"},
    }

    config = konfiguration.get(prioritaet, konfiguration["mittel"])

    _senden(verbindung, f"LED:{config['farbe']}")
    if config["buzzer"] != "aus":
        _senden(verbindung, f"BUZZ:{config['buzzer']}")

    print(f"[Arduino] Signal gesendet: {prioritaet} → LED {config['farbe']}, "
          f"Buzzer {config['buzzer']} ({aufgaben_titel})")


def auf_bestaetigung_warten(verbindung, max_wartezeit_sek=30):
    """
    Wartet, bis der Nutzer den physischen Knopf drückt.
    Gibt True zurück bei Bestätigung, False bei Timeout.

    Im Demo-Modus (kein Arduino) wird automatisch nach 2 Sek. bestätigt.
    """
    if verbindung is None:
        print("[Arduino DEMO] Simuliere Knopfdruck nach 2 Sekunden...")
        time.sleep(2)
        return True

    _senden(verbindung, "WAIT_BUTTON")
    start = time.time()

    while time.time() - start < max_wartezeit_sek:
        if verbindung.in_waiting > 0:
            antwort = verbindung.readline().decode("utf-8").strip()
            if antwort == "BUTTON_PRESSED":
                print("[Arduino] ✓ Bestätigung erhalten.")
                return True
        time.sleep(0.1)

    print("[Arduino] ✗ Keine Bestätigung (Timeout).")
    return False


def signal_stoppen(verbindung):
    """Schaltet LED und Buzzer aus (nach Bestätigung)."""
    _senden(verbindung, "STOP")


def ereignis_protokollieren(aufgabe_titel, prioritaet, bestaetigt, dauer_sek):
    """
    Speichert das Ergebnis eines Erinnerungs-Zyklus als Trainingsdaten
    für zukünftige ML-Verbesserungen (z.B. Reaktionszeit-Analyse).
    """
    eintrag = {
        "zeitstempel": str(datetime.now()),
        "aufgabe": aufgabe_titel,
        "prioritaet": prioritaet,
        "bestaetigt": bestaetigt,
        "reaktionszeit_sek": dauer_sek
    }

    log = []
    if os.path.exists(LOG_PFAD):
        with open(LOG_PFAD, "r", encoding="utf-8") as f:
            log = json.load(f)

    log.append(eintrag)

    os.makedirs(os.path.dirname(LOG_PFAD), exist_ok=True)
    with open(LOG_PFAD, "w", encoding="utf-8") as f:
        json.dump(log, f, ensure_ascii=False, indent=2)

    print(f"[Log] Ereignis gespeichert: {aufgabe_titel} ({'bestätigt' if bestaetigt else 'Timeout'})")


def vollstaendiger_erinnerungs_zyklus(verbindung, aufgabe_titel, prioritaet):
    """
    Führt den kompletten Ablauf aus: Signal senden → auf Bestätigung
    warten → Signal stoppen → Ereignis protokollieren.
    """
    start = time.time()
    prioritaet_signal_senden(verbindung, prioritaet, aufgabe_titel)
    bestaetigt = auf_bestaetigung_warten(verbindung)
    signal_stoppen(verbindung)
    dauer = round(time.time() - start, 1)
    ereignis_protokollieren(aufgabe_titel, prioritaet, bestaetigt, dauer)
    return bestaetigt
