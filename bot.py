import feedparser, requests, json, os, time, smtplib, hashlib
from email.mime.text import MIMEText
from datetime import datetime, timedelta

import re
from PIL import Image
import pytesseract
from io import BytesIO

KEYWORDS = [
    "recrutement",
    "embauche",
    "offre d'emploi", 
    "emploi", 
    "stage", 
    "concours", 
    "job",
    "hiring",
    "CDD",
    "CDI",
    "Bourse d'etude",
    "bourse"
    ]
QUERY_PAYS = "Burkina Faso"

SEEN = "seen.json"
JOURNAL = "journal_securite.log"
BLACKLIST = [
    "1xbet",
    "parieur", 
    "crypto", 
    "investissement rapide"
    ]
EMAIL_FROM = os.getenv("EMAIL_FROM")
EMAIL_PASS = os.getenv("EMAIL_PASS")
TO = os.getenv("EMAIL_TO")

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
MAX_PAR_JOUR = 20
COMPTEUR_FILE = "cmtr.json"
LIMITE_TAILLE_MO = 3  # 5 Mo

def extraire_images_de_entry(entry):
    images = []
    # Cas 1: media:content (YouTube, News)
    if "media_content" in entry:
        for m in entry.media_content:
            if "image" in m.get("type", "") or m.get("url","").endswith((".jpg",".png",".jpeg")):
                images.append(m["url"])
    # Cas 2: image dans le résumé HTML
    if "summary" in entry:
        imgs = re.findall(r'<img[^>]+src="([^"]+)"', entry.summary)
        images.extend(imgs)
    # Cas 3: enclosure
    if "links" in entry:
        for l in entry.links:
            if "image" in l.get("type",""):
                images.append(l.get("href"))
    return list(set(images))[:2] # on prend max 2 images pour rester rapide

def lire_texte_dans_image(url_image):
    try:
        r = requests.get(url_image, timeout=10, headers={"User-Agent": "BF-JOB-BOT"})
        if r.status_code != 200:
            return ""
        img = Image.open(BytesIO(r.content))
        # OCR - lit le français
        texte = pytesseract.image_to_string(img, lang='fra+eng')
        return texte
    except Exception as e:
        log_securite("ERREUR-OCR", str(e), "N/A")
        return ""
        

def extraire_date_du_texte(texte):
    patterns = [
        r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
        r'(\d{1,2}\s+(janvier|fevrier|mars|avril|mai|juin|juillet|aout|septembre|octobre|novembre|decembre)\s+\d{4})',
        r'date limite.*?(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
        r'cloture.*?(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
    ]
    mois_fr = {
        "janvier": "01", "fevrier": "02", "février": "02",
        "mars": "03", "avril": "04", "mai": "05", "juin": "06",
        "juillet": "07", "aout": "08", "août": "08",
        "septembre": "09", "octobre": "10", "novembre": "11", "decembre": "12", "décembre": "12"
    }
    for p in patterns:
        m = re.search(p, texte.lower())
        if m:
            try:
                date_str = m.group(1)
                # Si c'est du type "12 janvier 2024"
                if any(mois in date_str for mois in mois_fr):
                    for nom, num in mois_fr.items():
                        date_str = date_str.replace(nom, num)
                    # maintenant date_str est "12 01 2024"
                    try:
                        return datetime.strptime(date_str, "%d %m %Y")
                    except:
                        continue
                # parser en JJMMAAAA
                for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%d/%m/%y", "%d-%m-%y"):
                    try:
                        return datetime.strptime(date_str, fmt)
                    except:
                        continue
            except:
                continue
    return None

def analyse_offre(entry, texte_complet=None):
    # temps de pub
    try:
        temp_publication = datetime(*entry.published_parsed[:6])
    except:
        temp_publication = datetime.now()
    
    # temps de debut = temps de pub
    temp_debut = temp_publication

    if texte_complet is None:
        texte_complet=entry.title + " " + entry.get("summary","")

    # temps de fin
    temp_fin = extraire_date_du_texte(texte_complet)
    
    if not temp_fin:
        temp_fin = temp_debut + timedelta(days=21)
    
    # temps actuel
    temp_actuel = datetime.now()

    # analyse
    est_valide = temp_actuel < temp_fin and temp_actuel >= temp_debut
    jours_restants = (temp_fin - temp_actuel).days
    data = {
        "publication": temp_publication,
        "debut": temp_debut,
        "fin": temp_fin,
        "actuel": temp_actuel,
        "valide": est_valide,
        "jours_restants": jours_restants
    }
    return data

def empreinte(titre, lien):
    return hashlib.sha256((titre + lien).encode()).hexdigest()

def log_securite(action, titre, hash_code):
    ligne = f"{datetime.now()} | {action} | {hash_code[:20]} | {titre[:80]} \n"
    with open(JOURNAL, "a", encoding="utf-8") as f:
        f.write(ligne)
    print(ligne.strip())

def seen_load():
    try:
        return json.load(open(SEEN))
    except:
        return {}

def seen_save(s):
    json.dump(s, open(SEEN,"w"), indent=2)

    
def mail_telegram(titre, lien, source, hash_code):
    # mail avec signature
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
                <small>Bot BF-Job * Scan auto tous les 15min * Burkina Faso - {datetime.now()}</small>
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
    # telegram
    try:
        if TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
            text = f"*Bot BF-JOB*\n\n*{titre}*\n{lien}\n\nSource:{source}\nEmpreinte: `{hash_code[:20]}`"
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
            mail_telegram(f"[MAINTENANCE] seen.json {taille_mo:.2f}Mo - Nettoyage", "https://render.com", f"Maintenance - {taille_mo:.2f}Mo", "MAINTENANCE")
            
            # 2. Sauvegarde backup local (optionnel)
            backup_name = f"seen_backup_{datetime.now().strftime('%Y%m%d')}.json"
            os.rename(SEEN, backup_name)
            
            # 3. Vide pour libérer
            seen_save({})
            log_securite("SEEN-VIDE", f"Fichier vide, backup: {backup_name}", "N/A")
            
    except Exception as e:
        log_securite("Erreur-Limit", str(e), "N/A")

def scan():
    seen = seen_load()
    if get_compteur() >= MAX_PAR_JOUR:
        log_securite("Limite-Jour", f"Limite {MAX_PAR_JOUR}/jour atteinte", "N/A")
        return 

    SOCIAUX = {
        "GoogleNews": "",
        "Facebook": "site:facebook.com",
        "LinkedIn": "site:linkedin.com",
        "Twitter/X": "site:twitter.com OR site:x.com",
        "Youtube": "site:youtube.com",
        "Instagram": "site:instagram.com",
        "Pinterest": "site:pinterest.com",
    }
    # Radar google news
    for nom_radar, filtre_site in SOCIAUX.items():
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

                    # --- VERIF 1 : PHOTO ILLISIBLE? ---
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

                    # --- VERIF 2 : DATE ILLISIBLE? ---
                    try:
                        analyse = analyse_offre(e, texte_a_analyser)
                    except Exception as e_date:
                        log_securite("DATE-ILLISIBLE", f"Date illisible, envoi degrade - {e.title}", h)
                        # MODE DEGRADE : si mot-cle present on envoie quand meme le lien
                        if any(mot.lower() in texte_a_analyser.lower() for mot in KEYWORDS):
                            mail_telegram(f"{e.title} [A VERIFIER - Photo illisible]", e.link, f"{nom_radar} - Degrade", h)
                            inc_compteur()
                            if get_compteur() >= MAX_PAR_JOUR:
                                log_securite("Limite-Atteinte", "On stope pour aujourd'hui", "N/A")
                                seen_save(seen)
                                return

                            seen[h] = {"titre": e.title, "lien": e.link, "date": str(datetime.now()), "source": nom_radar, "degrade": True}
                        continue

                    # --- PRIORITE 2 : ANALYSE DES DATES SUR LE TEXTE COMPLET (texte + photo) ---
                    # On utilise la fonction analyser_offre que je t'ai donnée avant, mais avec texte_a_analyser
                    
                    if not analyse["valide"]:
                        log_securite("EXPIREE", f"Fin le {analyse['fin'].strftime('%d/%m/%Y')} - {e.title}", h)
                        seen[h] = {"titre": e.title, "expire": True, "fin": str(analyse["fin"])}
                        continue

                    urgent = "Urgent - Expire dans " if analyse["jours_restants"] <= 3 else "Valide"
                    seen[h] = {
                        "titre": e.title,
                        "lien": e.link,
                        "publication": str(analyse["publication"]),
                        "fin": str(analyse["fin"]),
                        "jours_restants": analyse["jours_restants"]
                    }
                    # Filtre
                    if any(b in e.title.lower() for b in BLACKLIST):
                        log_securite(f"Rejet-{nom_radar}", e.title, h)
                        seen[h] = {"titre": e.title, "rejete": True}
                        continue
                    log_securite(f"{urgent}", f"Reste {analyse['jours_restants']}j - {e.title}", h)
                    titre_enrichi = f"{e.title} [Fin: {analyse['fin'].strftime('%d/%m/%Y')} - {analyse['jours_restants']}j restants]"
                    mail_telegram(titre_enrichi, e.link, f"Web | Publier le {analyse['publication'].strftime('%d/%m/%Y')}", h)
                    inc_compteur()
                    if get_compteur() >= MAX_PAR_JOUR:
                        log_securite("Limite-Atteinte", "On stope pour aujourd'hui", "N/A")
                        seen_save(seen)
                        return

                    # Empreinte + Log
                    seen[h] = {"titre": e.title, "lien": e.link, "date": str(datetime.now()), "source":nom_radar, "fin": str(analyse['fin']), "jours_restants": analyse['jours_restants']}
                    log_securite(f"VALIDE-{nom_radar}", e.title, h)

                
            except Exception as e:
                log_securite(f"Erreur-Scan-{nom_radar}", str(e), "N/A")
            time.sleep(5) # securite anti-ban


    # Radar github
    try:
        url = f"https://api.github.com/search/repositories?q={'+'.join(KEYWORDS)}+{QUERY_PAYS}&sort=updated"
        r = requests.get(url, timeout=10, headers={"User-Agent":"BF-JOT-BOT"}).json()
        for repo in r.get("items", [])[:10]:
            titre = repo["name"]
            lien = repo["html_url"]
            h = empreinte(titre, lien)
            if h in seen: continue
                
            seen[h] = {"titre": titre, "lien":lien, "date": str(datetime.now()), "source":"GitHub"}
            log_securite("VALIDE-GitHub", titre, h)
            mail_telegram(titre, lien, "GitHub", h)
            # Radar github
            if get_compteur() >= MAX_PAR_JOUR:
                log_securite("Limite-Jour", "Limite atteinte avant GitHub", "N/A")
                seen_save(seen)
                return
            time.sleep(1)
    except:
        log_securite("Erreur-Scan-GitHub", str(e), "N/A")

    seen_save(seen)
    limit()

if __name__ == "__main__":
    try:
        limit()
        scan()
    except Exception as e:
        log_securite("Crash-Bot", str(e), "N/A")
        print(e)
    # while True:
        # try:
        #     limit()
        #     scan()
        # except Exception as e:
        #     log_securite("Crash-Bot", str(e), "N/A")
        #     print(e)
        #     time.sleep(900) # tous les 15 min
