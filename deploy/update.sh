#!/bin/bash
# 5GInvest - Mise à jour sur VPS
# Usage: sudo ./deploy/update.sh
set -e

APP_DIR="/opt/5ginvest"
cd "$APP_DIR"

echo "Mise à jour de 5GInvest..."

# Pull le code (si git configuré)
if [ -d .git ]; then
    git pull origin claude/revolut-investment-guide-lL2VL
fi

# Rebuild et redémarrer
docker compose down
docker compose build --no-cache
docker compose up -d

echo "Mise à jour terminée."
docker compose logs --tail=20
