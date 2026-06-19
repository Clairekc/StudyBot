# ============================================================
#  StudyBot — face_recognition.py
#  Gesichtserkennung mit OpenCV (LBPH-Algorithmus)
#
#  FUNKTIONEN:
#    - Onboarding: 6 Fotos aus verschiedenen Winkeln aufnehmen
#    - Login: einzelnes Foto zur Wiedererkennung
#    - Anwesenheitsprüfung: bestätigt, dass die richtige Person
#      vor der Kamera ist, bevor eine Erinnerung gesendet wird
# ============================================================

import cv2
import numpy as np
import os
import json
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FACES_DIR = os.path.join(BASE_DIR, "daten", "faces")
os.makedirs(FACES_DIR, exist_ok=True)

# Die 6 Positionen, die beim Onboarding verlangt werden
POSITIONEN = [
    {"key": "vorne",  "label": "Schau gerade nach vorne"},
    {"key": "oben",   "label": "Schau leicht nach oben"},
    {"key": "unten",  "label": "Schau leicht nach unten"},
    {"key": "links",  "label": "Drehe den Kopf leicht nach links"},
    {"key": "rechts", "label": "Drehe den Kopf leicht nach rechts"},
    {"key": "seite",  "label": "Zeige dein Profil (von der Seite)"},
]

_face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)


def gesicht_im_frame_finden(frame):
    """Sucht ein Gesicht im Kamerabild. Gibt (x,y,w,h) zurück oder None."""
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gesichter = _face_cascade.detectMultiScale(
        gray, scaleFactor=1.1, minNeighbors=5, minSize=(100, 100)
    )
    if len(gesichter) == 0:
        return None
    # Größtes erkanntes Gesicht zurückgeben
    return max(gesichter, key=lambda g: g[2] * g[3])


def foto_aufnehmen(frame, gesicht_box):
    """Schneidet das Gesicht aus dem Frame aus und gibt Graustufenbild zurück."""
    x, y, w, h = gesicht_box
    ausschnitt = frame[y:y + h, x:x + w]
    grau = cv2.cvtColor(ausschnitt, cv2.COLOR_BGR2GRAY)
    return cv2.resize(grau, (200, 200))


def nutzer_registrieren(nutzer_id, fotos_liste):
    """
    Trainiert ein LBPH-Modell aus den 6 Onboarding-Fotos und
    speichert es für den Nutzer.

    fotos_liste: Liste von 6 Graustufenbildern (von foto_aufnehmen)
    """
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    labels = np.array([0] * len(fotos_liste))  # Ein Label pro Nutzer
    recognizer.train(fotos_liste, labels)

    modell_pfad = os.path.join(FACES_DIR, f"{nutzer_id}.yml")
    recognizer.write(modell_pfad)

    meta_pfad = os.path.join(FACES_DIR, f"{nutzer_id}_meta.json")
    with open(meta_pfad, "w", encoding="utf-8") as f:
        json.dump({
            "nutzer_id": nutzer_id,
            "registriert_am": str(datetime.now()),
            "anzahl_fotos": len(fotos_liste)
        }, f, ensure_ascii=False, indent=2)

    return modell_pfad


def nutzer_erkennen(frame, bekannte_nutzer_ids, schwellenwert=70):
    """
    Vergleicht das aktuelle Kamerabild mit allen bekannten Nutzern.
    Gibt (nutzer_id, konfidenz) zurück, oder (None, 0) falls niemand erkannt wird.

    schwellenwert: LBPH-Distanz — niedriger = strenger.
    """
    gesicht_box = gesicht_im_frame_finden(frame)
    if gesicht_box is None:
        return None, 0.0

    foto = foto_aufnehmen(frame, gesicht_box)

    bester_nutzer = None
    beste_distanz = float("inf")

    for nutzer_id in bekannte_nutzer_ids:
        modell_pfad = os.path.join(FACES_DIR, f"{nutzer_id}.yml")
        if not os.path.exists(modell_pfad):
            continue

        recognizer = cv2.face.LBPHFaceRecognizer_create()
        recognizer.read(modell_pfad)

        try:
            label, distanz = recognizer.predict(foto)
            if distanz < beste_distanz:
                beste_distanz = distanz
                bester_nutzer = nutzer_id
        except cv2.error:
            continue

    if bester_nutzer is not None and beste_distanz < schwellenwert:
        konfidenz = max(0, 100 - beste_distanz)  # niedrige Distanz = hohe Konfidenz
        return bester_nutzer, round(konfidenz, 1)

    return None, 0.0


def alle_registrierten_nutzer():
    """Gibt die Liste aller registrierten Nutzer-IDs zurück."""
    if not os.path.exists(FACES_DIR):
        return []
    return [
        f.replace(".yml", "")
        for f in os.listdir(FACES_DIR)
        if f.endswith(".yml")
    ]
