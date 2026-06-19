# ============================================================
#  StudyBot — bridge_r.py
#  Bridge zwischen Python und R
#  Ruft die R-Skripte über subprocess auf und liest das
#  JSON-Ergebnis ein.
# ============================================================

import subprocess
import json
import os

# Pfad zum Projekt-Hauptordner (eine Ebene über python/)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R_SCRIPTS_DIR = os.path.join(BASE_DIR, "r_scripts")


def _rscript_aufrufen(skript_name, *args):
    """
    Ruft ein R-Skript per Kommandozeile auf und gibt das
    geparste JSON-Ergebnis zurück.
    """
    skript_pfad = os.path.join(R_SCRIPTS_DIR, skript_name)
    befehl = ["Rscript", "--vanilla", skript_pfad] + [str(a) for a in args]

    try:
        ergebnis = subprocess.run(
            befehl,
            capture_output=True,
            text=True,
            cwd=BASE_DIR,
            timeout=60
        )
    except FileNotFoundError:
        raise RuntimeError(
            "Rscript wurde nicht gefunden. Stelle sicher, dass R installiert "
            "und 'Rscript' im PATH verfügbar ist (Windows: R-Installationsordner/bin)."
        )
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"R-Skript '{skript_name}' hat das Zeitlimit überschritten.")

    if ergebnis.returncode != 0:
        raise RuntimeError(f"R-Fehler in {skript_name}:\n{ergebnis.stderr}")

    # Die letzte Zeile der Ausgabe ist das JSON-Ergebnis
    # (R gibt vorher noch Trainings-Logs aus, falls Modell neu trainiert wird)
    ausgabe_zeilen = ergebnis.stdout.strip().split("\n")
    json_zeile = ausgabe_zeilen[-1]

    try:
        return json.loads(json_zeile)
    except json.JSONDecodeError:
        raise RuntimeError(
            f"Konnte JSON-Ausgabe von {skript_name} nicht parsen:\n{ergebnis.stdout}"
        )


def aufgabe_clustern(tage_bis_faellig, geschaetzt_min, schwierigkeit):
    """Ruft clustering.R auf — ordnet die Aufgabe einem Cluster zu."""
    return _rscript_aufrufen(
        "clustering.R", tage_bis_faellig, geschaetzt_min, schwierigkeit
    )


def aufgabe_klassifizieren(tage_bis_faellig, geschaetzt_min, typ, cluster_name):
    """Ruft naive_bayes.R auf — berechnet die Priorität."""
    return _rscript_aufrufen(
        "naive_bayes.R", tage_bis_faellig, geschaetzt_min, typ, cluster_name
    )


def optimale_zeit_berechnen(bevorzugte_lernzeit, schlaf_stunde, aufgaben_anzahl):
    """Ruft neural_network.R auf — berechnet die beste Erinnerungszeit."""
    return _rscript_aufrufen(
        "neural_network.R", bevorzugte_lernzeit, schlaf_stunde, aufgaben_anzahl
    )


def vollstaendige_analyse(tage_bis_faellig, geschaetzt_min, schwierigkeit,
                            typ, bevorzugte_lernzeit, schlaf_stunde, aufgaben_anzahl):
    """
    Führt alle 3 ML-Schritte nacheinander aus — das ist die
    zentrale Funktion, die von Streamlit aufgerufen wird.
    """
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
    # Schneller Test ohne Streamlit
    print("Teste R-Bridge...")
    ergebnis = vollstaendige_analyse(
        tage_bis_faellig=1,
        geschaetzt_min=60,
        schwierigkeit=3,
        typ="test",
        bevorzugte_lernzeit=18,
        schlaf_stunde=22,
        aufgaben_anzahl=3
    )
    print(json.dumps(ergebnis, indent=2, ensure_ascii=False))
