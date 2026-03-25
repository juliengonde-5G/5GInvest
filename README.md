# 5GInvest - Module d'investissement guidé multi-banques

Application web (PWA) d'aide à la décision pour l'investissement sur banques françaises.
Installable sur Android avec notifications push.

## Fonctionnalités

- **Multi-programmes** : N programmes autonomes (budget, durée, risque)
- **11 banques françaises** : Revolut, Boursorama, Fortuneo, Trade Republic, DEGIRO, etc.
- **Analyse technique** : RSI, MACD, Bollinger, momentum, volume
- **Fiscalité française** : PFU, PEA, AV, PER, comparateur d'enveloppes
- **Justification** : chaque recommandation est expliquée et argumentée
- **Alertes push** : notifications Android quand il faut agir
- **Horaires France** : pas de vente la nuit (07:30-22:00 Paris)
- **Briefing matinal** : résumé des marchés à 8h

## Installation rapide sur VPS OVH

```bash
git clone <repo> /opt/5ginvest
cd /opt/5ginvest
sudo ./deploy/install.sh
```

Le script installe Docker, Nginx, configure le reverse proxy (compatible avec une app existante),
et lance l'application. HTTPS via Let's Encrypt inclus.

## Installation locale

```bash
pip install -r requirements.txt

# CLI
python main.py              # Page d'accueil
python main.py profile      # Configurer le profil
python main.py program create  # Créer un programme

# API Web
uvicorn api.app:app --reload
# Ouvrir http://localhost:8000
```

## Sur Android

1. Ouvrir Chrome sur `https://votre-domaine.fr`
2. Menu > "Installer l'application"
3. Accepter les notifications
4. L'app se comporte comme une app native

## Architecture

```
5GInvest/
├── api/
│   ├── app.py              # API FastAPI
│   ├── push_service.py     # Notifications push VAPID
│   └── scheduler.py        # Surveillance auto (APScheduler)
├── web/static/
│   ├── index.html          # PWA single-page app
│   ├── app.js              # Frontend JavaScript
│   ├── style.css           # Mobile-first dark theme
│   ├── sw.js               # Service Worker (cache + push)
│   └── manifest.json       # PWA manifest
├── config/
│   ├── settings.py         # Configuration globale
│   ├── user_profile.py     # Questionnaire investisseur
│   └── paths.py            # Chemins de persistance
├── banks/catalog.py        # 11 banques françaises
├── fiscal/engine.py        # Calculs fiscaux FR
├── programs/engine.py      # Moteur de programmes
├── strategy/
│   ├── indicators.py       # Indicateurs techniques
│   ├── short_term.py       # Stratégie court terme
│   └── justifier.py        # Justification des choix
├── alerts/alert_engine.py  # Alertes avec file d'attente
├── portfolio/tracker.py    # Suivi positions et P&L
├── deploy/
│   ├── install.sh          # Installation VPS
│   ├── update.sh           # Mise à jour
│   └── nginx-5ginvest.conf # Config reverse proxy
├── Dockerfile
├── docker-compose.yml
└── main.py                 # CLI
```
