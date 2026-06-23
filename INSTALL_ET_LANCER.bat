@echo off
echo ====================================
echo    StudyBot - Installation
echo ====================================
echo.
echo Installiere Bibliotheken...
pip install streamlit plotly pandas edge-tts streamlit-autorefresh opencv-python face-recognition
echo.
echo Starte StudyBot...
start "" "http://localhost:8501"
python -m streamlit run streamlit/app.py
pause