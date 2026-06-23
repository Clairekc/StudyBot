# ============================================================
#  StudyBot — seiten/start.py
#  Startseite: Neuer Nutzer oder bekannter Nutzer?
# ============================================================

import streamlit as st


def zeige():
    st.markdown("""
    <div class="sb-card" style="text-align:center;">
        <p style="color:#4A5A80; font-size:16px; margin:0;">
            Willkommen bei StudyBot — der dir das Leben einfacher macht. ✨
        </p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        <div class="sb-card" style="text-align:center; background:linear-gradient(135deg, #F3E8FF, #FFE3F0);">
            <p style="font-size:34px; margin:0;">🆕</p>
            <p style="font-weight:700; color:#2E3A5C; font-size:16px;">Neuer Nutzer</p>
            <p style="font-size:13px; color:#6B7A99;">Erstelle dein Profil in 3 Schritten</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Onboarding starten", use_container_width=True, type="primary"):
            st.session_state.seite = "onboarding_daten"
            st.rerun()

    with col2:
        st.markdown("""
        <div class="sb-card" style="text-align:center; background:linear-gradient(135deg, #DCEEFF, #E3F5E3);">
            <p style="font-size:34px; margin:0;">👋</p>
            <p style="font-weight:700; color:#2E3A5C; font-size:16px;">Schon dabei</p>
            <p style="font-size:13px; color:#6B7A99;">Melde dich mit deinem Gesicht an</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Anmelden", use_container_width=True):
            st.session_state.seite = "login"
            st.rerun()
