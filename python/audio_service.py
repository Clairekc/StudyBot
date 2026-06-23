# ============================================================
#  StudyBot — python/audio_service.py
#  Sprachausgabe über Web Speech API (Browser-TTS)
#  Kein Arduino nötig — funktioniert direkt im Browser
# ============================================================

from datetime import datetime


def nachricht_generieren(titel, prioritaet, erinnerungs_zeit_str, deadline_zeit_str=None):
    """
    Generiert die passende Sprachnachricht basierend auf:
    - Priorität (kritisch/hoch/mittel/niedrig)
    - Zeit bis Deadline (Tage / Stunden / Minuten)
    """
    jetzt = datetime.now()
    erinnerungs_zeit = datetime.fromisoformat(erinnerungs_zeit_str)

    # Deadline berechnen wenn angegeben
    if deadline_zeit_str:
        try:
            deadline = datetime.fromisoformat(deadline_zeit_str)
            diff = deadline - jetzt
            gesamt_minuten = diff.total_seconds() / 60
        except Exception:
            gesamt_minuten = None
    else:
        gesamt_minuten = None

    # Zeit bis Deadline bestimmen
    if gesamt_minuten is not None and gesamt_minuten > 0:
        if gesamt_minuten >= 1440:  # Mehr als 1 Tag
            tage = int(gesamt_minuten / 1440)
            zeitangabe = f"in {tage} {'Tag' if tage == 1 else 'Tagen'}"
            zeittyp = "tage"
        elif gesamt_minuten >= 60:  # Mehr als 1 Stunde
            stunden = int(gesamt_minuten / 60)
            zeitangabe = f"heute in {stunden} {'Stunde' if stunden == 1 else 'Stunden'}"
            zeittyp = "stunden"
        else:  # Minuten
            minuten = int(gesamt_minuten)
            zeitangabe = f"in {minuten} {'Minute' if minuten == 1 else 'Minuten'}"
            zeittyp = "minuten"
    else:
        zeitangabe = "jetzt"
        zeittyp = "minuten"

    # Nachricht nach Priorität und Zeittyp
    if prioritaet == "kritisch":
        if zeittyp == "tage":
            nachricht = f"Wichtig! {titel} ist {zeitangabe}. Bereite dich unbedingt vor!"
        elif zeittyp == "stunden":
            nachricht = f"Achtung! {titel} ist {zeitangabe}. Mach dich fertig!"
        else:
            nachricht = f"Alarm! {titel} beginnt {zeitangabe}! Sofort handeln!"

    elif prioritaet == "hoch":
        if zeittyp == "tage":
            nachricht = f"Erinnerung: {titel} ist {zeitangabe}. Fang rechtzeitig an!"
        elif zeittyp == "stunden":
            nachricht = f"{titel} ist {zeitangabe} fällig. Bereite dich vor!"
        else:
            nachricht = f"Dringend! {titel} {zeitangabe}!"

    elif prioritaet == "mittel":
        if zeittyp == "tage":
            nachricht = f"Nicht vergessen: {titel} ist {zeitangabe}."
        elif zeittyp == "stunden":
            nachricht = f"{titel} ist heute fällig. Du hast noch {zeitangabe.replace('heute ', '')}."
        else:
            nachricht = f"Erinnerung: {titel} {zeitangabe}."

    else:  # niedrig
        if zeittyp == "tage":
            nachricht = f"Kurze Erinnerung: {titel} ist {zeitangabe}."
        elif zeittyp == "stunden":
            nachricht = f"{titel} heute nicht vergessen!"
        else:
            nachricht = f"{titel} {zeitangabe}."

    return nachricht


def audio_javascript(nachricht, lautstaerke=1.0, geschwindigkeit=0.9):
    """
    Gibt JavaScript-Code zurück der die Nachricht im Browser vorliest.
    Wird in Streamlit via st.components.v1.html() eingebettet.
    """
    # Anführungszeichen in der Nachricht escapen
    nachricht_escaped = nachricht.replace("'", "\\'").replace('"', '\\"')

    js_code = f"""
    <script>
    (function() {{
        if ('speechSynthesis' in window) {{
            window.speechSynthesis.cancel();
            var msg = new SpeechSynthesisUtterance('{nachricht_escaped}');
            msg.lang = 'de-DE';
            msg.volume = {lautstaerke};
            msg.rate = {geschwindigkeit};
            msg.pitch = 1.0;

            // Beste deutsche Stimme auswählen
            var stimmen = window.speechSynthesis.getVoices();
            var de_stimme = stimmen.find(s => s.lang.startsWith('de'));
            if (de_stimme) msg.voice = de_stimme;

            window.speechSynthesis.speak(msg);
        }} else {{
            console.log('Web Speech API nicht verfügbar');
        }}
    }})();
    </script>
    """
    return js_code


def alarm_javascript(prioritaet):
    """
    Gibt einen kurzen Alarm-Ton aus (Beep) vor der Sprachnachricht.
    Frequenz und Dauer je nach Priorität.
    """
    configs = {
        "kritisch": {"freq": 880, "dauer": 0.5, "wiederholungen": 3},
        "hoch":     {"freq": 660, "dauer": 0.4, "wiederholungen": 2},
        "mittel":   {"freq": 523, "dauer": 0.3, "wiederholungen": 1},
        "niedrig":  {"freq": 440, "dauer": 0.2, "wiederholungen": 1},
    }
    c = configs.get(prioritaet, configs["mittel"])

    js_code = f"""
    <script>
    (function() {{
        var ctx = new (window.AudioContext || window.webkitAudioContext)();
        var wiederholungen = {c['wiederholungen']};
        var dauer = {c['dauer']};
        var freq = {c['freq']};

        function beep(i) {{
            if (i >= wiederholungen) return;
            var osc = ctx.createOscillator();
            var gain = ctx.createGain();
            osc.connect(gain);
            gain.connect(ctx.destination);
            osc.frequency.value = freq;
            osc.type = 'sine';
            gain.gain.setValueAtTime(0.3, ctx.currentTime);
            gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + dauer);
            osc.start(ctx.currentTime);
            osc.stop(ctx.currentTime + dauer);
            setTimeout(function() {{ beep(i + 1); }}, (dauer + 0.1) * 1000);
        }}
        beep(0);
    }})();
    </script>
    """
    return js_code
