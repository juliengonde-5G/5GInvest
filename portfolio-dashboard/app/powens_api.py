"""
Module Powens (ex-Budget Insight) - Agrégation bancaire.
API: https://docs.powens.com/api-reference
Sandbox gratuit: https://powens.com/developers/

Flow:
1. POST /auth/init → crée un user anonyme + access_token permanent
2. POST /auth/token/code → code temporaire pour la webview
3. Redirect → webview Powens (l'utilisateur choisit sa banque + s'authentifie)
4. Callback → connection_id créée
5. GET /accounts → liste les comptes
6. GET /transactions → récupère les transactions

Sandbox: {domain}-sandbox.biapi.pro
Production: {domain}.biapi.pro
"""

import os
import json
import time
import requests
import logging
from datetime import date, timedelta
from typing import Optional, List, Dict

logger = logging.getLogger(__name__)

POWENS_DOMAIN = os.environ.get("POWENS_DOMAIN", "")  # ex: "myapp"
POWENS_CLIENT_ID = os.environ.get("POWENS_CLIENT_ID", "")
POWENS_CLIENT_SECRET = os.environ.get("POWENS_CLIENT_SECRET", "")
POWENS_SANDBOX = os.environ.get("POWENS_SANDBOX", "true").lower() == "true"


def _base_url() -> str:
    if not POWENS_DOMAIN:
        return ""
    suffix = "-sandbox.biapi.pro" if POWENS_SANDBOX else ".biapi.pro"
    return f"https://{POWENS_DOMAIN}{suffix}/2.0"


def _headers(token: str = None) -> dict:
    h = {"Content-Type": "application/json"}
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h


def is_configured() -> bool:
    return bool(POWENS_DOMAIN and POWENS_CLIENT_ID)


# ─── AUTH ─────────────────────────────────────────────────

def create_user() -> dict:
    """
    Crée un utilisateur anonyme Powens.
    Retourne: {id, token} — le token est permanent.
    """
    url = f"{_base_url()}/auth/init"
    try:
        resp = requests.post(url, headers=_headers(), json={
            "client_id": POWENS_CLIENT_ID,
            "client_secret": POWENS_CLIENT_SECRET,
        }, timeout=10)
        data = resp.json()
        return {
            "user_id": data.get("id_user"),
            "token": data.get("auth_token"),
        }
    except Exception as e:
        logger.error(f"Powens create_user error: {e}")
        return {"error": str(e)}


def get_webview_url(token: str, redirect_uri: str) -> dict:
    """
    Génère l'URL de la webview Powens pour connecter une banque.
    L'utilisateur sera redirigé vers la webview où il choisit sa banque.
    """
    # 1. Obtenir un code temporaire
    url = f"{_base_url()}/auth/token/code"
    try:
        resp = requests.post(url, headers=_headers(token), timeout=10)
        data = resp.json()
        code = data.get("code")

        if not code:
            return {"error": "Impossible d'obtenir le code d'authentification", "detail": data}

        # 2. Construire l'URL de la webview
        webview_url = (
            f"https://webview.powens.com/connect"
            f"?domain={POWENS_DOMAIN}"
            f"&client_id={POWENS_CLIENT_ID}"
            f"&redirect_uri={redirect_uri}"
            f"&code={code}"
        )

        return {"url": webview_url, "code": code}
    except Exception as e:
        logger.error(f"Powens webview error: {e}")
        return {"error": str(e)}


def get_reconnect_url(token: str, connection_id: int, redirect_uri: str) -> dict:
    """URL pour renouveler l'authentification SCA d'une connexion."""
    try:
        resp = requests.post(f"{_base_url()}/auth/token/code", headers=_headers(token), timeout=10)
        code = resp.json().get("code")
        url = (
            f"https://webview.powens.com/reconnect"
            f"?domain={POWENS_DOMAIN}"
            f"&client_id={POWENS_CLIENT_ID}"
            f"&redirect_uri={redirect_uri}"
            f"&code={code}"
            f"&connection_id={connection_id}"
        )
        return {"url": url}
    except Exception as e:
        return {"error": str(e)}


# ─── CONNEXIONS ───────────────────────────────────────────

def list_connections(token: str) -> list:
    """Liste les connexions bancaires de l'utilisateur."""
    try:
        resp = requests.get(f"{_base_url()}/connections", headers=_headers(token), timeout=10)
        data = resp.json()
        connections = data.get("connections", data if isinstance(data, list) else [])
        return [{
            "id": c.get("id"),
            "id_connector": c.get("id_connector"),
            "state": c.get("state"),  # valid, wrongpass, bug, etc.
            "last_update": c.get("last_update"),
            "connector_name": c.get("connector", {}).get("name") if isinstance(c.get("connector"), dict) else None,
        } for c in connections]
    except Exception as e:
        logger.error(f"Powens list_connections error: {e}")
        return []


def delete_connection(token: str, connection_id: int) -> dict:
    """Supprime une connexion bancaire."""
    try:
        resp = requests.delete(f"{_base_url()}/connections/{connection_id}", headers=_headers(token), timeout=10)
        return {"status": "ok"} if resp.status_code in (200, 204) else resp.json()
    except Exception as e:
        return {"error": str(e)}


# ─── COMPTES ──────────────────────────────────────────────

POWENS_TYPE_MAP = {
    "checking": "ccp",
    "savings": "csl",
    "deposit": "ccp",
    "loan": "credit",
    "market": "cto",
    "life_insurance": "assurance_vie",
    "card": "ccp",
}


def list_accounts(token: str) -> list:
    """Liste tous les comptes de l'utilisateur."""
    try:
        resp = requests.get(f"{_base_url()}/accounts", headers=_headers(token), timeout=10)
        data = resp.json()
        accounts = data.get("accounts", data if isinstance(data, list) else [])
        return [{
            "id": a.get("id"),
            "name": a.get("name", "Compte"),
            "number": a.get("number", ""),
            "iban": a.get("iban", ""),
            "type": POWENS_TYPE_MAP.get(a.get("type", ""), "ccp"),
            "type_raw": a.get("type"),
            "balance": a.get("balance"),
            "currency": a.get("currency", {}).get("id", "EUR") if isinstance(a.get("currency"), dict) else "EUR",
            "disabled": a.get("disabled", False),
            "last_update": a.get("last_update"),
            "connection_id": a.get("id_connection"),
        } for a in accounts if not a.get("disabled")]
    except Exception as e:
        logger.error(f"Powens list_accounts error: {e}")
        return []


def enable_account(token: str, account_id: int) -> dict:
    """Active un compte (requis par Powens avant de pouvoir lire les transactions)."""
    try:
        resp = requests.put(
            f"{_base_url()}/accounts/{account_id}",
            headers=_headers(token),
            json={"disabled": False},
            timeout=10,
        )
        return resp.json()
    except Exception as e:
        return {"error": str(e)}


# ─── TRANSACTIONS ─────────────────────────────────────────

def get_transactions(token: str, account_id: int = None,
                     limit: int = 500, min_date: str = None) -> list:
    """Récupère les transactions."""
    params = {"limit": limit}
    if min_date:
        params["min_date"] = min_date

    endpoint = f"/accounts/{account_id}/transactions" if account_id else "/transactions"

    try:
        resp = requests.get(
            f"{_base_url()}{endpoint}",
            headers=_headers(token),
            params=params,
            timeout=15,
        )
        data = resp.json()
        transactions = data.get("transactions", data if isinstance(data, list) else [])
        return [{
            "date": t.get("date") or t.get("rdate", ""),
            "libelle": t.get("wording") or t.get("original_wording", "Transaction"),
            "montant": t.get("value", 0),
            "reference": str(t.get("id", "")),
            "source": "powens",
            "category_id": t.get("id_category"),
        } for t in transactions]
    except Exception as e:
        logger.error(f"Powens transactions error: {e}")
        return []


# ─── SYNC COMPLÈTE ────────────────────────────────────────

def sync_all(token: str) -> dict:
    """
    Synchronise tous les comptes et transactions.
    Retourne les données prêtes à importer dans notre DB.
    """
    accounts = list_accounts(token)
    result = {"accounts": [], "total_transactions": 0}

    min_date = (date.today() - timedelta(days=90)).isoformat()

    for acc in accounts:
        transactions = get_transactions(token, acc["id"], limit=500, min_date=min_date)
        acc["transactions"] = transactions
        acc["nb_transactions"] = len(transactions)
        result["accounts"].append(acc)
        result["total_transactions"] += len(transactions)
        time.sleep(0.3)  # Rate limiting

    return result
