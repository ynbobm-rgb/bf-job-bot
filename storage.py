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
        if data.get("date") == datetime.datetime.now().strftime("%Y-%m-%d"):
            return data.get("count", 0)
        else:
            return 0 # Nouveau jour
    except:
        return 0

# Fonction pour incrementer le compteur
def inc_compteur():
    count = get_compteur() + 1
    json.dump({"date": datetime.datetime.now().strftime("%Y-%m-%d"), "count": count}, open(COMPTEUR_FILE, "w"))
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
            <p>Date: {datetime.datetime.now()}</p>
            <hr>
            <pre>{contenu[:5000]}... (tronqué)</pre>
            """
            # Envoi via ton mail_telegram existant mais avec un hash special
            mail(f"[MAINTENANCE] seen.json {taille_mo:.2f}Mo - Nettoyage", "https://render.com", f"Maintenance - {taille_mo:.2f}Mo", "MAINTENANCE")
            telegram(f"[MAINTENANCE] seen.json {taille_mo:.2f}Mo - Nettoyage", "https://render.com", f"Maintenance - {taille_mo:.2f}Mo", "MAINTENANCE")
            
            # 2. Sauvegarde backup local (optionnel)
            backup_name = f"seen_backup_{datetime.datetime.now().strftime('%Y%m%d')}.json"
            os.rename(SEEN, backup_name)
            
            # 3. Vide pour libérer
            seen_save({})
            log_securite("SEEN-VIDE", f"Fichier vide, backup: {backup_name}", "N/A")
            
    except Exception as e:
        log_securite("Erreur-Limit", str(e), "N/A")


def seen_load() -> dict:
    """
    Charge le fichier seen.json.
    Retourne un dictionnaire mapping fingerprint -> metadata (dict).
    Compatible avec deux formats historiques :
     - si le fichier contient une liste de fingerprints, on convertit en {fp: {}}
     - si le fichier contient déjà un dict, on le retourne tel quel
    """
    if not os.path.exists(SEEN):
        logging.info("Fichier seen.json introuvable. Création d'une nouvelle table.")
        return {}

    try:
        with open(SEEN, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict):
                return data
            if isinstance(data, list):
                # ancien format : liste de fingerprints -> on convertit en dict vide par clef
                return {fp: {} for fp in data}
            # format inattendu -> retourne vide
            return {}
    except Exception as e:
        logging.error(f"Erreur lors du chargement de {SEEN} : {e}")
        return {}


def seen_save(seen_dict: dict):
    """
    Sauvegarde le dictionnaire seen dans le fichier JSON.
    """
    try:
        with open(SEEN, "w", encoding="utf-8") as f:
            json.dump(seen_dict, f, ensure_ascii=False, indent=4)
        logging.debug("Fichier seen.json sauvegardé avec succès.")
    except Exception as e:
        logging.error(f"Erreur lors de la sauvegarde de {SEEN} : {e}")
