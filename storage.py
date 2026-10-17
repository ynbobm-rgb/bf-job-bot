from config import *
import json, datetime, logging
from notifier.emailer import mail
from notifier.telegram import telegram
from logging_config import log_securite
import json
import os

# Fonction pour obtenir le compteur
def get_compteur():
    try:
        data = json.load(open(COMPTEUR_FILE))
        if data.get("date") == datetime.now().strftime("%Y-%m-%d"):
            return data.get("count", 0)
        else:
            return 0 # Nouveau jour
    except:
        return 0

# Fonction pour incrementer le compteur
def inc_compteur():
    count = get_compteur() + 1
    json.dump({"date": datetime.now().strftime("%Y-%m-%d"), "count": count}, open(COMPTEUR_FILE, "w"))
    return count


def limit():
    try:
        if not os.path.exists(SEEN):
            return
        
        taille_mo = os.path.getsize(SEEN) / (1024*1024)
        
        if taille_mo >= LIMITE_TAILLE_MO:
            log_securite("SEEN-TROP-GROS", f"{taille_mo:.2f} Mo - envoi et nettoyage", "N/A")
            
            # 1. Copie et envoie par mail
            with open(SEEN, "r", encoding="utf-8") as f:
                contenu = f.read()
            
            # On envoie en piece jointe / corps
            body = f"""<h2>Bot BF-JOB - Fichier seen.json trop gros</h2>
            <p>Taille: {taille_mo:.2f} Mo (limite {LIMITE_TAILLE_MO} Mo)</p>
            <p>Je vide le fichier pour libérer l'espace sur Render.</p>
            <p>Date: {datetime.now()}</p>
            <hr>
            <pre>{contenu[:5000]}... (tronqué)</pre>
            """
            # Envoi via ton mail_telegram existant mais avec un hash special
            mail(f"[MAINTENANCE] seen.json {taille_mo:.2f}Mo - Nettoyage", "https://render.com", f"Maintenance - {taille_mo:.2f}Mo", "MAINTENANCE")
            telegram(f"[MAINTENANCE] seen.json {taille_mo:.2f}Mo - Nettoyage", "https://render.com", f"Maintenance - {taille_mo:.2f}Mo", "MAINTENANCE")
            
            # 2. Sauvegarde backup local (optionnel)
            backup_name = f"seen_backup_{datetime.now().strftime('%Y%m%d')}.json"
            os.rename(SEEN, backup_name)
            
            # 3. Vide pour libérer
            seen_save({})
            log_securite("SEEN-VIDE", f"Fichier vide, backup: {backup_name}", "N/A")
            
    except Exception as e:
        log_securite("Erreur-Limit", str(e), "N/A")


def seen_load() -> set:
    """
    Charge la liste des offres déjà vues depuis le fichier JSON.
    Retourne un set (ensemble) pour optimiser la rapidité de recherche, 
    ou un set vide s'il y a une erreur ou si le fichier n'existe pas.
    """
    if not os.path.exists(SEEN):
        logging.info("Fichier seen.json introuvable. Création d'une nouvelle liste.")
        return set()
    
    try:
        with open(SEEN, "r", encoding="utf-8") as f:
            data = json.load(f)
            # On s'assure qu'on retourne bien un ensemble (set)
            return set(data) if isinstance(data, list) else set()
    except Exception as e:
        logging.error(f"Erreur lors du chargement de {SEEN} : {e}")
        return set()

def seen_save(seen_set: set):
    """
    Sauvegarde l'ensemble des offres vues dans le fichier JSON 
    en le convertissant proprement en liste.
    """
    try:
        with open(SEEN, "w", encoding="utf-8") as f:
            # Le format JSON ne comprend pas les 'set', on les convertit donc en 'list'
            json.dump(list(seen_set), f, ensure_ascii=False, indent=4)
        logging.debug("Fichier seen.json sauvegardé avec succès.")
    except Exception as e:
        logging.error(f"Erreur lors de la sauvegarde de {SEEN} : {e}")