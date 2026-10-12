# BF-JOB Bot

Bot Python qui surveille les offres d'emploi et les opportunités liées au Burkina Faso, puis envoie des alertes par email et Telegram.

## Objectif

Le bot parcourt des sources comme Google News et GitHub pour détecter des mots-clés liés aux emplois, stages, recrutements et bourses, filtrés pour le Burkina Faso. Il vérifie également la date de publication et d'expiration de chaque offre pour éviter les annonces obsolètes.

## Fonctionnalités

- Scan des flux RSS Google News
- Recherche GitHub sur des mots-clés ciblés
- Détection OCR d'images contenant du texte
- Analyse de dates pour valider les offres encore actives
- Filtrage des contenus blacklistés
- Envoi d'alertes par:
  - email SMTP
  - Telegram
- Gestion du compteur quotidien pour limiter les messages
- Protection contre la croissance excessive du fichier de suivi

## Stack technique

- Python 3.11
- `feedparser`
- `requests`
- `Pillow`
- `pytesseract`
- GitHub Actions pour exécution planifiée

## Structure du projet

```text
bf-job-bot/
├── bot.py
├── requirements.txt
├── LICENSE
├── README.md
├── .github/
│   └── workflows/
│       └── bot.yml
└── ... fichiers générés à l'exécution (seen.json, journal_securite.log, cmtr.json)
```

## Prérequis

- Python 3.11+
- `tesseract-ocr` installé sur la machine
- Variables d'environnement configurées

### Installation de Tesseract

Ubuntu / Debian :

```bash
sudo apt-get update
sudo apt-get install -y tesseract-ocr
```

## Installation

1. Cloner le dépôt

```bash
git clone https://github.com/ynbobm-rgb/bf-job-bot.git
cd bf-job-bot
```

2. Créer un environnement virtuel

```bash
python -m venv .venv
source .venv/bin/activate
```

3. Installer les dépendances

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

## Variables d'environnement

Créez un fichier `.env` ou configurez les variables dans votre environnement.

```bash
export TELEGRAM_TOKEN="VotreTokenTelegram"
export TELEGRAM_CHAT_ID="VotreChatIdTelegram"
export EMAIL_FROM="votre_email@gmail.com"
export EMAIL_PASS="votre_mot_de_passe_app"
export EMAIL_TO="destinataire@example.com"
```

Notes :
- Pour Gmail, il faut souvent utiliser un mot de passe d'application.
- Les variables peuvent aussi être injectées directement dans GitHub Actions via les secrets du dépôt.

## Lancement

```bash
python bot.py
```

Le script est conçu pour être exécuté régulièrement via GitHub Actions ou via un cron système.

## GitHub Actions

Le workflow planifié est défini dans :

```text
.github/workflows/bot.yml
```

Il s'exécute toutes les 30 minutes avec la commande :

```yaml
- name: Run bot
  run: python bot.py
```

Le workflow installe les dépendances systèmes et Python avant le lancement.

## Dépendances Python

Le fichier `requirements.txt` contient les dépendances minimales requises :

```txt
feedparser
requests
Pillow
pytesseract
```

## Sécurité et fichiers générés

Le bot crée plusieurs fichiers d'exécution :

- `seen.json` : historique des offres déjà traitées
- `journal_securite.log` : journal de sécurité
- `cmtr.json` : compteur quotidien

Ces fichiers doivent être gardés dans le dossier de travail du bot et peuvent être nettoyés périodiquement selon les besoins.

## Limites actuelles

- Code monolithique dans `bot.py`
- Pas de tests automatiques
- Pas de README complet sur l'architecture logicielle
- Gestion de configuration à améliorer (utiliser un fichier de config dédié)

## Licence

Ce projet est distribué sous licence MIT.

## Contribution

Les contributions sont les bienvenues. Pour modifier le projet :

1. Créez une branche
2. Appliquez vos changements
3. Testez localement
4. Ouvrez une pull request

## Avertissement

Ce projet sert de surveillance automatisée de contenu public. Vérifiez toujours la conformité légale et la fiabilité des sources que vous exploitez selon votre usage.
