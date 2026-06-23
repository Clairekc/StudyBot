# ============================================================
#  StudyBot — seiten/login.py
#  Login: Gesichtserkennung + Passwort-Bestätigung
#
#  SICHERHEIT: Visage identifiziert die Person, Passwort
#  bestätigt die Identität. Doppelte Sicherheit.
# ============================================================

import streamlit as st
import sys, os, cv2, json, hashlib
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(BASE_DIR, "python"))

from face_recognition_module import nutzer_erkennen, alle_registrierten_nutzer

PROFILE_DIR = os.path.join(BASE_DIR, "daten", "profile")


def begruessung_nach_uhrzeit():
    stunde = datetime.now().hour
    if 5 <= stunde < 12:    return "Guten Morgen"
    elif 12 <= stunde < 18: return "Guten Tag"
    elif 18 <= stunde < 22: return "Guten Abend"
    else:                   return "Hallo, schon spät unterwegs"


def profil_laden(nutzer_id):
    # Suche mit und ohne Timestamp
    kandidaten = [nutzer_id]
    teile = nutzer_id.split("_")
    if len(teile) >= 3 and len(teile[-1]) == 6 and teile[-1].isdigit():
        kandidaten.append("_".join(teile[:-1]))
    for nid in kandidaten:
        pfad = os.path.join(PROFILE_DIR, f"{nid}.json")
        if os.path.exists(pfad):
            with open(pfad, "r", encoding="utf-8") as f:
                return json.load(f)
    return None


def passwort_pruefen(profil, passwort_eingabe):
    """Vergleicht das eingegebene Passwort mit dem gespeicherten Hash."""
    gespeicherter_hash = profil.get("passwort_hash", "")
    if not gespeicherter_hash:
        return True  # Altes Profil ohne Passwort → akzeptieren
    eingabe_hash = hashlib.sha256(passwort_eingabe.encode("utf-8")).hexdigest()
    return eingabe_hash == gespeicherter_hash


def _snapshot_aufnehmen():
    kamera = cv2.VideoCapture(0)
    if not kamera.isOpened():
        return None
    frame = None
    for _ in range(5):
        ok, frame = kamera.read()
    kamera.release()
    return frame if ok else None


def zeige():
    st.markdown("""
    <div class="sb-card">
        <h4 style="color:#2E3A5C; margin-top:0;">Anmeldung</h4>
        <p style="color:#6B7A99; font-size:14px;">
            Schritt 1: Gesichtserkennung — Schritt 2: Passwort eingeben
        </p>
    </div>
    """, unsafe_allow_html=True)

    bekannte_nutzer = alle_registrierten_nutzer()
    if not bekannte_nutzer:
        st.warning("Noch keine Nutzer registriert.")
        if st.button("Zum Onboarding"):
            st.session_state.seite = "onboarding_daten"
            st.rerun()
        return

    # ── Schritt 1: Gesichtserkennung ──────────────────────────
    if "erkannter_nutzer" not in st.session_state:
        with st.expander("⚙️ Toleranz anpassen"):
            schwellenwert = st.slider("Erkennungs-Toleranz", 50, 130, 90, 5)

        if st.button("📷 Foto aufnehmen", type="primary", use_container_width=True):
            with st.spinner("Kamera öffnen..."):
                frame = _snapshot_aufnehmen()

            if frame is None:
                st.error("❌ Kamera nicht erreichbar.")
            else:
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                st.image(rgb, width=400)

                with st.spinner("Erkenne Gesicht..."):
                    nutzer_id, konfidenz, debug_info = nutzer_erkennen(
                        frame, bekannte_nutzer, schwellenwert=90
                    )

                if nutzer_id:
                    profil = profil_laden(nutzer_id)
                    if profil:
                        st.session_state.erkannter_nutzer = nutzer_id
                        st.session_state.erkanntes_profil = profil
                        st.session_state.erkannt_konfidenz = konfidenz
                        st.rerun()
                else:
                    st.error("❌ Gesicht nicht erkannt.")
                    with st.expander("🔍 Debug-Info"):
                        st.json(debug_info.get("alle_distanzen", {}))

    # ── Schritt 2: Passwort (Name wird NICHT angezeigt) ──────
    else:
        profil    = st.session_state.erkanntes_profil
        konfidenz = st.session_state.erkannt_konfidenz

        # Kein Name anzeigen — nur Passwort verlangen
        st.markdown("""
        <div class="sb-card" style="background:linear-gradient(135deg,#EEF4FF,#F3E8FF);
                                     text-align:center; padding:24px;">
            <p style="font-size:28px; margin:0;">🔒</p>
            <p style="color:#2E3A5C; font-weight:600; font-size:16px; margin:8px 0;">
                Gesicht erkannt!
            </p>
            <p style="color:#6B7A99; font-size:14px; margin:0;">
                Bitte gib dein Passwort ein.
            </p>
        </div>
        """, unsafe_allow_html=True)

        passwort = st.text_input("Passwort", type="password", key="login_passwort")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("✓ Anmelden", type="primary", use_container_width=True):
                if passwort_pruefen(profil, passwort):
                    st.session_state.aktueller_nutzer = st.session_state.erkannter_nutzer
                    st.session_state.profil = profil
                    for key in ["erkannter_nutzer", "erkanntes_profil", "erkannt_konfidenz"]:
                        st.session_state.pop(key, None)
                    st.session_state.seite = "dashboard"
                    st.rerun()
                else:
                    st.error("❌ Falsches Passwort. Bitte versuche es erneut.")

        with col2:
            if st.button("↩️ Anderer Nutzer", use_container_width=True):
                for key in ["erkannter_nutzer", "erkanntes_profil", "erkannt_konfidenz"]:
                    st.session_state.pop(key, None)
                st.rerun()

    st.markdown("---")
    if st.button("← Zurück zur Startseite"):
        for key in ["erkannter_nutzer", "erkanntes_profil", "erkannt_konfidenz"]:
            st.session_state.pop(key, None)
        st.session_state.seite = "start"
        st.rerun()
