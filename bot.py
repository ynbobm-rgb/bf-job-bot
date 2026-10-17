from logging_config import setup_logging
from scanner.github_search import scan_github
from scanner.google_news import scan_google_news
from storage import limit, seen_load, seen_save


def scan():
    # 1. Initialisation des logs
    setup_logging()
    
    # 2. Chargement des offres déjà vues
    seen = seen_load()
    
    # 3. Lancement des différents scanners
    continuer = scan_google_news(seen)
    if continuer:
        scan_github(seen)
        
    # 4. Sauvegarde finale et vérification des limites
    seen_save(seen)
    limit()
#juste un test