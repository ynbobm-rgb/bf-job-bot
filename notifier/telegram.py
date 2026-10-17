import requests
from config import *
from logging_config import log_securite
import datetime, html
            # Telegram gestion 

def telegram( titre, lien, source, hash_code):
    # mail avec signature
   
    # telegram
    try:
        if TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
            # text = f"*Bot BF-JOB*\n\n*{titre}*\n{lien}\n\nSource:{source}\nEmpreinte: `{hash_code[:20]}`\n Date d'envoie: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            text = (
                f"<b>Bot BF-JOB</b>\n\n"
                f"<b>{html.escape(titre)}</b>\n"
                f'<a href="{html.escape(lien, quote=True)}">Voir l’annonce</a>\n\n'
                f"Source : {html.escape(source)}\n"
                f"Empreinte : <code>{html.escape(hash_code[:20])}</code>\n"
                f"Date d’envoi : {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
            resp = requests.post(
                url,
                json={
                    "chat_id": TELEGRAM_CHAT_ID,
                    "text": text,
                    "parse_mode": "HTML",
                    "reply_markup": {
                        "inline_keyboard": [[
                            {
                                "text": "🔎 Vérifier l’authenticité",
                                "callback_data": f"verify:{hash_code}"
                            }
                        ]]
                    },
                },
                timeout=10,
            )
            # Vérifier réponse HTTP / JSON et logger en cas d'erreur
            try:
                data = resp.json()
            except Exception:
                log_securite("Erreur-telegram", f"Statut:{resp.status_code} Corps:{resp.text}", hash_code)
            else:
                if resp.status_code != 200 or not data.get("ok"):
                    log_securite("Erreur-telegram", f"Statut:{resp.status_code} Reponse:{data}", hash_code)
                else:
                    print(f"Telegram envoyé: {titre}")
    except Exception as e:
        log_securite("Erreur-telegram-exception", str(e), hash_code)
