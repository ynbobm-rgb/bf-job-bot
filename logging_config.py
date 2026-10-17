import logging
import os
from logging.handlers import RotatingFileHandler

def setup_logging():
    """
    Configure le système de logs pour :
    1. Créer le dossier 'logs' s'il n'existe pas.
    2. Afficher les logs dans le terminal (Console).
    3. Sauvegarder les logs dans 'logs/bot.log' avec une rotation automatique.
    """
    # 1. S'assurer que le dossier 'logs' existe
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
        
    log_file = os.path.join(log_dir, "bot.log")

    # 2. Récupérer le logger global
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Évite d'ajouter plusieurs fois les mêmes canaux si setup_logging() est appelé plusieurs fois
    if logger.hasHandlers():
        logger.handlers.clear()

    # 3. Définir le format d'affichage (Date, Niveau, Message)
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # --- CANAL 1 : Le Terminal (Console) ---
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # --- CANAL 2 : Le Fichier avec Rotation ---
    # Max 5 Mo par fichier, et garde maximum 3 fichiers de sauvegarde
    file_handler = RotatingFileHandler(
        log_file, 
        maxBytes=5 * 1024 * 1024, 
        backupCount=3, 
        encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    logging.info("Système de logs initialisé (Console + Fichier).")
    
def log_securite(action: str, titre: str, hash_code: str = ""):
    
    hash_court = hash_code[:20] if hash_code else "N/A"
    titre_court = titre[:80] if titre else "Pas de titre"
    
    # On formate le message 
    message_log = f"Action: {action} | HASH: {hash_court} | TITRE: {titre_court}"
    logging.info(message_log)
    