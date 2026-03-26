"""
Module de connexion bancaire via GoCardless Bank Account Data API (ex-Nordigen).
Gratuit pour usage personnel. Supporte 2400+ banques EU.
Fallback: import CSV manuel ou Linxo.

Flow:
1. Créer un lien de connexion (requisition) vers la banque
2. L'utilisateur s'authentifie sur le site de sa banque
3. On récupère les comptes et transactions via l'API

Docs: https://bankaccountdata.gocardless.com/overview/
"""

import os
import json
import time
import requests
import logging
from datetime import date, timedelta
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

GOCARDLESS_BASE = "https://bankaccountdata.gocardless.com/api/v2"
GOCARDLESS_SECRET_ID = os.environ.get("GOCARDLESS_SECRET_ID", "")
GOCARDLESS_SECRET_KEY = os.environ.get("GOCARDLESS_SECRET_KEY", "")

# Cache token
_token_cache = {"token": None, "expires": 0}


# ─── AUTH ─────────────────────────────────────────────────

def _get_token() -> str:
    """Obtient un access token GoCardless (valide 24h)."""
    if _token_cache["token"] and time.time() < _token_cache["expires"]:
        return _token_cache["token"]

    if not GOCARDLESS_SECRET_ID or not GOCARDLESS_SECRET_KEY:
        return None

    try:
        resp = requests.post(f"{GOCARDLESS_BASE}/token/new/", json={
            "secret_id": GOCARDLESS_SECRET_ID,
            "secret_key": GOCARDLESS_SECRET_KEY,
        }, timeout=10)
        data = resp.json()
        token = data.get("access")
        if token:
            _token_cache["token"] = token
            _token_cache["expires"] = time.time() + data.get("access_expires", 86400) - 60
            return token
    except Exception as e:
        logger.error(f"GoCardless auth error: {e}")
    return None


def _headers() -> dict:
    token = _get_token()
    if not token:
        return {}
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def is_configured() -> bool:
    """Vérifie si l'API bancaire est configurée."""
    return bool(GOCARDLESS_SECRET_ID and GOCARDLESS_SECRET_KEY)


# ─── INSTITUTIONS (liste des banques) ────────────────────

# Banques françaises populaires - IDs GoCardless
FR_BANKS = {
    "REVOLUT_REVOGB21": {"nom": "Revolut", "logo": "revolut"},
    "BOURSORAMA_BOUSFRPP": {"nom": "Boursorama", "logo": "boursorama"},
    "FORTUNEO_FTNOFRP1": {"nom": "Fortuneo", "logo": "fortuneo"},
    "N26_NTSBDEB1": {"nom": "N26", "logo": "n26"},
    "SOCIETE_GENERALE_SOGEFRPP": {"nom": "Société Générale", "logo": "sg"},
    "BNP_PARIBAS_BNPAFRPP": {"nom": "BNP Paribas", "logo": "bnp"},
    "CREDIT_AGRICOLE_AGRIFRPP": {"nom": "Crédit Agricole", "logo": "ca"},
    "LA_BANQUE_POSTALE_PSSTFRPP": {"nom": "La Banque Postale", "logo": "lbp"},
    "LCL_CRLYFRPP": {"nom": "LCL", "logo": "lcl"},
    "CIC_CMCIFRPP": {"nom": "CIC", "logo": "cic"},
    "CREDIT_MUTUEL_CMCIFR2A": {"nom": "Crédit Mutuel", "logo": "cm"},
    "CAISSE_D_EPARGNE_CEPAFRPP": {"nom": "Caisse d'Épargne", "logo": "ce"},
    "BANQUE_POPULAIRE_CCBPFRPP": {"nom": "Banque Populaire", "logo": "bp"},
    "HSBC_CCFRFRPP": {"nom": "HSBC France", "logo": "hsbc"},
    "ING_INGBFRPP": {"nom": "ING", "logo": "ing"},
    "HELLO_BANK_BNPAFRPP": {"nom": "Hello Bank", "logo": "hellobank"},
}


def list_institutions(country: str = "FR") -> list:
    """Liste les banques disponibles pour un pays."""
    headers = _headers()
    if not headers:
        # Fallback: liste statique
        return [{"id": k, "name": v["nom"]} for k, v in FR_BANKS.items()]

    try:
        resp = requests.get(
            f"{GOCARDLESS_BASE}/institutions/?country={country}",
            headers=headers, timeout=10,
        )
        return resp.json()
    except Exception as e:
        logger.error(f"List institutions error: {e}")
        return [{"id": k, "name": v["nom"]} for k, v in FR_BANKS.items()]


# ─── CONNEXION (requisition) ─────────────────────────────

def create_bank_link(institution_id: str, redirect_url: str) -> dict:
    """
    Crée un lien de connexion bancaire.
    L'utilisateur sera redirigé vers sa banque pour s'authentifier.
    Retourne: {id, link, status}
    """
    headers = _headers()
    if not headers:
        return {"error": "API bancaire non configurée. Ajoutez GOCARDLESS_SECRET_ID/KEY dans .env"}

    try:
        # 1. Créer un agreement (90 jours accès)
        agreement_resp = requests.post(f"{GOCARDLESS_BASE}/agreements/enduser/", headers=headers, json={
            "institution_id": institution_id,
            "max_historical_days": 90,
            "access_valid_for_days": 90,
            "access_scope": ["balances", "details", "transactions"],
        }, timeout=10)
        agreement = agreement_resp.json()

        # 2. Créer la requisition (lien de connexion)
        req_resp = requests.post(f"{GOCARDLESS_BASE}/requisitions/", headers=headers, json={
            "redirect": redirect_url,
            "institution_id": institution_id,
            "agreement": agreement.get("id"),
            "user_language": "FR",
        }, timeout=10)
        requisition = req_resp.json()

        return {
            "requisition_id": requisition.get("id"),
            "link": requisition.get("link"),
            "status": requisition.get("status"),
            "institution_id": institution_id,
        }
    except Exception as e:
        logger.error(f"Create bank link error: {e}")
        return {"error": str(e)}


def get_requisition_status(requisition_id: str) -> dict:
    """Vérifie le statut d'une connexion bancaire."""
    headers = _headers()
    if not headers:
        return {"error": "API non configurée"}

    try:
        resp = requests.get(f"{GOCARDLESS_BASE}/requisitions/{requisition_id}/", headers=headers, timeout=10)
        data = resp.json()
        return {
            "id": data.get("id"),
            "status": data.get("status"),
            "accounts": data.get("accounts", []),
            "institution_id": data.get("institution_id"),
        }
    except Exception as e:
        return {"error": str(e)}


# ─── COMPTES ──────────────────────────────────────────────

def get_account_details(account_id: str) -> dict:
    """Récupère les détails d'un compte bancaire."""
    headers = _headers()
    if not headers:
        return {"error": "API non configurée"}

    try:
        # Détails
        details_resp = requests.get(f"{GOCARDLESS_BASE}/accounts/{account_id}/details/", headers=headers, timeout=10)
        details = details_resp.json().get("account", {})

        # Solde
        balance_resp = requests.get(f"{GOCARDLESS_BASE}/accounts/{account_id}/balances/", headers=headers, timeout=10)
        balances = balance_resp.json().get("balances", [])

        # Prendre le solde "interimAvailable" ou "closingBooked"
        solde = 0
        for b in balances:
            if b.get("balanceType") in ("interimAvailable", "closingBooked"):
                solde = float(b.get("balanceAmount", {}).get("amount", 0))
                break

        return {
            "account_id": account_id,
            "iban": details.get("iban", ""),
            "name": details.get("name") or details.get("product", "Compte"),
            "currency": details.get("currency", "EUR"),
            "owner_name": details.get("ownerName", ""),
            "solde": solde,
            "type": _detect_account_type(details),
        }
    except Exception as e:
        logger.error(f"Account details error: {e}")
        return {"error": str(e)}


def _detect_account_type(details: dict) -> str:
    """Détecte le type de compte depuis les détails bancaires."""
    product = (details.get("product") or details.get("name") or "").lower()
    if "livret a" in product:
        return "livret_a"
    elif "ldds" in product or "développement durable" in product:
        return "ldds"
    elif "lep" in product or "épargne populaire" in product:
        return "lep"
    elif "pel" in product:
        return "pel"
    elif "cel" in product:
        return "cel"
    elif "livret" in product or "épargne" in product:
        return "csl"
    return "ccp"


# ─── TRANSACTIONS ─────────────────────────────────────────

def get_account_transactions(account_id: str, date_from: str = None, date_to: str = None) -> list:
    """Récupère les transactions d'un compte (max 90 jours)."""
    headers = _headers()
    if not headers:
        return []

    if not date_from:
        date_from = (date.today() - timedelta(days=89)).isoformat()
    if not date_to:
        date_to = date.today().isoformat()

    try:
        resp = requests.get(
            f"{GOCARDLESS_BASE}/accounts/{account_id}/transactions/",
            headers=headers, timeout=15,
            params={"date_from": date_from, "date_to": date_to},
        )
        data = resp.json()
        transactions = data.get("transactions", {})
        booked = transactions.get("booked", [])

        result = []
        for tx in booked:
            amount = float(tx.get("transactionAmount", {}).get("amount", 0))
            result.append({
                "date": tx.get("bookingDate") or tx.get("valueDate", ""),
                "libelle": tx.get("remittanceInformationUnstructured")
                           or tx.get("remittanceInformationUnstructuredArray", [""])[0]
                           or tx.get("creditorName")
                           or tx.get("debtorName")
                           or "Transaction",
                "montant": amount,
                "reference": tx.get("transactionId") or tx.get("internalTransactionId", ""),
                "source": "api_bancaire",
            })

        result.sort(key=lambda t: t["date"], reverse=True)
        return result
    except Exception as e:
        logger.error(f"Transactions error: {e}")
        return []


# ─── SYNC COMPLÈTE ────────────────────────────────────────

def sync_all_accounts(requisition_id: str) -> list:
    """
    Synchronise tous les comptes d'une connexion bancaire.
    Retourne la liste des comptes avec soldes et transactions.
    """
    status = get_requisition_status(requisition_id)
    if "error" in status:
        return [status]

    if status.get("status") != "LN":  # LN = linked
        return [{"error": f"Connexion pas encore active. Statut: {status.get('status')}"}]

    accounts = []
    for account_id in status.get("accounts", []):
        details = get_account_details(account_id)
        if "error" in details:
            continue

        transactions = get_account_transactions(account_id)
        details["transactions"] = transactions
        details["nb_transactions"] = len(transactions)
        accounts.append(details)

    return accounts
