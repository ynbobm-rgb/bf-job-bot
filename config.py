import os

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
log_dir = "logs"

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

SOCIAUX = {
        "GoogleNews": "",
        "Facebook": "site:facebook.com",
        "LinkedIn": "site:linkedin.com",
        "Twitter/X": "site:twitter.com OR site:x.com",
        "Youtube": "site:youtube.com",
        "Instagram": "site:instagram.com",
        "Pinterest": "site:pinterest.com",
}