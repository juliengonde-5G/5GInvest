"""
Chemins de fichiers de persistance.
En Docker: utilise /app/data/ (volume monté)
En local: utilise le répertoire courant.
"""

import os

DATA_DIR = os.environ.get("FGINVEST_DATA_DIR", os.path.join(os.path.dirname(os.path.dirname(__file__)), "data"))

# Créer le répertoire data s'il n'existe pas
os.makedirs(DATA_DIR, exist_ok=True)

PROFILE_FILE = os.path.join(DATA_DIR, "user_profile.json")
PORTFOLIO_FILE = os.path.join(DATA_DIR, "portfolio.json")
PROGRAMS_FILE = os.path.join(DATA_DIR, "programs.json")
SUBSCRIPTIONS_FILE = os.path.join(DATA_DIR, "push_subscriptions.json")
VAPID_FILE = os.path.join(DATA_DIR, "vapid_keys.json")
ALERTS_LOG = os.path.join(DATA_DIR, "alerts.log")
