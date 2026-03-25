#!/bin/bash
#
# 5GInvest - Script d'installation sur VPS OVH
# Compatible avec un serveur ayant déjà une autre app.
#
# Usage:
#   chmod +x deploy/install.sh
#   sudo ./deploy/install.sh
#
set -e

echo "═══════════════════════════════════════════════"
echo "  5GInvest - Installation sur VPS"
echo "═══════════════════════════════════════════════"

APP_DIR="/opt/5ginvest"
DOMAIN=""

# ─── 1. Vérifier les prérequis ──────────────────

echo ""
echo "[1/6] Vérification des prérequis..."

# Docker
if ! command -v docker &> /dev/null; then
    echo "  Docker non trouvé. Installation..."
    curl -fsSL https://get.docker.com | sh
    systemctl enable docker
    echo "  Docker installé."
else
    echo "  Docker: OK"
fi

# Docker Compose
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "  Docker Compose non trouvé. Installation..."
    apt-get install -y docker-compose-plugin || pip install docker-compose
    echo "  Docker Compose installé."
else
    echo "  Docker Compose: OK"
fi

# Nginx
if ! command -v nginx &> /dev/null; then
    echo "  Nginx non trouvé. Installation..."
    apt-get update && apt-get install -y nginx
    echo "  Nginx installé."
else
    echo "  Nginx: OK (config existante préservée)"
fi

# Certbot
if ! command -v certbot &> /dev/null; then
    echo "  Certbot non trouvé. Installation..."
    apt-get install -y certbot python3-certbot-nginx
    echo "  Certbot installé."
else
    echo "  Certbot: OK"
fi

# ─── 2. Copier les fichiers ─────────────────────

echo ""
echo "[2/6] Copie des fichiers..."

mkdir -p "$APP_DIR/data"

# Copier tout le projet
cp -r . "$APP_DIR/"
cd "$APP_DIR"

echo "  Fichiers copiés dans $APP_DIR"

# ─── 3. Configuration du domaine ─────────────────

echo ""
echo "[3/6] Configuration du domaine..."
read -p "  Sous-domaine ou domaine pour 5GInvest (ex: invest.mondomaine.fr): " DOMAIN

if [ -z "$DOMAIN" ]; then
    echo "  Pas de domaine. L'app sera accessible sur le port 8042."
    echo "  Vous pourrez configurer Nginx manuellement plus tard."
else
    # Configurer Nginx
    sed "s/invest.VOTRE_DOMAINE.fr/$DOMAIN/g" deploy/nginx-5ginvest.conf > /etc/nginx/sites-available/5ginvest

    if [ ! -L /etc/nginx/sites-enabled/5ginvest ]; then
        ln -s /etc/nginx/sites-available/5ginvest /etc/nginx/sites-enabled/
    fi

    # Vérifier la config nginx
    nginx -t
    systemctl reload nginx
    echo "  Nginx configuré pour $DOMAIN"
fi

# ─── 4. Build et lancement Docker ────────────────

echo ""
echo "[4/6] Build Docker..."

docker compose build
docker compose up -d

echo "  Container 5ginvest lancé."

# ─── 5. HTTPS avec Let's Encrypt ─────────────────

echo ""
echo "[5/6] Configuration HTTPS..."

if [ -n "$DOMAIN" ]; then
    read -p "  Configurer HTTPS avec Let's Encrypt ? (o/n) [o]: " SETUP_SSL
    SETUP_SSL=${SETUP_SSL:-o}

    if [ "$SETUP_SSL" = "o" ]; then
        read -p "  Email pour Let's Encrypt: " EMAIL
        certbot --nginx -d "$DOMAIN" --non-interactive --agree-tos -m "$EMAIL" || {
            echo "  Certbot a échoué. Vérifiez que le DNS pointe vers ce serveur."
            echo "  Relancez: sudo certbot --nginx -d $DOMAIN"
        }
    fi
else
    echo "  Pas de domaine, HTTPS ignoré."
fi

# ─── 6. Vérification ─────────────────────────────

echo ""
echo "[6/6] Vérification..."

sleep 3

if curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8042/api/home | grep -q "200"; then
    echo "  API: OK"
else
    echo "  API: En cours de démarrage... (vérifiez dans 30s)"
fi

echo ""
echo "═══════════════════════════════════════════════"
echo "  INSTALLATION TERMINÉE"
echo "═══════════════════════════════════════════════"
echo ""
if [ -n "$DOMAIN" ]; then
    echo "  URL: https://$DOMAIN"
else
    echo "  URL: http://VOTRE_IP:8042"
fi
echo ""
echo "  Sur votre téléphone Android:"
echo "  1. Ouvrez Chrome et allez sur l'URL ci-dessus"
echo "  2. Menu ⋮ → 'Installer l'application' ou 'Ajouter à l'écran d'accueil'"
echo "  3. Acceptez les notifications quand demandé"
echo ""
echo "  Commandes utiles:"
echo "  cd $APP_DIR && docker compose logs -f        # Voir les logs"
echo "  cd $APP_DIR && docker compose restart        # Redémarrer"
echo "  cd $APP_DIR && docker compose down           # Arrêter"
echo "  cd $APP_DIR && docker compose up -d --build  # Mettre à jour"
echo ""
echo "  L'app existante sur votre VPS n'a PAS été touchée."
echo "═══════════════════════════════════════════════"
