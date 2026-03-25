#!/bin/bash
set -e

echo "═══════════════════════════════════════════"
echo "  Portfolio Dashboard - Déploiement"
echo "═══════════════════════════════════════════"

# Vérifier .env
if [ ! -f .env ]; then
  echo "  Copie de .env.example → .env"
  cp .env.example .env
  echo "  ATTENTION: Éditez .env avec vos clés API avant de continuer."
  echo "  nano .env"
  exit 1
fi

# Build et lancement
echo "[1/3] Build des images Docker..."
docker compose -f docker-compose.prod.yml build

echo "[2/3] Lancement des services..."
docker compose -f docker-compose.prod.yml up -d

echo "[3/3] Migrations DB..."
sleep 5
docker compose -f docker-compose.prod.yml exec backend flask db upgrade

echo ""
echo "═══════════════════════════════════════════"
echo "  Dashboard accessible sur:"
echo "  Backend API: http://localhost:5050"
echo "  Frontend:    http://localhost:5051"
echo "═══════════════════════════════════════════"
