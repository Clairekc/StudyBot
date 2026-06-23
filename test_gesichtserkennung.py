# ============================================================
#  StudyBot — test_gesichtserkennung.py
#  Einfacher Test: Nimmt 6 Fotos auf, trainiert, erkennt wieder
#
#  AUFRUF:  python test_gesichtserkennung.py
#  Bedienung: Leertaste = Foto aufnehmen, ESC = Abbrechen
# ============================================================

import cv2
import sys
import os

# python/-Ordner zum Pfad hinzufügen, damit wir das Modul importieren können
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "python"))

from face_recognition_module import (
    gesicht_im_frame_finden,
    foto_aufnehmen,
    nutzer_registrieren,
    nutzer_erkennen,
    POSITIONEN
)

NUTZER_ID = "test_nutzer_001"


def onboarding_test():
    print("=" * 50)
    print("  STUDYBOT — Test Gesichtserkennung (Onboarding)")
    print("=" * 50)
    print()
    print("Es werden 6 Fotos aus verschiedenen Winkeln aufgenommen.")
    print("Drücke LEERTASTE, wenn dein Gesicht im grünen Rahmen ist.")
    print("Drücke ESC zum Abbrechen.")
    print()

    kamera = cv2.VideoCapture(0)
    if not kamera.isOpened():
        print("FEHLER: Kamera konnte nicht geöffnet werden.")
        return False

    fotos_aufgenommen = []

    for position in POSITIONEN:
        print(f"\n>>> Position: {position['label']}")
        foto_gemacht = False

        while not foto_gemacht:
            ret, frame = kamera.read()
            if not ret:
                break

            anzeige = frame.copy()
            gesicht_box = gesicht_im_frame_finden(frame)

            if gesicht_box is not None:
                x, y, w, h = gesicht_box
                # Grüner Rahmen wenn Gesicht erkannt
                cv2.rectangle(anzeige, (x, y), (x + w, y + h), (0, 255, 0), 2)
                status_text = "Gesicht erkannt - LEERTASTE druecken"
                farbe = (0, 255, 0)
            else:
                status_text = "Kein Gesicht erkannt..."
                farbe = (0, 0, 255)

            cv2.putText(anzeige, position['label'], (20, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
            cv2.putText(anzeige, status_text, (20, 80),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, farbe, 2)
            cv2.putText(anzeige, f"Foto {len(fotos_aufgenommen) + 1}/6", (20, 460),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

            cv2.imshow("StudyBot - Onboarding Test", anzeige)
            taste = cv2.waitKey(1) & 0xFF

            if taste == 27:  # ESC
                kamera.release()
                cv2.destroyAllWindows()
                print("\nAbgebrochen.")
                return False

            if taste == 32 and gesicht_box is not None:  # LEERTASTE
                foto = foto_aufnehmen(frame, gesicht_box)
                fotos_aufgenommen.append(foto)
                foto_gemacht = True
                print(f"  ✓ Foto aufgenommen ({len(fotos_aufgenommen)}/6)")

    kamera.release()
    cv2.destroyAllWindows()

    print(f"\n{len(fotos_aufgenommen)} Fotos aufgenommen. Trainiere Modell...")
    nutzer_registrieren(NUTZER_ID, fotos_aufgenommen)
    print(f"✓ Nutzer '{NUTZER_ID}' erfolgreich registriert!")
    return True


def erkennung_test():
    print("\n" + "=" * 50)
    print("  Jetzt: Wiedererkennung testen")
    print("=" * 50)
    print("Schau in die Kamera. Drücke ESC zum Beenden.")

    kamera = cv2.VideoCapture(0)

    while True:
        ret, frame = kamera.read()
        if not ret:
            break

        nutzer_id, konfidenz = nutzer_erkennen(frame, [NUTZER_ID])

        anzeige = frame.copy()
        if nutzer_id:
            text = f"Erkannt: {nutzer_id} ({konfidenz}%)"
            farbe = (0, 255, 0)
        else:
            text = "Nicht erkannt"
            farbe = (0, 0, 255)

        cv2.putText(anzeige, text, (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, farbe, 2)
        cv2.imshow("StudyBot - Erkennung Test", anzeige)

        if cv2.waitKey(1) & 0xFF == 27:  # ESC
            break

    kamera.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    if onboarding_test():
        erkennung_test()
    print("\nTest abgeschlossen.")
