# ============================================================
#  StudyBot — neural_network.R
#  Neuronales Netz für optimale Erinnerungszeit
#
#  ZIEL: Vorhersage der Aufmerksamkeit (0-1) zu jeder Tagesstunde,
#  basierend auf den Gewohnheiten aus dem Onboarding-Fragebogen.
#
#  ARCHITEKTUR: 4 Eingaben → [6] Hidden → 1 Ausgabe (Sigmoid)
#
#  AUFRUF AUS PYTHON:
#    Rscript neural_network.R <lernzeit_stunde> <schlaf_stunde> <aufgaben_anzahl>
# ============================================================

library(neuralnet)
library(jsonlite)

MODELL_PFAD <- "daten/models/neural_network.rds"

# ── Trainingsdaten generieren ────────────────────────────────
# Simuliert Aufmerksamkeitskurven für TAG- und NACHTMENSCHEN
# (manche Nutzer lernen abends, manche spät nachts, manche morgens)
nn_trainingsdaten <- function(n = 600) {
  set.seed(11)

  stunde              <- sample(6:23, n, replace = TRUE)
  # Breiter Bereich: deckt Morgenmenschen (15h) bis Nachtmenschen (23h) ab
  bevorzugte_lernzeit <- sample(15:23, n, replace = TRUE)
  # Schlafenszeit als Stunde 0-23 (z.B. 2 Uhr nachts = 2, nicht 26)
  schlaf_stunde       <- sample(c(21,22,23,0,1,2,3), n, replace = TRUE)
  aufgaben_anzahl     <- sample(1:8, n, replace = TRUE)

  # Zirkulärer Abstand zur Lernzeit (wichtig bei Nachtmenschen!)
  # Beispiel: Lernzeit=23, aktuelle Stunde=1 → Abstand soll 2 sein, nicht 22
  zirkulaerer_abstand <- function(a, b) {
    diff <- abs(a - b)
    pmin(diff, 24 - diff)
  }

  abstand_lernzeit <- zirkulaerer_abstand(stunde, bevorzugte_lernzeit)
  abstand_schlaf   <- zirkulaerer_abstand(stunde, schlaf_stunde)

  aufmerksamkeit <- 0.9 * exp(-0.5 * (abstand_lernzeit / 2.5)^2) -
                     0.3 * exp(-0.5 * (abstand_schlaf / 2)^2) +
                     aufgaben_anzahl * 0.01
  aufmerksamkeit <- aufmerksamkeit + rnorm(n, 0, 0.06)
  aufmerksamkeit <- pmin(pmax(aufmerksamkeit, 0), 1)

  # Schlafstunde in 0-23 Format normalisieren (0 statt 24)
  schlaf_stunde_norm <- schlaf_stunde %% 24

  data.frame(
    stunde_norm           = stunde / 23,
    lernzeit_norm         = bevorzugte_lernzeit / 23,
    schlaf_norm           = schlaf_stunde_norm / 23,
    aufgaben_norm         = aufgaben_anzahl / 8,
    aufmerksamkeit        = aufmerksamkeit
  )
}

# ── Modell trainieren ─────────────────────────────────────────
nn_trainieren <- function() {
  cat("[Neural Network] Trainiere Netzwerk (4 → 6 → 1)...\n")
  daten <- nn_trainingsdaten()

  set.seed(42)
  train_idx <- sample(1:nrow(daten), round(nrow(daten) * 0.8))
  train <- daten[train_idx, ]
  test  <- daten[-train_idx, ]

  modell <- neuralnet(
    aufmerksamkeit ~ stunde_norm + lernzeit_norm + schlaf_norm + aufgaben_norm,
    data          = train,
    hidden        = 6,
    linear.output = TRUE,
    threshold     = 0.05,   # schnelle Konvergenz für Demo (~20-30 Sek.)
    stepmax       = 1e5,
    act.fct       = "logistic"
  )

  pred <- as.numeric(predict(modell, test))
  rmse <- sqrt(mean((pred - test$aufmerksamkeit)^2))
  r2   <- cor(pred, test$aufmerksamkeit)^2
  cat(sprintf("[Neural Network] RMSE: %.4f | R²: %.3f\n", rmse, r2))

  if (!dir.exists("daten/models")) dir.create("daten/models", recursive = TRUE)
  saveRDS(list(modell = modell, r2 = r2), MODELL_PFAD)
  cat("[Neural Network] Modell gespeichert:", MODELL_PFAD, "\n")
  modell
}

# ── Modell laden ──────────────────────────────────────────────
nn_laden <- function() {
  if (file.exists(MODELL_PFAD)) return(readRDS(MODELL_PFAD)$modell)
  nn_trainieren()
}

# ── Optimale Erinnerungszeit berechnen ────────────────────────
optimale_zeit_berechnen <- function(bevorzugte_lernzeit, schlaf_stunde, aufgaben_anzahl) {
  modell <- nn_laden()

  # Schlafstunde auf 0-23 normalisieren (z.B. "2" bleibt 2, "26" würde zu "2")
  schlaf_stunde_norm <- as.numeric(schlaf_stunde) %% 24

  stunden <- 6:23
  scores <- sapply(stunden, function(h) {
    eingabe <- data.frame(
      stunde_norm   = h / 23,
      lernzeit_norm = as.numeric(bevorzugte_lernzeit) / 23,
      schlaf_norm   = schlaf_stunde_norm / 23,
      aufgaben_norm = as.numeric(aufgaben_anzahl) / 8
    )
    pred <- as.numeric(predict(modell, eingabe))
    min(max(pred, 0), 1)
  })

  beste_idx <- which.max(scores)
  beste_stunde <- stunden[beste_idx]

  list(
    beste_stunde = as.integer(beste_stunde),
    beste_uhrzeit = sprintf("%02d:00", beste_stunde),
    score = round(scores[beste_idx], 3),
    alle_stunden = stunden,
    alle_scores  = round(scores, 3)
  )
}

# ── Kommandozeilen-Schnittstelle ──────────────────────────────
if (!interactive()) {
  args <- commandArgs(trailingOnly = TRUE)
  if (length(args) >= 3) {
    ergebnis <- optimale_zeit_berechnen(args[1], args[2], args[3])
    cat(toJSON(ergebnis, auto_unbox = TRUE))
  }
}
