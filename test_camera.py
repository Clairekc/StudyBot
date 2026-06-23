import cv2

print("Ouverture der Kamera...")
kamera = cv2.VideoCapture(0)

if not kamera.isOpened():
    print("FEHLER: Kamera konnte nicht geöffnet werden.")
else:
    print("Kamera erfolgreich geöffnet! Drücke 'q' zum Beenden.")
    while True:
        ret, frame = kamera.read()
        if not ret:
            break
        cv2.imshow("Test - StudyBot Kamera", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

kamera.release()
cv2.destroyAllWindows()
print("Kamera geschlossen.")