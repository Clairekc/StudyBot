# 🤖 StudyBot

StudyBot ist ein intelligenter Lern- und Aufgabenassistent für Studierende, der Machine Learning nutzt, um Aufgaben zu verwalten und automatisch zu erinnern.

---

## Zwei Varianten

StudyBot kann auf zwei Arten genutzt werden:

### Variante 1 — Lokal (vollständig)

Die App läuft auf deinem PC. Alle Funktionen sind verfügbar:

- Gesichtserkennung mit Webcam
- Echte ML-Analyse mit R (k-Means, Naive Bayes, Neural Network)
- Automatische Erinnerungen im Hintergrund
- Arduino-Signal (LED + Buzzer) bei Anwesenheit
- E-Mail-Alarm bei Abwesenheit
- Sprachausgabe (Edge TTS)

**Starten:** Doppelklick auf `dist/StudyBot_Starten.exe`

### Variante 2 — Cloud (Demo)

Die App läuft online — kein Download nötig. Nur zur Vorschau der Benutzeroberfläche geeignet.

- Anmeldung per Name + Passwort (keine Webcam)
- ML-Analyse funktioniert (regelbasiert, ohne R)
- Keine Erinnerungen, kein Arduino, keine E-Mails

**Demo-Link:** https://clairekc-studybot-streamlit-app-py-ybpofb.streamlit.app

---

## Lokal starten

**Ohne Python-Kenntnisse:**
1. Doppelklick auf `dist/StudyBot_Starten.exe`
2. Der Browser öffnet sich automatisch auf `http://localhost:8501`

**Mit Terminal:**
```bash
cd C:\Users\Admin\Downloads\StudyBot_Final_Part1
streamlit run streamlit/app.py
```

---

## Machine Learning

| Methode | Aufgabe | Ergebnis |
|---|---|---|
| **k-Means** | Aufgaben gruppieren | 4 Cluster (Dringend Kurz, Dringend Lang, Geplant Schwer, Leicht Locker) |
| **Naive Bayes** | Priorität berechnen | kritisch / hoch / mittel / niedrig (83.3% Genauigkeit) |
| **Neural Network** | Beste Lernzeit finden | R² = 0.954 |

---

## Datenspeicherung

Alle Daten werden lokal als JSON-Dateien gespeichert — keine externe Datenbank:

- `daten/profile/` → Nutzerprofile
- `daten/tasks/` → Aufgaben und Erinnerungen
- `daten/faces/` → Gesichtsmodelle (LBPH)
- `daten/scheduler_log.json` → Protokoll

---

## Hardware (optional)

**Arduino ELEGOO UNO R3:**
- Pin 9 → LED Rot (kritisch)
- Pin 10 → LED Gelb (hoch)
- Pin 11 → LED Grün (mittel)
- Pin 8 → Buzzer
- Pin 2 → Bestätigungs-Button

---

## Externe Tools

| Tool | Link |
|---|---|
| Python | https://www.python.org |
| R | https://www.r-project.org |
| Streamlit | https://streamlit.io |
| GitLab RLP (Quellcode) | https://gitlab.rlp.net/mnch3146910289/studybot |
| GitHub (Cloud-Demo) | https://github.com/Clairekc/StudyBot |
| Tinkercad (Arduino-Simulation) | https://www.tinkercad.com/things/ankOzd2hPTK/editel |
| OnShape (3D-Gehäuse) | https://www.onshape.com |
| PTC Creo (3D-Modellierung) | https://www.ptc.com/creo |
| Arduino | https://www.arduino.cc |
| OpenCV (Gesichtserkennung) | https://opencv.org |
| Edge TTS (Sprachausgabe) | https://github.com/rany2/edge-tts |

---

## Studentin

**Mendeleive Claire Chiabou Kandjieu** — mnch@hochschule-trier.de  
Hochschule Trier — Machine Learning von Prof. Dr. Martin Vogt
