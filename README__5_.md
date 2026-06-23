# 🤖 StudyBot — KI-gestützter Lernassistent

StudyBot ist ein intelligenter Lernassistent für Schüler und Studierende, der Machine Learning nutzt, um personalisierte Aufgabenverwaltung und smarte Erinnerungen zu bieten.

---

## Projektübersicht

StudyBot kombiniert drei ML-Methoden (k-Means, Naive Bayes, Neural Network) mit Gesichtserkennung, automatischen Erinnerungen und einer benutzerfreundlichen Web-Oberfläche.

---

## Starten

**Ohne Python-Kenntnisse:**
1. Doppelklick auf `dist/StudyBot_Starten.exe`
2. Der Browser öffnet sich automatisch auf `http://localhost:8501`

**Mit Terminal:**
```bash
cd C:\Users\Admin\Downloads\StudyBot_Final_Part1
streamlit run streamlit/app.py
```

---

## Systemarchitektur

```
BENUTZER
   |
   v
EINGABE DER AUFGABEN (Streamlit Web-Interface)
   |
   v
DATENBANK DER AUFGABEN (JSON / lokal)
   |
   +------------------+------------------+
   |                  |                  |
   v                  v                  v
1. K-MEANS        2. NAIVE BAYES    3. NEURONALES NETZ
Gruppierung       Prioritäts-       Dringlichkeitswert
ähnlicher         klassifikation    berechnen
Aufgaben          Berechnung der    Perzeptron +
Clusterbildung    Wahrscheinlich-   Sigmoid Funktion
                  keiten
   |                  |                  |
   +------------------+------------------+
                      |
                      v
            4. ENTSCHEIDUNGSSYSTEM
            Kombination der Ergebnisse
            Bestimmung der Erinnerungszeit
                      |
          +-----------+-----------+
          |                       |
          v                       v
       AUSGABE                 ARDUINO (optional)
  Priorisierte Liste        LED / Buzzer / Button
  Erinnerung / Alarm        Physische Signale
  Empfehlungen              Licht / Ton Benachrichtigung
                                  |
                                  v
                             3D-DRUCK (optional)
                            Gehäuse des Geräts
```

**Ziel:** Intelligente Unterstützung für Studierende zur besseren Organisation und Zeitmanagement.

---

## Machine Learning Methoden

| Methode | Zweck | Ergebnis |
|---|---|---|
| **k-Means** | Aufgaben-Clustering | 4 Cluster (Dringend Kurz, Dringend Lang, Geplant Schwer, Leicht Locker) |
| **Naive Bayes** | Priorität-Klassifikation | kritisch / hoch / mittel / niedrig (83.3% Genauigkeit) |
| **Neural Network** | Optimale Lernzeit | R² = 0.954 |

---

## Datenspeicherung

Alle Daten werden **lokal** als JSON-Dateien gespeichert — keine Cloud, keine externe Datenbank:

- `daten/profile/` → Nutzerprofile (Name, E-Mail, Passwort-Hash)
- `daten/tasks/` → Aufgaben + ML-Ergebnisse + Erinnerungen
- `daten/faces/` → LBPH-Gesichtsmodelle pro Nutzer
- `daten/scheduler_log.json` → Protokoll aller Erinnerungen

---

## Hardware (Optional)

**Arduino ELEGOO UNO R3:**
- Pin 9 → LED Rot
- Pin 10 → LED Gelb
- Pin 11 → LED Grün
- Pin 8 → Buzzer
- Pin 2 → Button

---

## Externe Tools & Links

| Tool | Beschreibung | Link |
|---|---|---|
| **Python** | Programmiersprache (v3.11) | https://www.python.org |
| **R** | Statistik & ML-Sprache | https://www.r-project.org |
| **Streamlit** | Web-Framework für Python | https://streamlit.io |
| **GitLab RLP** | Versionskontrolle (Quellcode) | https://gitlab.rlp.net/mnch3146910289/studybot |
| **Tinkercad** | Arduino-Schaltung Simulation | https://www.tinkercad.com/things/ankOzd2hPTK/editel |
| **OnShape** | 3D-CAD Design (Gehäuse) | https://www.onshape.com |
| **PTC Creo** | 3D-Modellierung professionell | https://www.ptc.com/creo |
| **Arduino** | Mikrocontroller Plattform | https://www.arduino.cc |
| **Edge TTS** | Text-to-Speech (KatjaNeural) | https://github.com/rany2/edge-tts |
| **OpenCV** | Gesichtserkennung (LBPH) | https://opencv.org |

---

## Entwickler

- **Mendel Kandjieu** — mnch@hochschule-trier.de
- Hochschule Trier — Sommersemester 2026

---

## Lizenz

Dieses Projekt wurde im Rahmen eines Hochschulprojekts entwickelt und dient ausschließlich akademischen Zwecken.
