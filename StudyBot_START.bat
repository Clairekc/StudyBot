@echo off
cd /d "%~dp0"
echo StudyBot wird gestartet...
start "" "http://localhost:8501"
python -m streamlit run streamlit/app.py --server.port 8501
pause