
import re

# Fix 1: Passwort genau 6 Zeichen
c = open('streamlit/seiten/onboarding_daten.py', encoding='utf-8').read()
c = c.replace('len(passwort) != 6', 'TEMP').replace('len(passwort) < 6', 'len(passwort) != 6').replace('TEMP', 'len(passwort) != 6')
open('streamlit/seiten/onboarding_daten.py', 'w', encoding='utf-8').write(c)
print('Fix 1 OK')

# Fix 2: Rappels passes supprimer
import json, os
from datetime import datetime
for f in os.listdir('daten/tasks'):
    if 'erinnerungen' not in f: continue
    pfad = os.path.join('daten/tasks', f)
    with open(pfad, encoding='utf-8') as fp:
        data = json.load(fp)
    data['erinnerungen'] = [e for e in data['erinnerungen'] if e.get('gesendet') or datetime.fromisoformat(e['zeit']) > datetime.now()]
    with open(pfad, 'w', encoding='utf-8') as fp:
        json.dump(data, fp, ensure_ascii=False, indent=2)
print('Fix 2 OK')

# Fix 3: Autorefresh 10 secondes
c = open('streamlit/seiten/dashboard.py', encoding='utf-8').read()
c = c.replace('interval=30000', 'interval=10000')
open('streamlit/seiten/dashboard.py', 'w', encoding='utf-8').write(c)
print('Fix 3 OK')
