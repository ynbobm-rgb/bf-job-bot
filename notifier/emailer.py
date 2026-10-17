from email.mime.text import MIMEText
import smtplib
import datetime
from config import *
from logging_config import log_securite

                # Mail avec signature

def mail(titre, lien, source, hash_code):
    try:
            body = f"""
                <div>
                    <h2>Alerte de ton Bot BF-JOB</h2>
                    <p>Salut, c'est ton bot. J'ai trouve une nouvelle offre correspondant a tes mots-cles.</p>
                    <h3>{titre}</h3>
                    <p>
                        <b>
                            Source detecter:
                        </b>
                        {source}
                    </p>
                    <p><b>Empreinte de securite:</b>{hash_code[:16]}...</p>
                    <p><a href='{lien}' style="background:#007bff; color:white; padding:10px 15px; text-decoration:none; border-radius: 5px">Voir l'offre</a></p>
                    <hr>
                    <small>Bot BF-Job * Scan auto tous les 15min * Burkina Faso - {datetime.datetime.now()}</small>
                </div>
            """
            msg = MIMEText(body, "html", "utf-8")
            msg["Subject"] = f"[Bot BF-JOB] {titre[:70]}"
            msg["From"] = f"Ton Bot BF-JOB <{EMAIL_FROM}>"
            msg["To"] = TO
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
                s.login(EMAIL_FROM, EMAIL_PASS)
                s.send_message(msg)
            print(f"Alerte: {titre}")
    except Exception as e:
            log_securite("Erreur-mail", str(e), hash_code)