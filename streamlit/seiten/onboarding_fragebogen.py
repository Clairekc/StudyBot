# ============================================================
#  StudyBot — seiten/onboarding_fragebogen.py
#  Onboarding Schritt 3: Fragebogen über Gewohnheiten
#
#  WICHTIG: Alle Antworten sind vorgegeben (Klick statt Tippen)
# ============================================================

import streamlit as st
import os
import json
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PROFILE_DIR = os.path.join(BASE_DIR, "daten", "profile")
os.makedirs(PROFILE_DIR, exist_ok=True)


def zeige():
    from seiten.onboarding_daten import fortschritt_anzeigen
    fortschritt_anzeigen(3)

    vorname = st.session_state.onboarding_daten["vorname"]

    st.markdown(f"""
    <div class="sb-card">
        <h4 style="color:#3A4A6B; margin-top:0;">Schritt 3 — Deine Gewohnheiten</h4>
        <p style="color:#6B7A99; font-size:14px;">
            {vorname}, beantworte ein paar kurze Fragen — einfach anklicken,
            kein Tippen nötig.
        </p>
    </div>
    """, unsafe_allow_html=True)

    with st.form("fragebogen_formular"):

        st.markdown("**1. Wann stehst du normalerweise auf?**")
        aufstehen = st.radio(
            "aufstehen", ["Vor 6:30 Uhr", "6:30 – 7:30 Uhr", "7:30 – 8:30 Uhr", "Nach 8:30 Uhr"],
            label_visibility="collapsed", horizontal=True
        )

        st.markdown("**2. Wann gehst du normalerweise schlafen?**")
        schlafen = st.radio(
            "schlafen", ["Vor 21 Uhr", "21 – 22 Uhr", "22 – 23 Uhr", "23 – 0 Uhr", "Nach 0 Uhr"],
            label_visibility="collapsed", horizontal=True
        )

        st.markdown("**3. Wann lernst du am liebsten?**")
        lernzeit = st.radio(
            "lernzeit", ["Morgens (6–10 Uhr)", "Mittags (10–14 Uhr)",
                         "Nachmittags (14–18 Uhr)", "Abends (18–22 Uhr)", "Nachts (nach 22 Uhr)"],
            label_visibility="collapsed", horizontal=True
        )

        st.markdown("**4. Wie lange kannst du dich am Stück konzentrieren?**")
        konzentration = st.radio(
            "konzentration", ["Unter 20 Minuten", "20 – 40 Minuten", "40 – 60 Minuten", "Über 60 Minuten"],
            label_visibility="collapsed", horizontal=True
        )

        st.markdown("**5. Wann isst du normalerweise zu Mittag?**")
        mittagessen = st.radio(
            "mittag", ["Vor 12 Uhr", "12 – 13 Uhr", "13 – 14 Uhr", "Nach 14 Uhr"],
            label_visibility="collapsed", horizontal=True
        )

        st.markdown("**6. Wie oft vergisst du Hausaufgaben oder Termine?**")
        vergesslichkeit = st.radio(
            "vergessen", ["Fast nie", "Selten", "Manchmal", "Oft"],
            label_visibility="collapsed", horizontal=True
        )

        st.markdown("**7. Was machst du am liebsten zur Entspannung?**")
        entspannung = st.radio(
            "entspannung", ["Sport", "Musik hören", "Serien/Videos schauen", "Mit Freunden treffen", "Lesen"],
            label_visibility="collapsed", horizontal=True
        )

        st.markdown("**8. Wie lernst du am liebsten?**")
        lernstil = st.radio(
            "lernstil", ["Alleine, ruhig", "Mit Musik im Hintergrund", "In der Gruppe", "Mit Pausen alle 25 Min"],
            label_visibility="collapsed", horizontal=True
        )

        st.markdown("**9. Wann treibst du am liebsten Sport?**")
        sportzeit = st.radio(
            "sport", ["Morgens", "Nachmittags", "Abends", "Ich mache selten Sport"],
            label_visibility="collapsed", horizontal=True
        )

        st.markdown("**10. Wie viele Aufgaben hast du durchschnittlich pro Tag?**")
        aufgaben_pro_tag = st.radio(
            "aufgaben", ["1 – 2", "3 – 4", "5 – 6", "Mehr als 6"],
            label_visibility="collapsed", horizontal=True
        )

        abgeschickt = st.form_submit_button("Onboarding abschließen ✓", type="primary", use_container_width=True)

        if abgeschickt:
            antworten = {
                "aufstehen": aufstehen,
                "schlafen": schlafen,
                "lernzeit": lernzeit,
                "konzentration": konzentration,
                "mittagessen": mittagessen,
                "vergesslichkeit": vergesslichkeit,
                "entspannung": entspannung,
                "lernstil": lernstil,
                "sportzeit": sportzeit,
                "aufgaben_pro_tag": aufgaben_pro_tag
            }

            # Vollständiges Profil zusammenbauen und speichern
            profil = {
                **st.session_state.onboarding_daten,
                "fragebogen": antworten,
                "streak": 0,
                "punkte": 0
            }

            nutzer_id = profil["nutzer_id"]
            pfad = os.path.join(PROFILE_DIR, f"{nutzer_id}.json")
            with open(pfad, "w", encoding="utf-8") as f:
                json.dump(profil, f, ensure_ascii=False, indent=2)

            # E-Mails senden (Bestätigung an Nutzer + Info an Admin)
            try:
                import sys
                BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                sys.path.insert(0, os.path.join(BASE_DIR, "python"))
                from email_service import registrierungs_emails_senden
                registrierungs_emails_senden(
                    profil["vorname"], profil["nachname"],
                    profil["email"], nutzer_id
                )
            except Exception as e:
                print(f"[Email] Fehler: {e}")

            st.session_state.aktueller_nutzer = nutzer_id
            st.session_state.profil = profil
            st.session_state.onboarding_erfolg = True
            st.rerun()

    # ── Erfolgsmeldung nach Abschluss ──────────────────────────
    if st.session_state.get("onboarding_erfolg"):
        st.balloons()
        st.success(f"🎉 Willkommen, {vorname}! Dein Onboarding war erfolgreich.")
        if st.button("Zum Dashboard →", type="primary", use_container_width=True):
            # Aufräumen
            for key in ["onboarding_daten", "gesicht_fotos", "gesicht_vorschau", "onboarding_erfolg"]:
                st.session_state.pop(key, None)
            st.session_state.seite = "dashboard"
            st.rerun()

    if st.button("← Zurück"):
        st.session_state.seite = "onboarding_gesicht"
        st.rerun()
