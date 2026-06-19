# ============================================================
#  StudyBot — naive_bayes.R
#  Naive Bayes Klassifikation der Aufgaben-Priorität
#
#  ZIEL: Berechnet die Wahrscheinlichkeit für jede Prioritäts-
#  klasse basierend auf Deadline, Aufwand, Typ und Cluster.
#
#  KLASSEN: kritisch | hoch | mittel | niedrig
#
#  AUFRUF AUS PYTHON:
#    Rscript naive_bayes.R <tage_bis_faellig> <geschaetzt_min> <typ> <cluster_name>
# ============================================================

library(e1071)
library(jsonlite)

MODELL_PFAD <- "daten/models/naive_bayes.rds"

# ── Trainingsdaten generieren ────────────────────────────────
nb_trainingsdaten <- function(n = 300) {
  set.seed(7)

  daten <- data.frame(
    tage_bis_faellig = sample(-2:20, n, replace = TRUE),
    geschaetzt_min    = sample(c(10,20,30,45,60,90,120,180), n, replace = TRUE),
    typ = factor(
      sample(c("hausaufgabe","test","projekt","erinnerung"), n,
             replace = TRUE, prob = c(0.45, 0.25, 0.20, 0.10)),
      levels = c("hausaufgabe","test","projekt","erinnerung")
    ),
    cluster_name = factor(
      sample(c("dringend_kurz","dringend_lang","geplant_schwer","leicht_locker"),
             n, replace = TRUE),
      levels = c("dringend_kurz","dringend_lang","geplant_schwer","leicht_locker")
    )
  )

  # Priorität nach klaren Regeln ableiten (mit etwas Rauschen)
  daten$prioritaet <- with(daten, ifelse(
    tage_bis_faellig < 0 | cluster_name == "dringend_lang", "kritisch",
    ifelse(tage_bis_faellig <= 2 | typ == "test", "hoch",
    ifelse(tage_bis_faellig <= 7 | cluster_name == "geplant_schwer", "mittel",
    "niedrig"))
  ))

  # 5% Rauschen für realistischere Daten
  rauschen_idx <- sample(1:n, round(n * 0.05))
  daten$prioritaet[rauschen_idx] <- sample(
    c("kritisch","hoch","mittel","niedrig"), length(rauschen_idx), replace = TRUE
  )
  daten$prioritaet <- factor(daten$prioritaet,
                              levels = c("kritisch","hoch","mittel","niedrig"))

  cat(sprintf("[Naive Bayes] %d Trainingsdaten erstellt.\n", nrow(daten)))
  daten
}

# ── Modell trainieren ─────────────────────────────────────────
nb_trainieren <- function() {
  cat("[Naive Bayes] Trainiere Modell...\n")
  daten <- nb_trainingsdaten()

  set.seed(123)
  train_idx <- sample(1:nrow(daten), round(nrow(daten) * 0.8))
  train <- daten[train_idx, ]
  test  <- daten[-train_idx, ]

  modell <- naiveBayes(
    prioritaet ~ tage_bis_faellig + geschaetzt_min + typ + cluster_name,
    data = train,
    laplace = 1   # Laplace-Glättung gegen Zero-Probability
  )

  vorhersage <- predict(modell, test)
  genauigkeit <- round(mean(vorhersage == test$prioritaet) * 100, 1)
  cat(sprintf("[Naive Bayes] Genauigkeit: %.1f%%\n", genauigkeit))
  cat("[Naive Bayes] Konfusionsmatrix:\n")
  print(table(Vorhersage = vorhersage, Tatsaechlich = test$prioritaet))

  if (!dir.exists("daten/models")) dir.create("daten/models", recursive = TRUE)
  saveRDS(modell, MODELL_PFAD)
  cat("[Naive Bayes] Modell gespeichert:", MODELL_PFAD, "\n")
  modell
}

# ── Modell laden ──────────────────────────────────────────────
nb_laden <- function() {
  if (file.exists(MODELL_PFAD)) return(readRDS(MODELL_PFAD))
  nb_trainieren()
}

# ── Eine Aufgabe klassifizieren ───────────────────────────────
aufgabe_klassifizieren <- function(tage_bis_faellig, geschaetzt_min, typ, cluster_name) {
  modell <- nb_laden()

  neu <- data.frame(
    tage_bis_faellig = as.numeric(tage_bis_faellig),
    geschaetzt_min    = as.numeric(geschaetzt_min),
    typ = factor(typ, levels = c("hausaufgabe","test","projekt","erinnerung")),
    cluster_name = factor(cluster_name,
                           levels = c("dringend_kurz","dringend_lang",
                                      "geplant_schwer","leicht_locker"))
  )

  wahrsch <- predict(modell, neu, type = "raw")
  klasse  <- predict(modell, neu)

  list(
    prioritaet = as.character(klasse),
    konfidenz  = round(max(wahrsch) * 100, 1),
    wahrscheinlichkeiten = round(as.numeric(wahrsch), 4),
    klassen = colnames(wahrsch)
  )
}

# ── Kommandozeilen-Schnittstelle ──────────────────────────────
if (!interactive()) {
  args <- commandArgs(trailingOnly = TRUE)
  if (length(args) >= 4) {
    ergebnis <- aufgabe_klassifizieren(args[1], args[2], args[3], args[4])
    cat(toJSON(ergebnis, auto_unbox = TRUE))
  }
}
