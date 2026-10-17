
import hashlib 
from fingerprint import add_fingerprint

def empreinte(titre, lien):
    hash_create = hashlib.sha256((titre + lien).encode()).hexdigest()
    add_fingerprint(hash_create)
    return hash_create
