import subprocess
import webbrowser
import time
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))
subprocess.Popen(["pip", "install", "streamlit", "plotly", "pandas", "edge-tts", "streamlit-autorefresh", "opencv-python", "--quiet"])
time.sleep(5)
webbrowser.open("http://localhost:8501")
subprocess.run(["python", "-m", "streamlit", "run", "streamlit/app.py"])