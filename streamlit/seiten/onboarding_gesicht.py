# ============================================================
#  StudyBot — seiten/onboarding_gesicht.py
#  Onboarding Schritt 2: Gesichtserkennung (3 Fotos)
# ============================================================

import streamlit as st
import sys, os
from PIL import Image

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(BASE_DIR, "python"))

# ── Cloud-Erkennung ──────────────────────────────────────────
def ist_cloud():
    return os.environ.get("STREAMLIT_SHARING_MODE") == "streamlit" or \
           os.path.exists("/mount/src")

CLOUD_MODUS = ist_cloud()

if not CLOUD_MODUS:
    import cv2
    from face_recognition_module import (
        gesicht_im_frame_finden, foto_aufnehmen,
        nutzer_registrieren, POSITIONEN
    )
else:
    import json, hashlib
    POSITIONEN = [
        {"key": "vorne",  "label": "Geradeaus schauen"},
        {"key": "links",  "label": "Leicht nach links"},
        {"key": "rechts", "label": "Leicht nach rechts"},
    ]
    PROFILE_DIR = os.path.join(BASE_DIR, "daten", "profile")

    def nutzer_registrieren_cloud(nutzer_id, passwort, vorname, nachname, email):
        """Registriert Nutzer ohne Gesichtsfoto (Demo-Modus)."""
        os.makedirs(PROFILE_DIR, exist_ok=True)
        profil = {
            "nutzer_id": nutzer_id,
            "vorname": vorname,
            "nachname": nachname,
            "email": email,
            "passwort_hash": hashlib.sha256(passwort.encode()).hexdigest(),
            "cloud_modus": True
        }
        with open(os.path.join(PROFILE_DIR, f"{nutzer_id}.json"), "w", encoding="utf-8") as f:
            json.dump(profil, f, ensure_ascii=False, indent=2)


def onboarding_daten_pruefen():
    if "onboarding_daten" not in st.session_state:
        st.warning("Bitte fülle zuerst Schritt 1 aus.")
        if st.button("Zu Schritt 1"):
            st.session_state.seite = "onboarding_daten"
            st.rerun()
        st.stop()


def _state_zuruecksetzen():
    st.session_state.gesicht_fotos = {}
    st.session_state.gesicht_vorschau = {}


def _snapshot():
    if CLOUD_MODUS:
        return None
    import cv2
    kamera = cv2.VideoCapture(0)
    if not kamera.isOpened():
        return None
    frame = None
    for _ in range(5):
        ok, frame = kamera.read()
    kamera.release()
    return frame if ok else None


def zeige():
    onboarding_daten_pruefen()

    from seiten.onboarding_daten import fortschritt_anzeigen
    fortschritt_anzeigen(2)

    vorname = st.session_state.onboarding_daten["vorname"]

    # ── Cloud-Modus: Kein Foto, direkt weiter ───────────────
    if CLOUD_MODUS:
        st.markdown(f"""
        <div class="sb-card">
            <h4 style="color:#2E3A5C;margin-top:0;">Schritt 2 — Gesichtserkennung</h4>
            <p style="color:#6B7A99;font-size:14px;">
                Hallo {vorname}! 
            </p>
        </div>
        """, unsafe_allow_html=True)

        st.info("""
        🌐 **Demo-Modus (Cloud)**
        
        Die Gesichtserkennung funktioniert nur lokal mit einer Webcam.  
        Im Demo-Modus wird dein Konto ohne Gesichtsfoto erstellt — 
        du kannst dich mit **Name + Passwort** anmelden.
        """)

        st.success("✓ Schritt 2 wird im Demo-Modus übersprungen.")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("← Zurück", use_container_width=True):
                st.session_state.seite = "onboarding_daten"
                st.rerun()
        with col2:
            if st.button("Weiter →", type="primary", use_container_width=True):
                # Profil direkt speichern (ohne Gesicht)
                daten = st.session_state.onboarding_daten
                nutzer_registrieren_cloud(
                    daten["nutzer_id"],
                    daten.get("passwort", ""),
                    daten["vorname"],
                    daten.get("nachname", ""),
                    daten.get("email", "")
                )
                st.session_state.seite = "onboarding_fragebogen"
                st.rerun()
        return

    # ── Lokaler Modus: echte Kamera ─────────────────────────
    st.markdown(f"""
    <div class="sb-card">
        <h4 style="color:#2E3A5C;margin-top:0;">Schritt 2 — Gesichtserkennung</h4>
        <p style="color:#6B7A99;font-size:14px;">
            Hallo {vorname}! Wir nehmen <b>3 kurze Fotos</b> auf damit StudyBot
            dich wiedererkennt.<br>
            <b>So geht es:</b> Befolge die Anweisung unten →
            klicke <b>📷 Foto aufnehmen</b> → siehst du dein Gesicht?
            Klicke <b>✓ Übernehmen</b>.
        </p>
    </div>
    """, unsafe_allow_html=True)

    if "gesicht_fotos" not in st.session_state:
        _state_zuruecksetzen()

    aktuelle_anzahl = len(st.session_state.gesicht_fotos)
    fertig = aktuelle_anzahl >= len(POSITIONEN)

    if st.button("🔄 Neu starten", use_container_width=False):
        _state_zuruecksetzen()
        st.rerun()

    if not fertig:
        position = POSITIONEN[aktuelle_anzahl]
        fortschritt = aktuelle_anzahl / len(POSITIONEN)
        st.progress(fortschritt)
        st.info(f"📸 **Foto {aktuelle_anzahl + 1} von {len(POSITIONEN)}:** {position['label']}")

        col_a, col_b = st.columns([1, 1])
        with col_a:
            aufnehmen = st.button("📷 Foto aufnehmen", type="primary",
                                   use_container_width=True,
                                   key=f"snap_{aktuelle_anzahl}")

        if aufnehmen:
            with st.spinner("Kamera..."):
                frame = _snapshot()

            if frame is None:
                st.error("Kamera nicht erreichbar.")
            else:
                import cv2
                gesicht_box = gesicht_im_frame_finden(frame)
                anzeige = frame.copy()
                if gesicht_box is not None:
                    x, y, w, h = gesicht_box
                    cv2.rectangle(anzeige, (x, y), (x+w, y+h), (0, 200, 0), 3)
                rgb = cv2.cvtColor(anzeige, cv2.COLOR_BGR2RGB)
                st.image(rgb, width=380)
                if gesicht_box is not None:
                    st.success("✓ Gesicht erkannt!")
                    st.session_state["aktuelles_frame"] = frame
                    st.session_state["gesicht_ok"] = True
                else:
                    st.warning("Kein Gesicht erkannt. Bitte neu positionieren.")
                    st.session_state["gesicht_ok"] = False

        if st.session_state.get("gesicht_ok") and "aktuelles_frame" in st.session_state:
            with col_b:
                if st.button("✓ Übernehmen", use_container_width=True,
                             key=f"ok_{aktuelle_anzahl}"):
                    import cv2
                    frame = st.session_state["aktuelles_frame"]
                    box = gesicht_im_frame_finden(frame)
                    if box is not None:
                        foto = foto_aufnehmen(frame, box)
                        vorschau = Image.fromarray(
                            cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        ).resize((90, 90))
                        st.session_state.gesicht_fotos[position["key"]] = foto
                        st.session_state.gesicht_vorschau[position["key"]] = vorschau
                        st.session_state.pop("aktuelles_frame", None)
                        st.session_state.pop("gesicht_ok", None)
                        st.rerun()
    else:
        st.success("✓ Alle 3 Fotos aufgenommen!")

    st.markdown("---")
    st.markdown("**Deine Aufnahmen:**")
    spalten = st.columns(3)
    for i, pos in enumerate(POSITIONEN):
        with spalten[i]:
            if pos["key"] in st.session_state.get("gesicht_vorschau", {}):
                st.image(st.session_state.gesicht_vorschau[pos["key"]])
                st.markdown(
                    f"<p style='text-align:center;font-size:12px;color:#3A8B3A;font-weight:600;'>✓ {pos['key']}</p>",
                    unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="width:90px;height:90px;background:#F0F3FA;border-radius:10px;
                    display:flex;align-items:center;justify-content:center;
                    border:2px dashed #C8D0E0;margin:auto;">
                    <span style="font-size:24px;color:#B0BACF;">📷</span>
                </div>
                <p style='text-align:center;font-size:11px;color:#B0BACF;margin:4px 0;'>{pos['label'][:12]}...</p>
                """, unsafe_allow_html=True)

    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Zurück", use_container_width=True):
            _state_zuruecksetzen()
            st.session_state.seite = "onboarding_daten"
            st.rerun()
    with col2:
        if fertig:
            if st.button("Weiter →", type="primary", use_container_width=True):
                with st.spinner("Trainiere Gesichtserkennung..."):
                    nutzer_id = st.session_state.onboarding_daten["nutzer_id"]
                    fotos_liste = [
                        st.session_state.gesicht_fotos[p["key"]] for p in POSITIONEN
                    ]
                    nutzer_registrieren(nutzer_id, fotos_liste)
                st.session_state.seite = "onboarding_fragebogen"
                st.rerun()
