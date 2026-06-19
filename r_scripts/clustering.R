# ============================================================
#  StudyBot — clustering.R
#  k-Means Clusteranalyse für Aufgaben (Tasks)
#
#  ZIEL: Jede Aufgabe wird automatisch einem von 4 Verhaltens-
#  Clustern zugeordnet, basierend auf Dringlichkeit und Aufwand.
#
#  CLUSTER:
#    A = Dringend + Kurz      → Sofortige Erinnerung
#    B = Dringend + Lang      → Mehrfache Erinnerungen, Etappen
#    C = Nicht dringend + Schwer → Frühzeitig planen
#    D = Nicht dringend + Einfach → Sanfte Erinnerung
#
#  AUFRUF AUS PYTHON (über subprocess oder rpy2):
#    Rscript clustering.R <tage_bis_faellig> <geschaetzt_min> <schwierigkeit>
# ============================================================

library(cluster)
library(jsonlite)

MODELL_PFAD <- "daten/models/clustering.rds"

# ── Trainingsdaten generieren ────────────────────────────────
# Simuliert 200 typische Schüleraufgaben für das Training
clustering_trainingsdaten <- function(n = 200) {
  set.seed(42)

  # Cluster A: Dringend + Kurz (z.B. "Vokabeln lernen bis morgen")
  a <- data.frame(
    tage_bis_faellig = runif(n/4, 0, 2),
    geschaetzt_min    = runif(n/4, 10, 30),
    schwierigkeit     = sample(1:2, n/4, replace = TRUE),
    label = "dringend_kurz"
  )

  # Cluster B: Dringend + Lang (z.B. "Referat in 3 Tagen fertig")
  b <- data.frame(
    tage_bis_faellig = runif(n/4, 0, 4),
    geschaetzt_min    = runif(n/4, 90, 240),
    schwierigkeit     = sample(2:3, n/4, replace = TRUE),
    label = "dringend_lang"
  )

  # Cluster C: Nicht dringend + Schwer (z.B. "Mathe-Projekt in 3 Wochen")
  c <- data.frame(
    tage_bis_faellig = runif(n/4, 7, 30),
    geschaetzt_min    = runif(n/4, 60, 180),
    schwierigkeit     = sample(2:3, n/4, replace = TRUE),
    label = "geplant_schwer"
  )

  # Cluster D: Nicht dringend + Einfach (z.B. "Zimmer aufräumen")
  d <- data.frame(
    tage_bis_faellig = runif(n/4, 5, 20),
    geschaetzt_min    = runif(n/4, 5, 25),
    schwierigkeit     = sample(1:2, n/4, replace = TRUE),
    label = "leicht_locker"
  )

  rbind(a, b, c, d)
}

# ── k-Means Modell trainieren ────────────────────────────────
clustering_trainieren <- function(k = 4) {
  cat("[Clustering] Trainiere k-Means mit k =", k, "...\n")

  daten <- clustering_trainingsdaten()
  X     <- scale(daten[, c("tage_bis_faellig", "geschaetzt_min", "schwierigkeit")])

  set.seed(42)
  km <- kmeans(X, centers = k, nstart = 25, iter.max = 100)

  # Cluster-Nummer → sprechende Bezeichnung zuordnen
  zuordnung_tabelle <- table(km$cluster, daten$label)
  cluster_namen <- apply(zuordnung_tabelle, 1, function(zeile) {
    names(which.max(zeile))
  })

  cat("[Clustering] Cluster-Zuordnung:\n")
  print(zuordnung_tabelle)

  ergebnis <- list(
    modell      = km,
    namen       = cluster_namen,
    skalierung  = list(
      mittelwert = attr(X, "scaled:center"),
      std_abw    = attr(X, "scaled:scale")
    )
  )

  if (!dir.exists("daten/models")) dir.create("daten/models", recursive = TRUE)
  saveRDS(ergebnis, MODELL_PFAD)
  cat("[Clustering] Modell gespeichert:", MODELL_PFAD, "\n")
  ergebnis
}

# ── Modell laden (oder neu trainieren, falls nicht vorhanden) ─
clustering_laden <- function() {
  if (file.exists(MODELL_PFAD)) {
    return(readRDS(MODELL_PFAD))
  }
  clustering_trainieren()
}

# ── Eine neue Aufgabe klassifizieren ─────────────────────────
aufgabe_clustern <- function(tage_bis_faellig, geschaetzt_min, schwierigkeit) {
  modell <- clustering_laden()

  punkt <- c(tage_bis_faellig, geschaetzt_min, schwierigkeit)
  punkt_skaliert <- (punkt - modell$skalierung$mittelwert) / modell$skalierung$std_abw

  # Abstand zu allen Zentren berechnen
  zentren <- modell$modell$centers
  abstaende <- apply(zentren, 1, function(z) sqrt(sum((punkt_skaliert - z)^2)))

  naechstes_cluster <- which.min(abstaende)
  cluster_name <- modell$namen[naechstes_cluster]

  list(
    cluster_id   = as.integer(naechstes_cluster),
    cluster_name = unname(cluster_name),
    abstand      = round(min(abstaende), 3)
  )
}

# ── Kommandozeilen-Schnittstelle (für Python-Aufruf) ─────────
# Erlaubt Aufruf wie: Rscript clustering.R 3 90 2
if (!interactive()) {
  args <- commandArgs(trailingOnly = TRUE)
  if (length(args) >= 3) {
    ergebnis <- aufgabe_clustern(
      as.numeric(args[1]),
      as.numeric(args[2]),
      as.numeric(args[3])
    )
    # JSON-Ausgabe für Python lesbar
    cat(toJSON(ergebnis, auto_unbox = TRUE))
  }
}
