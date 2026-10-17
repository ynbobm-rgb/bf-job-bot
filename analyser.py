from datetime import timedelta
import re
import datetime

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
