c = open('scheduler.py', encoding='utf-8').read()
old = 'audio_alarm_speichern(titel, prioritaet, erinnerungs_zeit)'
new = '''audio_alarm_speichern(titel, prioritaet, erinnerungs_zeit)
                try:
                    from audio_service import nachricht_generieren, audio_abspielen
                    msg = nachricht_generieren(titel, prioritaet, erinnerungs_zeit)
                    audio_abspielen(msg)
                except Exception as e:
                    _log(f"Audio Fehler: {e}", "fehler")'''
c = c.replace(old, new)
open('scheduler.py', 'w', encoding='utf-8').write(c)
print('OK')