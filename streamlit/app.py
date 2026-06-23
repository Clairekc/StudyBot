# ============================================================
#  StudyBot — app.py
#  Haupt-Einstiegspunkt der Streamlit-Anwendung
#
#  STARTEN:  python -m streamlit run streamlit/app.py
#
#  Startet automatisch den Hintergrund-Scheduler als Thread
#  im selben Prozess — kein zweites Terminal nötig.
# ============================================================

import streamlit as st
import sys
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE_DIR, "python"))
sys.path.insert(0, BASE_DIR)

st.set_page_config(
    page_title="StudyBot",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ── Scheduler einmalig starten (nur beim ersten Laden) ────────
if "scheduler_gestartet" not in st.session_state:
    try:
        from scheduler import scheduler_starten
        scheduler_starten()
        st.session_state.scheduler_gestartet = True
        print("[App] ✓ Scheduler gestartet")
    except Exception as e:
        print(f"[App] Scheduler-Fehler: {e}")
        st.session_state.scheduler_gestartet = False

# ── Globales Styling ──────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Poppins', sans-serif;
    }
    .stApp {
        background: linear-gradient(180deg, #F5F9FF 0%, #FFFFFF 100%);
    }
    .studybot-header {
        background: linear-gradient(135deg, #BFE0FF 0%, #E8D5FF 50%, #FFE3F0 100%);
        border-radius: 24px;
        padding: 28px 32px;
        margin-bottom: 20px;
        text-align: center;
        box-shadow: 0 4px 20px rgba(140,170,230,0.18);
    }
    .studybot-title {
        font-size: 48px;
        font-weight: 800;
        color: #2E3A5C;
        margin: 0;
        letter-spacing: -1px;
    }
    .studybot-subtitle {
        font-size: 16px;
        color: #4A5A80;
        margin-top: 4px;
        font-weight: 500;
    }
    .sb-card {
        background: white;
        border-radius: 18px;
        padding: 20px;
        margin-bottom: 14px;
        box-shadow: 0 2px 14px rgba(100,130,200,0.10);
        border: 1px solid #EEF2FA;
    }
    .badge-kritisch { background:#FFE3E3; color:#C0392B; padding:4px 14px; border-radius:20px; font-weight:600; font-size:13px; }
    .badge-hoch     { background:#FFEAD1; color:#D17A1A; padding:4px 14px; border-radius:20px; font-weight:600; font-size:13px; }
    .badge-mittel   { background:#E1F5E1; color:#3A8B3A; padding:4px 14px; border-radius:20px; font-weight:600; font-size:13px; }
    .badge-niedrig  { background:#E3EFFF; color:#3A6BC0; padding:4px 14px; border-radius:20px; font-weight:600; font-size:13px; }
    .stButton > button { border-radius:14px; font-weight:600; padding:10px 20px; border:none; }
    .progress-step { display:inline-block; width:34px; height:34px; border-radius:50%; text-align:center; line-height:34px; font-weight:700; margin:0 4px; font-size:14px; }
    .step-active { background:linear-gradient(135deg,#8FC2FF,#B89FFF); color:white; }
    .step-done   { background:#A8E0A8; color:white; }
    .step-future { background:#E8ECF5; color:#9AA5BD; }
    h1,h2,h3,h4 { color:#2E3A5C; }
    .metric-card { background:white; border-radius:14px; padding:16px; text-align:center; box-shadow:0 2px 10px rgba(100,130,200,0.08); border:1px solid #EEF2FA; }
    .metric-value { font-size:32px; font-weight:800; color:#2E3A5C; }
    .metric-label { font-size:12px; color:#9AA5BD; font-weight:500; }
</style>
""", unsafe_allow_html=True)

# ── Header ─────────────────────────────────────────────────────
st.markdown("""
<div class="studybot-header">
    <p class="studybot-title">🤖 StudyBot</p>
    <p class="studybot-subtitle">Dein smarter Lern- und Aufgabenassistent</p>
</div>
""", unsafe_allow_html=True)

# ── Session State ───────────────────────────────────────────────
if "seite" not in st.session_state:
    st.session_state.seite = "start"
if "aktueller_nutzer" not in st.session_state:
    st.session_state.aktueller_nutzer = None

# ── Router ──────────────────────────────────────────────────────
from seiten import start, onboarding_daten, onboarding_gesicht, onboarding_fragebogen, login, dashboard

seite = st.session_state.seite
if seite == "start":
    start.zeige()
elif seite == "onboarding_daten":
    onboarding_daten.zeige()
elif seite == "onboarding_gesicht":
    onboarding_gesicht.zeige()
elif seite == "onboarding_fragebogen":
    onboarding_fragebogen.zeige()
elif seite == "login":
    login.zeige()
elif seite == "dashboard":
    dashboard.zeige()
