#!/usr/bin/env python3
"""
architecture_report.py

Script exécutable qui génère un fichier ARCHITECTURE.md décrivant
l'architecture proposée, les risques, le design et un plan de refactor
pour le projet bf-job-bot.

Usage:
  python architecture_report.py

Le script écrit ARCHITECTURE.md à la racine du dépôt et affiche un
résumé dans la sortie standard.

Langue: Français
"""

from __future__ import annotations
import os
import sys
from datetime import datetime

ARCH_MD = "ARCHITECTURE.md"

CONTENT = f"""
# Architecture, Design et Plan de Refactor — BF-JOB Bot

Généré le: {datetime.utcnow().isoformat()}Z

## But

Un plan architectural clair pour transformer le script monolithique `bot.py` en un projet structuré, testable et maintenable. Le document couvre la structure proposée, les responsabilités des modules, les risques principaux, les décisions de conception et un plan d'actions exécutable.

### Stack
- Language: Python 3.11
- Exécution: script CLI / worker planifiable (cron / GitHub Actions)
- Librairies principales: feedparser, requests, Pillow, pytesseract

## Structure proposée (arborescence)

```text
bf_job_bot/                # package principal
  __init__.py
  __main__.py              # point d'entrée (console script)
  config.py                # configuration (pydantic/BaseSettings)
  logging_config.py        # configuration du logging
  scanner/                 # récupère des sources (Google News, GitHub...)
    __init__.py
    google_news.py
    github_search.py
  ocr.py                   # fonctions OCR (pytesseract wrapper)
  analyser.py              # parsing des dates, règles métier
  notifier/                # envoi de notifications
    __init__.py
    emailer.py
    telegram.py
  storage.py               # abstraction de persistence (JSON/SQLite)
  utils.py                 # helpers (hash, parse HTML, validation)
  maintenance.py           # rotation des fichiers, purge seen.json
tests/
  unit/
  integration/
.github/
  workflows/
    bot.yml                # workflow existant mis à jour
README.md
requirements.txt
ARCHITECTURE.md
```

## Rôles & flux d'exécution
- __main__ initialise la configuration, les logs et lance un orchestrateur `run()`.
- `scanner` collecte items (entries) depuis RSS et GitHub et retourne des objets normalisés (title, link, summary, images, published).
- `ocr` lit les images simulées et retourne le texte détecté.
- `analyser` compose le texte (title + summary + ocr) et extrait/valide les dates; renvoie un objet `AnalysisResult`.
- `notifier` s'occupe d'envoyer les messages (email et Telegram) de façon testable (interfaces mockables).
- `storage` stocke l'état (seen, compteur) de façon atomique (lock/transaction). Idéalement : adapter pour SQLite si besoin d'atomicité.

## Principales décisions de design
1. Configuration typée: utiliser `pydantic.BaseSettings` (ou `python-dotenv`) pour centraliser et valider les variables d'environnement (TELEGRAM_TOKEN, EMAIL_*...).
2. Logging structuré: `logging` module, handlers rotatifs (RotatingFileHandler), niveau configurable par env var.
3. Réessais et backoff: centraliser les appels HTTP via une session `requests.Session()` et wrapper pour retry exponentiel (tenacity ou implémentation simple).
4. Abstraction de stockage: interface `Storage` avec implémentation `JsonStorage` et option `SqliteStorage`.
5. Tests: isolation par DI (dependency injection) ; mocks pour HTTP et SMTP; tests unitaires pour parsing de dates et OCR wrapper.
6. CI: pipeline GitHub Actions avec jobs: lint, type-check, tests (pytest), et déploiement si besoin.

## Risques identifiés & recommandations

1. Concurrence et corruption de fichiers JSON
   - Risque: `seen.json` écrit simultanément -> corruption.
   - Mitigation: utiliser verrous de fichier (flock) ou migrer vers SQLite.

2. Exposition de secrets
   - Risque: EMAIL_PASS, TELEGRAM_TOKEN dans logs ou commits.
   - Mitigation: valider l'utilisation de `secrets` sur Actions, ne pas logger les secrets, utiliser variables d'environnement/secret manager.

3. Taux d'appel API & ratelimiting
   - Risque: GitHub Search non-authentifié -> limites basses.
   - Mitigation: utiliser token GitHub via env (GITHUB_TOKEN) et gérer `X-RateLimit-Remaining` et retry.

4. OCR peu fiable / coût
   - Risque: OCR augmente taux de faux positifs et coût CPU.
   - Mitigation: OCR seulement si nécessaire (taille d'image, format), et mettre timeout/queue; batcher le travail si montée en charge.

5. Envoi massif d'emails / spam
   - Risque: envoyer trop d'alertes -> bloqué par SMTP/Telegram.
   - Mitigation: regrouper alertes, backoff, quotas journaliers (déjà présent mais à fiabiliser), et opt-in/out.

6. Parser de dates fragile
   - Risque: expressions régulières actuelles manquent de robustesse.
   - Mitigation: utiliser `dateparser` (support langues) ou tests étendus et heuristiques plus strictes.

## Plan de migration (étapes concrètes)

1. Init: ajouter scaffolding package + config + logging
   - Créer `bf_job_bot/__main__.py` qui invoque `run()`.
   - Déplacer fonctions utilitaires dans modules.

2. Stockage: implémenter `storage.py` avec interface et `JsonStorage` safe

3. Notifier: extraire email/telegram dans `notifier/` et y ajouter tests (mock SMTP, requests)

4. Scanner: séparer Google News & GitHub search en modules testables

5. Tests: ajouter pytest, fixtures `tests/unit/test_analyser.py`, `tests/unit/test_utils.py`.

6. CI: mettre en place workflow multi-steps: lint -> tests -> build

7. Documentation: compléter README et ajouter ARCHITECTURE.md

## Exemple minimal de contrat d'API interne (pseudo types)

```python
# AnalysisResult
{
  "title": str,
  "link": str,
  "publication": datetime,
  "fin": Optional[datetime],
  "valide": bool,
  "jours_restants": int,
}
```

## Checklist de qualité
- [ ] CI exécute tests à chaque PR
- [ ] Couverture minimale 70% pour `analyser` et `utils`
- [ ] Aucun secret dans les logs ou commits
- [ ] `seen.json` protégé par rotation et backup
- [ ] Gestion d'erreurs et retries sur tous les appels réseau

## Commandes recommandées (local)

```bash
# créer venv et installer
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# exécuter le script généré
python bot.py

# exécuter le générateur d'architecture (ce fichier)
python architecture_report.py
```

## Prochaines actions que je peux faire pour toi
1. Générer automatiquement le scaffolding minimal (création de fichiers module avec squelettes) sur une branche dédiée.
2. Écrire les tests unitaires pour `extraire_date_du_texte` et `analyse_offre`.
3. Implémenter `storage.py` safe + migration vers SQLite.

---

Fin du document. Réécris/ajuste si tu veux plus de détails sur une partie (tests, storage, notifier) ou veux que je crée automatiquement la structure de fichiers.
"""


def write_architecture():
    with open(ARCH_MD, 'w', encoding='utf-8') as f:
        f.write(CONTENT)
    print(f"Fichier {ARCH_MD} écrit avec succès dans: {os.path.abspath(ARCH_MD)}")


if __name__ == '__main__':
    try:
        write_architecture()
        print('\nRésumé:')
        print('- Document généré: ARCHITECTURE.md')
        print('- Si tu veux, je peux maintenant:')
        print('  * créer le scaffolding de modules (ex: bf_job_bot/...) dans une branche')
        print('  * écrire des tests unitaires pour les fonctions critiques')
    except Exception as e:
        print('Erreur lors de la génération:', e)
        sys.exit(1)
