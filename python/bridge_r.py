# ============================================================
#  StudyBot — bridge_r.py
#  Bridge zwischen Python und R
#  Lokaler Modus: ruft R-Skripte via subprocess auf
#  Cloud-Modus: gibt vorberechnete Fallback-Ergebnisse zurück
# ============================================================

import subprocess
import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R_SCRIPTS_DIR = os.path.join(BASE_DIR, "r_scripts")
CACHE_DATEI = os.path.join(BASE_DIR, "daten", "ml_cache.json")


# ── R-Verfügbarkeit prüfen (einmalig beim Import) ────────────
def _r_verfuegbar():
    try:
        subprocess.run(["Rscript", "--version"],
                       capture_output=True, timeout=5)
        return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False

R_VERFUEGBAR = _r_verfuegbar()


# ── Fallback-Ergebnisse (wenn R nicht verfügbar) ─────────────
def _fallback_cluster(tage, dauer):
    """Bestimmt Cluster-Zuordnung regelbasiert ohne R."""
    if tage <= 2 and dauer <= 45:
        name = "dringend_kurz"
    elif tage <= 2 and dauer > 45:
        name = "dringend_lang"
    elif dauer > 60:
        name = "geplant_schwer"
    else:
        name = "leicht_locker"
    
    zentren = {
        "dringend_kurz":  [20, 1],
        "dringend_lang":  [100, 2],
        "geplant_schwer": [90, 10],
        "leicht_locker":  [25, 18],
    }
    cx, cy = zentren[name]
    import math
    distanz = round(math.sqrt((dauer - cx)**2 + (tage - cy)**2), 2)
    
    return {
        "cluster_name": name,
        "cluster_nummer": list(zentren.keys()).index(name) + 1,
        "distanz": distanz,
        "methode": "fallback"
    }


def _fallback_prioritaet(tage, dauer, cluster_name):
    """Bestimmt Priorität regelbasiert ohne R."""
    if tage <= 1 or cluster_name in ["dringend_kurz", "dringend_lang"]:
        prio, konfidenz = "kritisch", 96.7
    elif tage <= 3:
        prio, konfidenz = "hoch", 83.3
    elif tage <= 7:
        prio, konfidenz = "mittel", 74.1
    else:
        prio, konfidenz = "niedrig", 68.5
    
    return {
        "prioritaet": prio,
        "konfidenz": konfidenz,
        "wahrscheinlichkeiten": {
            "kritisch": konfidenz if prio == "kritisch" else 3.0,
            "hoch": konfidenz if prio == "hoch" else 8.0,
            "mittel": konfidenz if prio == "mittel" else 12.0,
            "niedrig": konfidenz if prio == "niedrig" else 5.0,
        },
        "methode": "fallback"
    }


def _fallback_nn(lernzeit, schlaf):
    """Gibt Aufmerksamkeitsprofil ohne R zurück."""
    import math
    stunden = list(range(6, 24))
    scores = []
    peak = lernzeit
    for h in stunden:
        dist = abs(h - peak)
        score = max(0.05, 0.91 * math.exp(-0.08 * dist**2))
        # Müdigkeit nach Mitternacht
        if h >= schlaf or h < 7:
            score *= 0.3
        scores.append(round(min(score, 1.0), 3))
    
    beste_idx = scores.index(max(scores))
    beste_stunde = stunden[beste_idx]
    
    return {
        "beste_stunde": beste_stunde,
        "beste_uhrzeit": f"{beste_stunde:02d}:00",
        "score": scores[beste_idx],
        "alle_stunden": stunden,
        "alle_scores": scores,
        "methode": "fallback"
    }


# ── R-Aufruf (wenn R verfügbar) ──────────────────────────────
def _rscript_aufrufen(skript_name, *args):
    skript_pfad = os.path.join(R_SCRIPTS_DIR, skript_name)
    befehl = ["Rscript", "--vanilla", skript_pfad] + [str(a) for a in args]

    try:
        ergebnis = subprocess.run(
            befehl, capture_output=True, text=True,
            cwd=BASE_DIR, timeout=60
        )
    except FileNotFoundError:
        raise RuntimeError("Rscript nicht gefunden.")
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"R-Skript '{skript_name}' Timeout.")

    if ergebnis.returncode != 0:
        raise RuntimeError(f"R-Fehler in {skript_name}:\n{ergebnis.stderr}")

    ausgabe_zeilen = ergebnis.stdout.strip().split("\n")
    json_zeile = ausgabe_zeilen[-1]

    try:
        return json.loads(json_zeile)
    except json.JSONDecodeError:
        raise RuntimeError(f"JSON-Parse-Fehler in {skript_name}:\n{ergebnis.stdout}")


# ── Öffentliche API (identisch wie vorher) ───────────────────
def aufgabe_clustern(tage_bis_faellig, geschaetzt_min, schwierigkeit):
    if R_VERFUEGBAR:
        return _rscript_aufrufen("clustering.R", tage_bis_faellig, geschaetzt_min, schwierigkeit)
    return _fallback_cluster(tage_bis_faellig, geschaetzt_min)


def aufgabe_klassifizieren(tage_bis_faellig, geschaetzt_min, typ, cluster_name):
    if R_VERFUEGBAR:
        return _rscript_aufrufen("naive_bayes.R", tage_bis_faellig, geschaetzt_min, typ, cluster_name)
    return _fallback_prioritaet(tage_bis_faellig, geschaetzt_min, cluster_name)


def optimale_zeit_berechnen(bevorzugte_lernzeit, schlaf_stunde, aufgaben_anzahl):
    if R_VERFUEGBAR:
        return _rscript_aufrufen("neural_network.R", bevorzugte_lernzeit, schlaf_stunde, aufgaben_anzahl)
    return _fallback_nn(bevorzugte_lernzeit, schlaf_stunde)


def vollstaendige_analyse(tage_bis_faellig, geschaetzt_min, schwierigkeit,
                           typ, bevorzugte_lernzeit, schlaf_stunde, aufgaben_anzahl):
    cluster_ergebnis = aufgabe_clustern(tage_bis_faellig, geschaetzt_min, schwierigkeit)
    nb_ergebnis = aufgabe_klassifizieren(
        tage_bis_faellig, geschaetzt_min, typ, cluster_ergebnis["cluster_name"]
    )
    nn_ergebnis = optimale_zeit_berechnen(
        bevorzugte_lernzeit, schlaf_stunde, aufgaben_anzahl
    )
    return {
        "cluster": cluster_ergebnis,
        "prioritaet": nb_ergebnis,
        "optimale_zeit": nn_ergebnis
    }


if __name__ == "__main__":
    print(f"R verfügbar: {R_VERFUEGBAR}")
    ergebnis = vollstaendige_analyse(1, 60, 3, "test", 18, 22, 3)
    print(json.dumps(ergebnis, indent=2, ensure_ascii=False))
