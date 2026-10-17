import requests
from config import *
from logging_config import log_securite
from datetime import datetime
            # Telegram gestion 

def telegram( titre, lien, source, hash_code):
    # mail avec signature
   
    # telegram
    try:
        if TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
            text = f"*Bot BF-JOB*\n\n*{titre}*\n{lien}\n\nSource:{source}\nEmpreinte: `{hash_code[:20]}`\n Date d'envoie: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
            resp = requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "Markdown"}, timeout=10)
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
