import requests 
from PIL import Image
from io import BytesIO
import pytesseract
from logging_config import log_securite

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
       