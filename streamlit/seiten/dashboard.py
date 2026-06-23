# ============================================================
#  StudyBot — seiten/dashboard.py
#  Dashboard: Schön, modern, für Jugendliche
#  Tabs: Übersicht | Neue Aufgabe | Alle Aufgaben
# ============================================================

import streamlit as st
import sys, os, json
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit.components.v1 as components
from datetime import datetime, date, timedelta

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(BASE_DIR, "python"))
sys.path.insert(0, BASE_DIR)

from bridge_r import vollstaendige_analyse
import arduino_control
from scheduler import erinnerungen_planen, log_lesen
from audio_service import nachricht_generieren, audio_javascript, alarm_javascript

TASKS_DIR   = os.path.join(BASE_DIR, "daten", "tasks")
PROFILE_DIR = os.path.join(BASE_DIR, "daten", "profile")
ALARM_DATEI = os.path.join(BASE_DIR, "daten", "audio_alarm.json")
os.makedirs(TASKS_DIR, exist_ok=True)


def _audio_alarm_pruefen():
    """
    Prüft ob ein neuer Audio-Alarm vorliegt und spielt ihn ab.
    Wird bei jedem Dashboard-Refresh aufgerufen.
    """
    if not os.path.exists(ALARM_DATEI):
        return
    try:
        with open(ALARM_DATEI, "r", encoding="utf-8") as f:
            alarm = json.load(f)
        if alarm.get("abgespielt"):
            return
        titel = alarm["titel"]
        prioritaet = alarm["prioritaet"]
        erinnerungs_zeit = alarm["erinnerungs_zeit"]
        deadline_zeit = alarm.get("deadline_zeit")

        # Nachricht generieren
        nachricht = nachricht_generieren(titel, prioritaet, erinnerungs_zeit, deadline_zeit)

        # Alarm-Ton + Sprachnachricht im Browser abspielen
        components.html(alarm_javascript(prioritaet), height=0)
        components.html(audio_javascript(nachricht), height=0)

        # Als abgespielt markieren
        alarm["abgespielt"] = True
        with open(ALARM_DATEI, "w", encoding="utf-8") as f:
            json.dump(alarm, f, ensure_ascii=False, indent=2)

        st.toast(f"🔔 {nachricht}", icon="🔊")

    except Exception as e:
        pass  # Kein Alarm oder Fehler — still ignorieren

LERNZEIT_MAPPING = {
    "Morgens (6–10 Uhr)": 8, "Mittags (10–14 Uhr)": 12,
    "Nachmittags (14–18 Uhr)": 16, "Abends (18–22 Uhr)": 20,
    "Nachts (nach 22 Uhr)": 23,
}
SCHLAF_MAPPING = {
    "Vor 21 Uhr": 21, "21 – 22 Uhr": 21, "22 – 23 Uhr": 22,
    "23 – 0 Uhr": 23, "Nach 0 Uhr": 1,
}
PRIO_FARBEN = {
    "kritisch": "#FF6B6B", "hoch": "#FFA94D",
    "mittel": "#69DB7C",   "niedrig": "#74C0FC"
}
PRIO_BADGE = {
    "kritisch": ("badge-kritisch", "🔴 Kritisch"),
    "hoch":     ("badge-hoch",     "🟠 Hoch"),
    "mittel":   ("badge-mittel",   "🟢 Mittel"),
    "niedrig":  ("badge-niedrig",  "🔵 Niedrig"),
}
LOCKERE_CLUSTER = {"leicht_locker"}


def _nutzer_id_kandidaten(nutzer_id):
    """Gibt mögliche IDs zurück — mit und ohne Timestamp."""
    kandidaten = [nutzer_id]
    teile = nutzer_id.split("_")
    if len(teile) >= 3 and len(teile[-1]) == 6 and teile[-1].isdigit():
        kandidaten.append("_".join(teile[:-1]))
    return kandidaten


def _aufgaben_laden(nutzer_id):
    for nid in _nutzer_id_kandidaten(nutzer_id):
        pfad = os.path.join(TASKS_DIR, f"{nid}_tasks.json")
        if os.path.exists(pfad):
            with open(pfad, "r", encoding="utf-8") as f:
                return json.load(f)
    return []


def _aufgabe_speichern(nutzer_id, eintrag):
    # Speichert immer mit dem stabilen ID (ohne Timestamp)
    nid = _nutzer_id_kandidaten(nutzer_id)[-1]
    pfad = os.path.join(TASKS_DIR, f"{nid}_tasks.json")
    alle = _aufgaben_laden(nutzer_id)
    alle.append(eintrag)
    with open(pfad, "w", encoding="utf-8") as f:
        json.dump(alle, f, ensure_ascii=False, indent=2)


def _erinnerungen_laden(nutzer_id):
    for nid in _nutzer_id_kandidaten(nutzer_id):
        pfad = os.path.join(TASKS_DIR, f"{nid}_erinnerungen.json")
        if os.path.exists(pfad):
            with open(pfad, "r", encoding="utf-8") as f:
                return json.load(f).get("erinnerungen", [])
    return []


def _zeit_anpassen(ergebnis, bevorzugte_lernzeit):
    if ergebnis["cluster"]["cluster_name"] not in LOCKERE_CLUSTER:
        return ergebnis
    vorschlag = max(12, min(bevorzugte_lernzeit - 3, 19))
    ergebnis["optimale_zeit"]["beste_stunde"] = vorschlag
    ergebnis["optimale_zeit"]["beste_uhrzeit"] = f"{vorschlag:02d}:00"
    return ergebnis


# ══════════════════════════════════════════════════════════════
#  TAB 1 — ÜBERSICHT & VISUALISIERUNGEN
# ══════════════════════════════════════════════════════════════
def _tab_uebersicht(profil):
    # Audio-Alarm prüfen und abspielen
    _audio_alarm_pruefen()

    # Auto-refresh toutes les 30 secondes sans clignotement
    try:
        from streamlit_autorefresh import st_autorefresh
        st_autorefresh(interval=30000, key="dashboard_refresh")
    except ImportError:
        pass  # Si pas installé, on garde le bouton manuel

    col_refresh, _ = st.columns([1, 4])
    with col_refresh:
        if st.button("🔄 Jetzt aktualisieren", use_container_width=True):
            st.rerun()

    aufgaben     = _aufgaben_laden(profil["nutzer_id"])
    erinnerungen = _erinnerungen_laden(profil["nutzer_id"])

    # ── Metriken ────────────────────────────────────────────────
    ausstehend = sum(1 for e in erinnerungen if not e.get("gesendet"))
    gesendet   = sum(1 for e in erinnerungen if e.get("gesendet"))

    c1, c2, c3, c4 = st.columns(4)
    for col, val, label, color in [
        (c1, len(aufgaben), "Aufgaben", "#74C0FC"),
        (c2, sum(1 for a in aufgaben if a.get("ergebnis",{}).get("prioritaet",{}).get("prioritaet")=="kritisch"), "Kritisch", "#FF6B6B"),
        (c3, ausstehend, "Geplante Alarme", "#FFA94D"),
        (c4, gesendet, "Gesendete Alarme", "#69DB7C"),
    ]:
        col.markdown(f"""
        <div style="background:white;border-radius:16px;padding:18px;text-align:center;
                    box-shadow:0 2px 12px rgba(0,0,0,0.06);border-left:4px solid {color};">
            <p style="font-size:32px;font-weight:800;color:{color};margin:0;">{val}</p>
            <p style="font-size:12px;color:#9AA5BD;margin:0;font-weight:500;">{label}</p>
        </div>""", unsafe_allow_html=True)

    if not aufgaben:
        st.markdown("<br>", unsafe_allow_html=True)
        st.info("🎯 Noch keine Aufgaben! Geh zu '➕ Neue Aufgabe' und leg los.")
        return

    df = pd.DataFrame([{
        "Titel": a["titel"],
        "Priorität": a.get("ergebnis",{}).get("prioritaet",{}).get("prioritaet","?"),
        "Konfidenz %": a.get("ergebnis",{}).get("prioritaet",{}).get("konfidenz", 0),
        "Cluster": a.get("ergebnis",{}).get("cluster",{}).get("cluster_name","?").replace("_"," ").title(),
        "Beste Zeit": a.get("ergebnis",{}).get("optimale_zeit",{}).get("beste_uhrzeit","?"),
        "Fällig": a.get("faellig","?"),
        "Typ": a.get("typ","?"),
    } for a in aufgaben])

    st.markdown("<br>", unsafe_allow_html=True)
    col_l, col_r = st.columns(2)

    with col_l:
        # ── Donut: Prioritätsverteilung (Naive Bayes) ──────────
        st.markdown("#### 🟡 Naive Bayes — Prioritätsverteilung")
        prio_counts = df["Priorität"].value_counts()
        fig_donut = go.Figure(go.Pie(
            labels=prio_counts.index,
            values=prio_counts.values,
            hole=0.55,
            marker_colors=[PRIO_FARBEN.get(p, "#ccc") for p in prio_counts.index],
            textinfo="label+percent",
            hovertemplate="%{label}: %{value} Aufgaben<extra></extra>"
        ))
        fig_donut.update_layout(
            showlegend=False, margin=dict(t=10,b=10,l=10,r=10),
            height=260, paper_bgcolor="rgba(0,0,0,0)",
            annotations=[dict(text=f"{len(df)}<br>Aufgaben", x=0.5, y=0.5,
                            font_size=16, showarrow=False)]
        )
        st.plotly_chart(fig_donut, use_container_width=True)

        # ── Balken: Cluster-Verteilung (k-Means) ───────────────
        st.markdown("#### 🔵 k-Means — Aufgabentypen")
        cluster_counts = df["Cluster"].value_counts().reset_index()
        cluster_counts.columns = ["Cluster", "Anzahl"]
        fig_bar = px.bar(
            cluster_counts, x="Cluster", y="Anzahl",
            color="Cluster",
            color_discrete_sequence=["#74C0FC","#B197FC","#FFA94D","#69DB7C"],
            text="Anzahl"
        )
        fig_bar.update_layout(
            showlegend=False, margin=dict(t=10,b=10,l=10,r=10),
            height=260, paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor="#F0F0F0")
        )
        fig_bar.update_traces(textposition="outside")
        st.plotly_chart(fig_bar, use_container_width=True)

    with col_r:
        # ── Linie: Aufmerksamkeitskurve (Neural Network) ────────
        st.markdown("#### 🧠 Neuronales Netz — Dein Aufmerksamkeitsprofil")
        fragebogen = profil.get("fragebogen", {})
        bevorzugte_lernzeit = LERNZEIT_MAPPING.get(fragebogen.get("lernzeit","Abends (18–22 Uhr)"), 18)
        schlaf_stunde = SCHLAF_MAPPING.get(fragebogen.get("schlafen","22 – 23 Uhr"), 22)
        try:
            from bridge_r import optimale_zeit_berechnen
            nn = optimale_zeit_berechnen(bevorzugte_lernzeit, schlaf_stunde, 3)
            stunden = [f"{h}:00" for h in nn["alle_stunden"]]
            scores  = [round(s*100,1) for s in nn["alle_scores"]]
            fig_line = go.Figure()
            fig_line.add_trace(go.Scatter(
                x=stunden, y=scores, mode="lines+markers",
                fill="tozeroy", fillcolor="rgba(116,192,252,0.15)",
                line=dict(color="#74C0FC", width=3),
                marker=dict(size=6, color="#4A90D9"),
                hovertemplate="%{x}: %{y}%<extra></extra>"
            ))
            beste = nn["beste_uhrzeit"]
            fig_line.update_layout(
                margin=dict(t=10,b=10,l=10,r=10), height=260,
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(showgrid=False, tickangle=-45),
                yaxis=dict(showgrid=True, gridcolor="#F0F0F0",
                           title="Aufmerksamkeit %", range=[0,110])
            )
            st.plotly_chart(fig_line, use_container_width=True)
            st.caption(f"⭐ Beste Zeit: **{beste}** ({int(nn['score']*100)}% Aufmerksamkeit)")
        except Exception as e:
            st.caption(f"Kurve nicht verfügbar: {e}")

        # ── Radar: Aufgaben nach Typ ────────────────────────────
        st.markdown("#### 📊 Aufgabentypen — Radardiagramm")
        alle_typen = ["hausaufgabe", "test", "projekt", "erinnerung"]
        typ_counts = df["Typ"].value_counts().reindex(alle_typen, fill_value=0)
        fig_radar = go.Figure(go.Scatterpolar(
            r=list(typ_counts.values) + [typ_counts.values[0]],
            theta=alle_typen + [alle_typen[0]],
            fill="toself",
            fillcolor="rgba(177,151,252,0.25)",
            line_color="#B197FC",
            name="Aufgaben"
        ))
        fig_radar.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, max(typ_counts.max(),1)+1])),
            showlegend=False, margin=dict(t=20,b=20,l=20,r=20),
            height=260, paper_bgcolor="rgba(0,0,0,0)"
        )
        st.plotly_chart(fig_radar, use_container_width=True)

    # ── Timeline: Nächste Erinnerungen ─────────────────────────
    st.markdown("---")
    st.markdown("#### 📅 Nächste geplante Erinnerungen")
    kommende = sorted(
        [e for e in erinnerungen if not e.get("gesendet") and
         datetime.fromisoformat(e["zeit"]) > datetime.now()],
        key=lambda e: e["zeit"]
    )[:6]

    if kommende:
        cols = st.columns(min(len(kommende), 3))
        for i, e in enumerate(kommende):
            ziel = datetime.fromisoformat(e["zeit"])
            diff = ziel - datetime.now()
            if diff.days > 0:
                diff_txt = f"in {diff.days} Tag{'en' if diff.days>1 else ''}"
            else:
                h = diff.seconds // 3600
                diff_txt = f"in {h}h" if h > 0 else "bald"
            farbe = PRIO_FARBEN.get(e["prioritaet"], "#ccc")
            cols[i % 3].markdown(f"""
            <div style="background:white;border-radius:14px;padding:14px;
                        border-left:4px solid {farbe};
                        box-shadow:0 2px 10px rgba(0,0,0,0.06);margin-bottom:10px;">
                <p style="font-size:11px;color:#9AA5BD;margin:0;">{diff_txt}</p>
                <p style="font-weight:700;color:#2E3A5C;margin:4px 0;font-size:13px;">
                    {e['titel'][:30]}</p>
                <p style="font-size:12px;color:{farbe};margin:0;font-weight:600;">
                    {ziel.strftime('%d.%m. %H:%M')} Uhr</p>
            </div>""", unsafe_allow_html=True)
    else:
        st.info("Keine anstehenden Erinnerungen.")

    # ── Schöne Tabelle: Alle Aufgaben ───────────────────────────
    st.markdown("---")
    st.markdown("#### 📋 Alle Aufgaben im Überblick")

    df_anzeige = df.copy()
    df_anzeige["Priorität"] = df_anzeige["Priorität"].map({
        "kritisch": "🔴 Kritisch", "hoch": "🟠 Hoch",
        "mittel": "🟢 Mittel", "niedrig": "🔵 Niedrig"
    }).fillna(df_anzeige["Priorität"])

    st.dataframe(
        df_anzeige,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Titel": st.column_config.TextColumn("📝 Aufgabe", width="large"),
            "Priorität": st.column_config.TextColumn("⚡ Priorität"),
            "Konfidenz %": st.column_config.ProgressColumn(
                "🎯 Konfidenz", min_value=0, max_value=100, format="%.0f%%"
            ),
            "Cluster": st.column_config.TextColumn("🔵 Cluster"),
            "Beste Zeit": st.column_config.TextColumn("🕐 Beste Zeit"),
            "Fällig": st.column_config.TextColumn("📅 Deadline"),
            "Typ": st.column_config.TextColumn("📂 Typ"),
        }
    )

    # ── Scheduler Log ───────────────────────────────────────────
    st.markdown("---")
    with st.expander("📋 Scheduler-Aktivitäten"):
        log = log_lesen(8)
        if log:
            for e in log:
                icon = {"signal":"⚡","fehler":"❌","planung":"📅",
                        "system":"⚙️","anwesenheit":"👁️"}.get(e["typ"], "ℹ️")
                st.markdown(
                    f"`{e['zeit'][:16]}` {icon} {e['nachricht']}"
                )
        else:
            st.caption("Noch keine Aktivitäten.")


# ══════════════════════════════════════════════════════════════
#  TAB 2 — NEUE AUFGABE
# ══════════════════════════════════════════════════════════════
def _tab_neue_aufgabe(profil):
    st.markdown("""
    <div class="sb-card" style="background:linear-gradient(135deg,#EEF4FF,#F3E8FF);">
        <p style="margin:0;color:#4A5A80;font-size:15px;">
            💡 Gib deine Aufgabe ein — StudyBot plant alles automatisch.
        </p>
    </div>
    """, unsafe_allow_html=True)

    fragebogen = profil.get("fragebogen", {})
    bevorzugte_lernzeit = LERNZEIT_MAPPING.get(fragebogen.get("lernzeit","Abends (18–22 Uhr)"), 18)
    schlaf_stunde = SCHLAF_MAPPING.get(fragebogen.get("schlafen","22 – 23 Uhr"), 22)

    with st.form("aufgabe_formular"):
        titel = st.text_input("📝 Was steht an?", placeholder="z.B. Mathe-Prüfung vorbereiten")

        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            faellig = st.date_input("📅 Fällig am", min_value=date.today(),
                                    value=date.today() + timedelta(days=7))
        with col2:
            from datetime import time as time_type
            faellig_zeit = st.time_input(
                "🕐 Uhrzeit Deadline",
                value=time_type(14, 0)
            )
            faellig_stunde = faellig_zeit.hour
            faellig_minute = faellig_zeit.minute
        with col3:
            typ = st.selectbox("📂 Typ", ["hausaufgabe","test","projekt","erinnerung"])

        col4, col5 = st.columns(2)
        with col4:
            geschaetzt_min = st.selectbox(
                "⏱️ Geschätzte Dauer",
                [15,30,45,60,90,120,180],
                format_func=lambda x: f"{x} Minuten"
            )
        with col5:
            schwierigkeit = st.select_slider(
                "💪 Schwierigkeit", options=[1,2,3], value=2,
                format_func=lambda x: ["Leicht 😊","Mittel 🤔","Schwer 😤"][x-1]
            )

        abgeschickt = st.form_submit_button(
            "✅ Aufgabe einreichen & Erinnerungen planen",
            type="primary", use_container_width=True
        )

    if abgeschickt and titel.strip():
        tage_bis_faellig = (faellig - date.today()).days
        from datetime import datetime as dt2
        deadline_exacte = dt2(faellig.year, faellig.month, faellig.day, faellig_stunde, faellig_minute)
        if deadline_exacte <= dt2.now():
            st.error('Diese Deadline liegt bereits in der Vergangenheit!')
            st.stop()

        with st.spinner("🤖 StudyBot analysiert... (k-Means → Naive Bayes → Neural Net)"):
            try:
                ergebnis = vollstaendige_analyse(
                    tage_bis_faellig=max(tage_bis_faellig, 0),
                    geschaetzt_min=geschaetzt_min,
                    schwierigkeit=schwierigkeit,
                    typ=typ,
                    bevorzugte_lernzeit=bevorzugte_lernzeit,
                    schlaf_stunde=schlaf_stunde,
                    aufgaben_anzahl=len(_aufgaben_laden(profil["nutzer_id"])) + 1
                )
                ergebnis = _zeit_anpassen(ergebnis, bevorzugte_lernzeit)
            except Exception as e:
                st.error(f"Analysefehler: {e}")
                st.stop()

        prioritaet      = ergebnis["prioritaet"]["prioritaet"]
        optimale_stunde = ergebnis["optimale_zeit"]["beste_stunde"]

        if tage_bis_faellig == 0:
            optimale_stunde = max(7, min(optimale_stunde, faellig_stunde - 1))

        geplante = erinnerungen_planen(
            nutzer_id=profil["nutzer_id"],
            aufgabe_titel=titel,
            faellig_datum=faellig,
            prioritaet=prioritaet,
            optimale_stunde=optimale_stunde,
            faellig_stunde=faellig_stunde,
            faellig_minute=faellig_minute
        )
        _aufgabe_speichern(profil["nutzer_id"], {
            "titel": titel, "faellig": str(faellig),
            "faellig_stunde": faellig_stunde, "typ": typ,
            "geschaetzt_min": geschaetzt_min, "schwierigkeit": schwierigkeit,
            "nutzer_id": profil["nutzer_id"], "ergebnis": ergebnis,
            "erstellt_am": str(datetime.now())
        })

        st.success(f"✓ '{titel}' erfasst! {len(geplante)} Erinnerungen geplant.")

        badge_kl, badge_txt = PRIO_BADGE.get(prioritaet, ("badge-mittel", prioritaet))
        c1, c2, c3 = st.columns(3)
        c1.markdown(f"""
        <div class="sb-card" style="text-align:center;">
            <p style="font-size:11px;color:#9AA5BD;margin:0;">CLUSTER (k-Means)</p>
            <p style="font-weight:700;color:#2E3A5C;margin:6px 0;">
                {ergebnis['cluster']['cluster_name'].replace('_',' ').title()}</p>
        </div>""", unsafe_allow_html=True)
        c2.markdown(f"""
        <div class="sb-card" style="text-align:center;">
            <p style="font-size:11px;color:#9AA5BD;margin:0;">PRIORITÄT (Naive Bayes)</p>
            <p style="margin:6px 0;"><span class="{badge_kl}">{badge_txt}</span></p>
            <p style="font-size:11px;color:#9AA5BD;margin:0;">{ergebnis['prioritaet']['konfidenz']}% Konfidenz</p>
        </div>""", unsafe_allow_html=True)
        c3.markdown(f"""
        <div class="sb-card" style="text-align:center;">
            <p style="font-size:11px;color:#9AA5BD;margin:0;">OPTIMALE ZEIT (Neural Net)</p>
            <p style="font-weight:700;color:#2E3A5C;margin:6px 0;">
                🕐 {ergebnis['optimale_zeit']['beste_uhrzeit']}</p>
        </div>""", unsafe_allow_html=True)

        if geplante:
            st.markdown("**📅 Geplante Erinnerungen:**")
            for e in geplante[:5]:
                ziel = datetime.fromisoformat(e["zeit"])
                farbe = PRIO_FARBEN.get(e["prioritaet"], "#ccc")
                st.markdown(f"""
                <div style="background:white;border-radius:12px;padding:10px 16px;
                            border-left:3px solid {farbe};margin-bottom:6px;
                            box-shadow:0 1px 6px rgba(0,0,0,0.05);">
                    <span style="color:{farbe};font-weight:600;font-size:12px;">
                        {ziel.strftime('%A, %d.%m.%Y')} um {ziel.strftime('%H:%M')} Uhr
                    </span>
                    <span style="float:right;color:#9AA5BD;font-size:11px;">
                        → automatisch per Arduino
                    </span>
                </div>""", unsafe_allow_html=True)
            if len(geplante) > 5:
                st.caption(f"... und {len(geplante)-5} weitere Erinnerungen.")


# ══════════════════════════════════════════════════════════════
#  TAB 3 — NUTZER ÜBERSICHT
# ══════════════════════════════════════════════════════════════
def _tab_nutzer():
    profil_aktuell = st.session_state.get("profil", {})
    nutzer_id_aktuell = profil_aktuell.get("nutzer_id", "")

    st.markdown("#### 👥 StudyBot Community")

    if not os.path.exists(PROFILE_DIR):
        st.info("Noch keine Nutzer registriert.")
        return

    profile_dateien = [f for f in os.listdir(PROFILE_DIR) if f.endswith(".json")]

    if not profile_dateien:
        st.info("Noch keine Nutzer registriert.")
        return

    # Große Metrik oben
    st.markdown(f"""
    <div style="background:linear-gradient(135deg,#667eea,#764ba2);
                border-radius:20px;padding:28px;text-align:center;margin-bottom:20px;">
        <p style="font-size:56px;font-weight:800;color:white;margin:0;">{len(profile_dateien)}</p>
        <p style="font-size:16px;color:rgba(255,255,255,0.8);margin:4px 0;">
            registrierte Nutzer
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Eigene Daten vollständig anzeigen
    st.markdown("**Dein Konto:**")
    st.markdown(f"""
    <div class="sb-card" style="border-left:4px solid #74C0FC;">
        <p style="font-weight:700;color:#2E3A5C;margin:0;font-size:16px;">
            {profil_aktuell.get('vorname','')} {profil_aktuell.get('nachname','')}
        </p>
        <p style="color:#9AA5BD;font-size:13px;margin:4px 0;">
            {profil_aktuell.get('email','')}
        </p>
        <p style="color:#9AA5BD;font-size:12px;margin:0;">
            Dabei seit {profil_aktuell.get('erstellt_am','')[:10]}
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Andere Nutzer — nur Vornamen
    andere = []
    for datei in profile_dateien:
        try:
            with open(os.path.join(PROFILE_DIR, datei), encoding="utf-8") as f:
                p = json.load(f)
            nid = p.get("nutzer_id", "")
            if nid != nutzer_id_aktuell and not nutzer_id_aktuell.startswith(nid) and not nid.startswith(nutzer_id_aktuell.rsplit("_",1)[0] if "_" in nutzer_id_aktuell else nutzer_id_aktuell):
                andere.append(p.get("vorname", "Unbekannt"))
        except Exception:
            continue

    if andere:
        st.markdown("<br>**Auch dabei:**", unsafe_allow_html=True)
        cols = st.columns(min(len(andere), 4))
        for i, name in enumerate(andere):
            cols[i % 4].markdown(f"""
            <div style="background:white;border-radius:12px;padding:14px;
                        text-align:center;box-shadow:0 2px 8px rgba(0,0,0,0.06);">
                <p style="font-size:24px;margin:0;">👤</p>
                <p style="font-weight:600;color:#2E3A5C;margin:4px 0;font-size:14px;">{name}</p>
            </div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════
#  HAUPTFUNKTION
# ══════════════════════════════════════════════════════════════
def zeige():
    if "profil" not in st.session_state:
        st.warning("Bitte melde dich zuerst an.")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔐 Zur Anmeldung", use_container_width=True, type="primary"):
                st.session_state.seite = "login"
                st.rerun()
        with col2:
            if st.button("🏠 Zur Startseite", use_container_width=True):
                st.session_state.seite = "start"
                st.rerun()
        return

    profil  = st.session_state.profil
    vorname = profil.get("vorname", "")

    # ── Begrüßungsband ────────────────────────────────────────
    stunde = datetime.now().hour
    if stunde < 12:   emoji, gruss = "☀️", "Guten Morgen"
    elif stunde < 18: emoji, gruss = "🌤️", "Guten Tag"
    elif stunde < 22: emoji, gruss = "🌙", "Guten Abend"
    else:             emoji, gruss = "⭐", "Gute Nacht"

    st.markdown(f"""
    <div style="background:linear-gradient(135deg,#667eea,#764ba2);
                border-radius:20px;padding:20px 28px;margin-bottom:20px;
                display:flex;align-items:center;justify-content:space-between;">
        <div>
            <p style="color:rgba(255,255,255,0.8);font-size:13px;margin:0;">
                {emoji} {gruss}</p>
            <p style="color:white;font-size:22px;font-weight:700;margin:4px 0;">
                {vorname} 👋</p>
            <p style="color:rgba(255,255,255,0.7);font-size:12px;margin:0;">
                Der Scheduler läuft im Hintergrund — du wirst automatisch erinnert.</p>
        </div>
        <div style="text-align:right;">
            <p style="color:white;font-size:28px;margin:0;">🤖</p>
            <p style="color:rgba(255,255,255,0.7);font-size:11px;margin:0;">StudyBot aktiv</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Tabs ──────────────────────────────────────────────────
    tab1, tab2, tab3 = st.tabs(["📊 Mein Dashboard", "➕ Neue Aufgabe", "👥 Nutzer"])

    with tab1:
        _tab_uebersicht(profil)

    with tab2:
        _tab_neue_aufgabe(profil)

    with tab3:
        _tab_nutzer()

    # ── Navigation unten ─────────────────────────────────────
    st.markdown("---")
    col_a, col_b, col_c = st.columns([2, 1, 1])
    with col_b:
        if st.button("🏠 Startseite", use_container_width=True):
            for key in ["profil","aktueller_nutzer"]:
                st.session_state.pop(key, None)
            st.session_state.seite = "start"
            st.rerun()
    with col_c:
        if st.button("🚪 Abmelden", use_container_width=True):
            for key in ["profil","aktueller_nutzer"]:
                st.session_state.pop(key, None)
            st.session_state.seite = "start"
            st.rerun()
