import time
import requests
import datetime
import logging

from config import KEYWORDS, MAX_PAR_JOUR, QUERY_PAYS
from logging_config import log_securite
from notifier.emailer import mail
from notifier.telegram import telegram
from storage import get_compteur, inc_compteur
from utils import empreinte

def scan_github(seen: dict):
    """
    Parcourt l'API de GitHub pour trouver des projets/offres.
    """
    logging.info("Démarrage du scan GitHub...")
    
    if get_compteur() >= MAX_PAR_JOUR:
        return

    try:
        url = f"https://api.github.com/search/repositories?q={'+'.join(KEYWORDS)}+{QUERY_PAYS}&sort=updated"
        r = requests.get(url, timeout=10, headers={"User-Agent": "BF-JOB-BOT"}).json()
        
        for repo in r.get("items", [])[:10]:
            titre = repo["name"]
            lien = repo["html_url"]
            h = empreinte(titre, lien)
            
            if h in seen:
                continue
                
            seen[h] = {"titre": titre, "lien": lien, "date": str(datetime.datetime.now()), "source": "GitHub"}
            log_securite("VALIDE-GitHub", titre, h)
            mail(titre, lien, "GitHub", h)
            telegram(titre, lien, "GitHub", h)
            
            inc_compteur()
            if get_compteur() >= MAX_PAR_JOUR:
                log_securite("Limite-Jour", "Limite atteinte pendant GitHub", "N/A")
                return
                
            time.sleep(1)
            
    except Exception as e:
        log_securite("Erreur-Scan-GitHub", str(e), "N/A")