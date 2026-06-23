/* ============================================================
 *  StudyBot — studybot.ino
 *  Arduino-Sketch für ELEGOO UNO R3
 *
 *  PINBELEGUNG:
 *    Pin 9  → LED Rot     (kritisch)
 *    Pin 10 → LED Gelb    (hoch)
 *    Pin 11 → LED Gruen   (mittel)
 *    Pin 6  → LED Blau    (niedrig)
 *    Pin 8  → Active Buzzer
 *    Pin 2  → Bestaetigungs-Knopf (INPUT_PULLUP)
 *
 *  PROTOKOLL (über Serial, 9600 Baud):
 *    "LED:rot"        → schaltet rote LED ein (andere aus)
 *    "LED:gelb"       → schaltet gelbe LED ein
 *    "LED:gruen"      → schaltet gruene LED ein
 *    "LED:blau"       → schaltet blaue LED ein
 *    "BUZZ:brutal"    → schnelles, lautes Piepsen (kritisch)
 *    "BUZZ:mittel"    → moderates Piepsen (hoch)
 *    "BUZZ:leicht"    → sanftes, langsames Piepsen (mittel)
 *    "WAIT_BUTTON"    → wartet auf Knopfdruck, sendet "BUTTON_PRESSED"
 *    "STOP"           → schaltet alles aus
 * ============================================================ */

const int LED_ROT   = 9;
const int LED_GELB  = 10;
const int LED_GRUEN = 11;
const int LED_BLAU  = 6;
const int BUZZER    = 8;
const int BUTTON     = 2;

void setup() {
  Serial.begin(9600);

  pinMode(LED_ROT,   OUTPUT);
  pinMode(LED_GELB,  OUTPUT);
  pinMode(LED_GRUEN, OUTPUT);
  pinMode(LED_BLAU,  OUTPUT);
  pinMode(BUZZER,    OUTPUT);
  pinMode(BUTTON,    INPUT_PULLUP);

  alle_aus();
  Serial.println("StudyBot Arduino bereit.");
}

void loop() {
  if (Serial.available() > 0) {
    String befehl = Serial.readStringUntil('\n');
    befehl.trim();
    verarbeite_befehl(befehl);
  }
}

void verarbeite_befehl(String befehl) {
  if (befehl.startsWith("LED:")) {
    String farbe = befehl.substring(4);
    led_einschalten(farbe);
  }
  else if (befehl.startsWith("BUZZ:")) {
    String intensitaet = befehl.substring(5);
    buzzer_pattern(intensitaet);
  }
  else if (befehl == "WAIT_BUTTON") {
    warte_auf_knopfdruck();
  }
  else if (befehl == "STOP") {
    alle_aus();
  }
}

void led_einschalten(String farbe) {
  alle_leds_aus();
  if      (farbe == "rot")   digitalWrite(LED_ROT,   HIGH);
  else if (farbe == "gelb")  digitalWrite(LED_GELB,  HIGH);
  else if (farbe == "gruen") digitalWrite(LED_GRUEN, HIGH);
  else if (farbe == "blau")  digitalWrite(LED_BLAU,  HIGH);
}

void alle_leds_aus() {
  digitalWrite(LED_ROT,   LOW);
  digitalWrite(LED_GELB,  LOW);
  digitalWrite(LED_GRUEN, LOW);
  digitalWrite(LED_BLAU,  LOW);
}

void buzzer_pattern(String intensitaet) {
  if (intensitaet == "brutal") {
    // Kritisch: schnell, laut, 6x wiederholt
    for (int i = 0; i < 6; i++) {
      digitalWrite(BUZZER, HIGH);
      delay(150);
      digitalWrite(BUZZER, LOW);
      delay(80);
    }
  }
  else if (intensitaet == "mittel") {
    // Hoch: moderates Tempo, 3x wiederholt
    for (int i = 0; i < 3; i++) {
      digitalWrite(BUZZER, HIGH);
      delay(250);
      digitalWrite(BUZZER, LOW);
      delay(200);
    }
  }
  else if (intensitaet == "leicht") {
    // Mittel: sanft, 1x kurz
    digitalWrite(BUZZER, HIGH);
    delay(300);
    digitalWrite(BUZZER, LOW);
  }
}

void warte_auf_knopfdruck() {
  // Wartet bis zu 30 Sekunden auf Knopfdruck
  unsigned long start = millis();
  while (millis() - start < 30000) {
    if (digitalRead(BUTTON) == LOW) {  // INPUT_PULLUP: LOW = gedrueckt
      delay(50);  // Entprellen
      if (digitalRead(BUTTON) == LOW) {
        Serial.println("BUTTON_PRESSED");
        // Warten bis Knopf losgelassen wird
        while (digitalRead(BUTTON) == LOW) { delay(10); }
        return;
      }
    }
  }
  Serial.println("BUTTON_TIMEOUT");
}

void alle_aus() {
  alle_leds_aus();
  digitalWrite(BUZZER, LOW);
}
