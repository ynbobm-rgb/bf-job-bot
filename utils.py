
import hashlib 

def empreinte(titre, lien):
    return hashlib.sha256((titre + lien).encode()).hexdigest()

