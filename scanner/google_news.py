import time
from analyser import analyse_offre, extraire_images_de_entry
from config import BLACKLIST, KEYWORDS, MAX_PAR_JOUR, QUERY_PAYS, SOCIAUX
import feedparser
from datetime import datetime
import logging
from logging_config import log_securite
from notifier.emailer import mail
from notifier.telegram import telegram
from ocr import lire_texte_dans_image
from storage import get_compteur, inc_compteur
from utils import empreinte

def scan_google_news(seen: dict):
    """
    Parcourt les flux Google News pour trouver des offres.
    """
    logging.info("Démarrage du scan Google News...")
    
    for nom_radar, filtre_site in SOCIAUX.items():
        if get_compteur() >= MAX_PAR_JOUR:
            log_securite("Limite-Jour", f"Limite {MAX_PAR_JOUR}/jour atteinte", "N/A")
            return False

        for k in KEYWORDS:
            query = f"{k} {QUERY_PAYS} {filtre_site}".strip()
            rss_url = f"https://news.google.com/rss/search?q={query.replace(' ', '+')}&hl=fr&gl=BF&ceid=BF:fr"
            
            try:
                feed = feedparser.parse(rss_url)
                for e in feed.entries[:5]:
                    h = empreinte(e.title, e.link)
                    if h in seen:
                        continue

                    texte_a_analyser = e.title + " " + e.get("summary", "")

                    # --- VERIF 1 : PHOTO ILLISIBLE / OCR ---
                    try:
                        images = extraire_images_de_entry(e)
                        if images:
                            log_securite("PHOTO-DETECTEE", f"{len(images)} image(s) -> OCR en cours - {e.title}", h)
                            for img_url in images:
                                texte_image = lire_texte_dans_image(img_url)
                                if texte_image:
                                    texte_a_analyser += " " + texte_image
                                break
                    except Exception as e_ocr:
                        log_securite("OCR-ILLISIBLE", f"On garde juste le lien - {e_ocr}", h)

                    # --- VERIF 2 : DATE ILLISIBLE ---
                    try:
                        analyse = analyse_offre(e, texte_a_analyser)
                    except Exception as e_date:
                        log_securite("DATE-ILLISIBLE", f"Date illisible, envoi dégradé - {e.title}", h)
                        if any(mot.lower() in texte_a_analyser.lower() for mot in KEYWORDS):
                            mail(f"{e.title} [A VERIFIER - Photo illisible]", e.link, f"{nom_radar} - Dégradé", h)
                            telegram(f"{e.title} [A VERIFIER - Photo illisible]", e.link, f"{nom_radar} - Dégradé", h)
                            inc_compteur()
                            
                            seen[h] = {"titre": e.title, "lien": e.link, "date": str(datetime.now()), "source": nom_radar, "degrade": True}
                            
                            if get_compteur() >= MAX_PAR_JOUR:
                                log_securite("Limite-Atteinte", "On stoppe pour aujourd'hui", "N/A")
                                return False
                        continue

                    # --- VERIF 3 : VALIDITE DE L'OFFRE ---
                    if not analyse["valide"]:
                        log_securite("EXPIREE", f"Fin le {analyse['fin'].strftime('%d/%m/%Y')} - {e.title}", h)
                        seen[h] = {"titre": e.title, "expire": True, "fin": str(analyse["fin"])}
                        continue

                    # --- FILTRE BLACKLIST ---
                    if any(b in e.title.lower() for b in BLACKLIST):
                        log_securite(f"Rejet-{nom_radar}", e.title, h)
                        seen[h] = {"titre": e.title, "rejete": True}
                        continue

                    urgent = "Urgent - Expire dans " if analyse["jours_restants"] <= 3 else "Valide"
                    log_securite(f"{urgent}", f"Reste {analyse['jours_restants']}j - {e.title}", h)
                    
                    titre_enrichi = f"{e.title} [Fin: {analyse['fin'].strftime('%d/%m/%Y')} - {analyse['jours_restants']}j restants]"
                    mail(titre_enrichi, e.link, f"Web | Publié le {analyse['publication'].strftime('%d/%m/%Y')}", h)
                    telegram(titre_enrichi, e.link, f"Web | Publié le {analyse['publication'].strftime('%d/%m/%Y')}", h)
                    
                    inc_compteur()
                    seen[h] = {
                        "titre": e.title, 
                        "lien": e.link, 
                        "date": str(datetime.now()), 
                        "source": nom_radar, 
                        "fin": str(analyse['fin']), 
                        "jours_restants": analyse['jours_restants']
                    }
                    
                    if get_compteur() >= MAX_PAR_JOUR:
                        log_securite("Limite-Atteinte", "On stoppe pour aujourd'hui", "N/A")
                        return False

            except Exception as ex:
                log_securite(f"Erreur-Scan-{nom_radar}", str(ex), "N/A")
            
            time.sleep(5)  # Sécurité anti-ban
            
    return True



