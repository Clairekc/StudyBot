# ============================================================
#  StudyBot — python/audio_service.py
#  Sprachausgabe über Microsoft Edge TTS (KatjaNeural)
#  Hochwertige deutsche Stimme, kein Browser nötig
# ============================================================

import asyncio
import os
import subprocess
from datetime import datetime

VOICE = "de-DE-KatjaNeural"
AUDIO_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "daten", "audio")
os.makedirs(AUDIO_DIR, exist_ok=True)


def nachricht_generieren(titel, prioritaet, erinnerungs_zeit_str, deadline_zeit_str=None):
    """Generiert die passende Sprachnachricht."""
    jetzt = datetime.now()

    if deadline_zeit_str:
        try:
            deadline = datetime.fromisoformat(deadline_zeit_str)
            diff = deadline - jetzt
            gesamt_minuten = diff.total_seconds() / 60
        except Exception:
            gesamt_minuten = None
    else:
        gesamt_minuten = None

    if gesamt_minuten is not None and gesamt_minuten > 0:
        if gesamt_minuten >= 1440:
            tage = int(gesamt_minuten / 1440)
            zeitangabe = f"in {tage} {'Tag' if tage == 1 else 'Tagen'}"
            zeittyp = "tage"
        elif gesamt_minuten >= 60:
            stunden = int(gesamt_minuten / 60)
            zeitangabe = f"heute in {stunden} {'Stunde' if stunden == 1 else 'Stunden'}"
            zeittyp = "stunden"
        else:
            minuten = int(gesamt_minuten)
            zeitangabe = f"in {minuten} {'Minute' if minuten == 1 else 'Minuten'}"
            zeittyp = "minuten"
    else:
        zeitangabe = "jetzt"
        zeittyp = "minuten"

    if prioritaet == "kritisch":
        if zeittyp == "tage":
            return f"Wichtig! {titel} ist {zeitangabe}. Bereite dich unbedingt vor!"
        elif zeittyp == "stunden":
            return f"Achtung! {titel} ist {zeitangabe}. Mach dich fertig!"
        else:
            return f"Alarm! {titel} beginnt {zeitangabe}! Sofort handeln!"
    elif prioritaet == "hoch":
        if zeittyp == "tage":
            return f"Erinnerung: {titel} ist {zeitangabe}. Fang rechtzeitig an!"
        elif zeittyp == "stunden":
            return f"{titel} ist {zeitangabe} fällig. Bereite dich vor!"
        else:
            return f"Dringend! {titel} {zeitangabe}!"
    elif prioritaet == "mittel":
        if zeittyp == "tage":
            return f"Nicht vergessen: {titel} ist {zeitangabe}."
        elif zeittyp == "stunden":
            return f"{titel} ist heute fällig. Du hast noch {zeitangabe.replace('heute ', '')}."
        else:
            return f"Erinnerung: {titel} {zeitangabe}."
    else:
        if zeittyp == "tage":
            return f"Kurze Erinnerung: {titel} ist {zeitangabe}."
        elif zeittyp == "stunden":
            return f"{titel} heute nicht vergessen!"
        else:
            return f"{titel} {zeitangabe}."


async def _text_zu_audio(nachricht, datei_pfad):
    """Konvertiert Text zu Audio mit Edge TTS."""
    import edge_tts
    tts = edge_tts.Communicate(nachricht, voice=VOICE, rate="-5%")
    await tts.save(datei_pfad)


def audio_abspielen(nachricht):
    """Spielt eine Sprachnachricht ab — direkt, ohne Browser."""
    try:
        datei = os.path.join(AUDIO_DIR, "alarm.mp3")
        asyncio.run(_text_zu_audio(nachricht, datei))
        # Windows: direkt abspielen
        os.startfile(datei)
        print(f"[Audio] Abgespielt: {nachricht[:50]}")
        return True
    except Exception as e:
        print(f"[Audio] Fehler: {e}")
        return False


def audio_javascript(nachricht, lautstaerke=1.0, geschwindigkeit=0.9):
    """
    Fallback: Web Speech API für Streamlit-Dashboard.
    Wird verwendet wenn Edge TTS nicht direkt abgespielt werden kann.
    """
    nachricht_escaped = nachricht.replace("'", "\\'").replace('"', '\\"')
    return f"""
    <script>
    (function() {{
        if ('speechSynthesis' in window) {{
            window.speechSynthesis.cancel();
            var msg = new SpeechSynthesisUtterance('{nachricht_escaped}');
            msg.lang = 'de-DE';
            msg.volume = {lautstaerke};
            msg.rate = {geschwindigkeit};
            msg.pitch = 1.0;
            var stimmen = window.speechSynthesis.getVoices();
            var de_stimme = stimmen.find(s => s.lang && s.lang.startsWith('de'));
            if (de_stimme) msg.voice = de_stimme;
            window.speechSynthesis.speak(msg);
        }}
    }})();
    </script>
    """


def alarm_javascript(prioritaet):
    """Bip-Ton je nach Priorität."""
    configs = {
        "kritisch": {"freq": 880, "dauer": 0.5, "n": 3},
        "hoch":     {"freq": 660, "dauer": 0.4, "n": 2},
        "mittel":   {"freq": 523, "dauer": 0.3, "n": 1},
        "niedrig":  {"freq": 440, "dauer": 0.2, "n": 1},
    }
    c = configs.get(prioritaet, configs["mittel"])
    return f"""
    <script>
    (function() {{
        var ctx = new (window.AudioContext || window.webkitAudioContext)();
        function beep(i) {{
            if (i >= {c['n']}) return;
            var osc = ctx.createOscillator();
            var gain = ctx.createGain();
            osc.connect(gain); gain.connect(ctx.destination);
            osc.frequency.value = {c['freq']};
            osc.type = 'sine';
            gain.gain.setValueAtTime(0.3, ctx.currentTime);
            gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + {c['dauer']});
            osc.start(ctx.currentTime); osc.stop(ctx.currentTime + {c['dauer']});
            setTimeout(function() {{ beep(i+1); }}, {int((c['dauer']+0.1)*1000)});
        }}
        beep(0);
    }})();
    </script>
    """
