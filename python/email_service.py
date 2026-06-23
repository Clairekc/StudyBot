# ============================================================
#  StudyBot — python/email_service.py
#  Automatischer E-Mail-Versand nach Onboarding
#
#  GMAIL SETUP:
#  1. Gehe zu myaccount.google.com → Sicherheit
#  2. Aktiviere 2-Faktor-Authentifizierung
#  3. Suche "App-Passwörter" → erstelle eines für "StudyBot"
#  4. Trage das 16-stellige Passwort unten ein
# ============================================================

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# ── Konfiguration ─────────────────────────────────────────────
ABSENDER_EMAIL = "mendelkandjieu@gmail.com"
ABSENDER_PASSWORT = "qklp isfi dfma trvx"  # App-Passwort hier eintragen (16 Zeichen)
ADMIN_EMAIL = "mnch@hochschule-trier.de"


def _email_senden(empfaenger, betreff, inhalt_html):
    """Sendet eine HTML-Email über Gmail SMTP."""
    if not ABSENDER_PASSWORT:
        print(f"[Email] App-Passwort nicht konfiguriert. Email an {empfaenger} nicht gesendet.")
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = betreff
        msg["From"]    = f"StudyBot <{ABSENDER_EMAIL}>"
        msg["To"]      = empfaenger

        teil = MIMEText(inhalt_html, "html", "utf-8")
        msg.attach(teil)

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(ABSENDER_EMAIL, ABSENDER_PASSWORT)
            server.sendmail(ABSENDER_EMAIL, empfaenger, msg.as_string())

        print(f"[Email] ✓ Gesendet an {empfaenger}")
        return True

    except Exception as e:
        print(f"[Email] Fehler: {e}")
        return False


def bestaetigung_an_nutzer_senden(vorname, nachname, email, nutzer_id):
    """
    Sendet eine Willkommens-Email an den neuen Nutzer.
    Enthält KEIN Passwort — nur die Bestätigung der Registrierung.
    """
    betreff = "🤖 Willkommen bei StudyBot!"
    inhalt = f"""
    <div style="font-family:Arial,sans-serif; max-width:600px; margin:auto;">
        <div style="background:linear-gradient(135deg,#667eea,#764ba2);
                    padding:30px; border-radius:16px 16px 0 0; text-align:center;">
            <h1 style="color:white; margin:0;">🤖 StudyBot</h1>
            <p style="color:rgba(255,255,255,0.8); margin:8px 0 0;">
                Dein smarter Lern- und Aufgabenassistent
            </p>
        </div>
        <div style="background:white; padding:30px; border-radius:0 0 16px 16px;
                    box-shadow:0 4px 20px rgba(0,0,0,0.08);">
            <h2 style="color:#2E3A5C;">Hallo {vorname}! 👋</h2>
            <p style="color:#4A5A80; line-height:1.6;">
                Deine Registrierung bei StudyBot war erfolgreich!<br>
                Ab jetzt erinnert dich StudyBot automatisch an deine Aufgaben —
                zur richtigen Zeit, auf die richtige Art.
            </p>
            <div style="background:#F5F7FF; border-radius:12px; padding:20px; margin:20px 0;">
                <p style="margin:0; color:#6B7A99; font-size:13px;">DEIN KONTO</p>
                <p style="margin:6px 0; font-weight:600; color:#2E3A5C; font-size:16px;">
                    {vorname} {nachname}
                </p>
                <p style="margin:0; color:#9AA5BD; font-size:13px;">
                    Registriert am {datetime.now().strftime('%d.%m.%Y um %H:%M')} Uhr
                </p>
            </div>
            <div style="background:#FFF8E1; border-radius:12px; padding:16px; margin:20px 0;
                        border-left:4px solid #FFA94D;">
                <p style="margin:0; color:#D17A1A; font-size:13px;">
                    🔒 <strong>Sicherheitshinweis:</strong> Dein Passwort wird niemals
                    per E-Mail verschickt. Bewahre es sicher auf.
                </p>
            </div>
            <p style="color:#4A5A80; font-size:14px;">
                Beim nächsten Login: Gesichtserkennung + dein Passwort eingeben.
            </p>
            <p style="color:#9AA5BD; font-size:12px; margin-top:30px; text-align:center;">
                StudyBot — Dein persönlicher Lernassistent
            </p>
        </div>
    </div>
    """
    return _email_senden(email, betreff, inhalt)


def benachrichtigung_an_admin_senden(vorname, nachname, email):
    """
    Sendet eine kurze Benachrichtigung an den Admin.
    KEIN Passwort, nur Registrierungsinfo.
    """
    betreff = f"StudyBot: Neuer Nutzer — {vorname} {nachname}"
    inhalt = f"""
    <div style="font-family:Arial,sans-serif; max-width:500px; margin:auto;
                background:white; padding:24px; border-radius:12px;
                box-shadow:0 2px 12px rgba(0,0,0,0.08);">
        <h3 style="color:#2E3A5C; margin-top:0;">📋 Neuer Nutzer registriert</h3>
        <table style="width:100%; border-collapse:collapse;">
            <tr>
                <td style="color:#9AA5BD; padding:8px 0; font-size:13px;">Name</td>
                <td style="color:#2E3A5C; font-weight:600;">{vorname} {nachname}</td>
            </tr>
            <tr>
                <td style="color:#9AA5BD; padding:8px 0; font-size:13px;">E-Mail</td>
                <td style="color:#2E3A5C;">{email}</td>
            </tr>
            <tr>
                <td style="color:#9AA5BD; padding:8px 0; font-size:13px;">Registriert</td>
                <td style="color:#2E3A5C;">
                    {datetime.now().strftime('%d.%m.%Y um %H:%M')} Uhr
                </td>
            </tr>
        </table>
        <p style="color:#9AA5BD; font-size:11px; margin-top:20px;">
            Das Passwort des Nutzers wird aus Datenschutzgründen nicht übermittelt.
        </p>
    </div>
    """
    return _email_senden(ADMIN_EMAIL, betreff, inhalt)


def registrierungs_emails_senden(vorname, nachname, email, nutzer_id):
    """Sendet beide Emails nach erfolgreichem Onboarding."""
    ok1 = bestaetigung_an_nutzer_senden(vorname, nachname, email, nutzer_id)
    ok2 = benachrichtigung_an_admin_senden(vorname, nachname, email)
    return ok1, ok2
