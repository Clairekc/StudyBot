# ============================================================
#  StudyBot — seiten/onboarding_daten.py
#  Onboarding Schritt 1: Persönliche Daten + Passwort
# ============================================================

import streamlit as st
import os, json, re, hashlib
from datetime import date, datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PROFILE_DIR = os.path.join(BASE_DIR, "daten", "profile")
os.makedirs(PROFILE_DIR, exist_ok=True)


def fortschritt_anzeigen(aktueller_schritt):
    schritte = ["Daten", "Gesicht", "Fragebogen"]
    html = '<div style="text-align:center; margin-bottom:20px;">'
    for i, name in enumerate(schritte, start=1):
        if i < aktueller_schritt:
            klasse, symbol = "step-done", "✓"
        elif i == aktueller_schritt:
            klasse, symbol = "step-active", str(i)
        else:
            klasse, symbol = "step-future", str(i)
        html += f'<span class="progress-step {klasse}">{symbol}</span>'
        if i < len(schritte):
            html += '<span style="color:#D0D8E8;">────</span>'
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)


def passwort_hashen(passwort):
    """Hasht das Passwort sicher — wird nie im Klartext gespeichert."""
    return hashlib.sha256(passwort.encode("utf-8")).hexdigest()


def nutzer_existiert_bereits(nutzer_id):
    """Prüft ob bereits ein Profil mit dieser ID existiert."""
    pfad = os.path.join(PROFILE_DIR, f"{nutzer_id}.json")
    return os.path.exists(pfad)


def zeige():
    fortschritt_anzeigen(1)

    st.markdown("""
    <div class="sb-card">
        <h4 style="color:#2E3A5C; margin-top:0;">Schritt 1 — Deine Daten</h4>
        <p style="color:#6B7A99; font-size:14px;">
            Erzähl uns kurz wer du bist und wähle ein sicheres Passwort.
            Du brauchst es beim nächsten Login.
        </p>
    </div>
    """, unsafe_allow_html=True)

    with st.form("daten_formular"):
        col1, col2 = st.columns(2)
        with col1:
            vorname = st.text_input("Vorname")
        with col2:
            nachname = st.text_input("Nachname")

        col3, col4 = st.columns(2)
        with col3:
            geburtsdatum = st.date_input(
                "Geburtsdatum",
                value=date(2005, 1, 1),
                min_value=date(1950, 1, 1),  # Minimum 1950
                max_value=date.today()
            )
        with col4:
            email = st.text_input("E-Mail-Adresse")

        st.markdown("---")
        col5, col6 = st.columns(2)
        with col5:
            passwort = st.text_input(
                "🔒 Passwort wählen",
                type="password",
                help="Mindestens 6 Zeichen. Du brauchst es beim Login."
            )
        with col6:
            passwort_bestaetigung = st.text_input(
                "🔒 Passwort bestätigen",
                type="password"
            )

        abgeschickt = st.form_submit_button(
            "Weiter →", type="primary", use_container_width=True
        )

        if abgeschickt:
            fehler = []
            if not vorname.strip():
                fehler.append("Bitte gib deinen Vornamen ein.")
            if not nachname.strip():
                fehler.append("Bitte gib deinen Nachnamen ein.")
            if "@" not in email or "." not in email:
                fehler.append("Bitte gib eine gültige E-Mail-Adresse ein.")
            if len(passwort) != 6:
                fehler.append("Das Passwort muss mindestens 6 Zeichen haben.")
            if passwort != passwort_bestaetigung:
                fehler.append("Die Passwörter stimmen nicht überein.")

            if fehler:
                for f in fehler:
                    st.error(f)
            else:
                # ID stabil basiert auf Name (kein Timestamp)
                nutzer_id = re.sub(
                    r'[^a-z0-9]', '_',
                    f"{vorname.lower()}_{nachname.lower()}"
                )[:30]

                # Prüfen ob dieser Nutzer bereits existiert
                if nutzer_existiert_bereits(nutzer_id):
                    st.error(
                        f"⚠️ Ein Konto für '{vorname} {nachname}' existiert bereits! "
                        f"Bitte melde dich über den Login an."
                    )
                    st.info("👉 Gehe zur Startseite und klicke auf 'Schon dabei'.")
                else:
                    st.session_state.onboarding_daten = {
                        "nutzer_id": nutzer_id,
                        "vorname": vorname.strip(),
                        "nachname": nachname.strip(),
                        "geburtsdatum": str(geburtsdatum),
                        "email": email.strip(),
                        "passwort_hash": passwort_hashen(passwort),
                        "erstellt_am": str(datetime.now())
                    }
                    st.session_state.seite = "onboarding_gesicht"
                    st.rerun()

    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("← Zurück", use_container_width=True):
            st.session_state.seite = "start"
            st.rerun()
