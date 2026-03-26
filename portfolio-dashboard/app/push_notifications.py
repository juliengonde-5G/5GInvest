"""
Notifications push Web Push (VAPID) pour le dashboard.
Alertes: arbitrages, objectifs atteints, variations fortes.
"""

import os
import json
import logging
from datetime import datetime
from pywebpush import webpush, WebPushException
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization
import base64

logger = logging.getLogger(__name__)

VAPID_FILE = os.path.join(os.path.dirname(__file__), "data", "vapid_keys.json")
SUBS_FILE = os.path.join(os.path.dirname(__file__), "data", "push_subs.json")

os.makedirs(os.path.dirname(VAPID_FILE), exist_ok=True)


def _load_vapid():
    if os.path.exists(VAPID_FILE):
        with open(VAPID_FILE) as f:
            return json.load(f)
    # Générer
    private_key = ec.generate_private_key(ec.SECP256R1())
    priv_bytes = private_key.private_numbers().private_value.to_bytes(32, "big")
    pub_bytes = private_key.public_key().public_bytes(
        serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint,
    )
    keys = {
        "public_key": base64.urlsafe_b64encode(pub_bytes).rstrip(b"=").decode(),
        "private_key": base64.urlsafe_b64encode(priv_bytes).rstrip(b"=").decode(),
        "contact": "mailto:admin@5ginvest.fr",
    }
    with open(VAPID_FILE, "w") as f:
        json.dump(keys, f, indent=2)
    return keys


VAPID_KEYS = _load_vapid()


def get_public_key():
    return VAPID_KEYS["public_key"]


def _load_subs():
    if os.path.exists(SUBS_FILE):
        with open(SUBS_FILE) as f:
            return json.load(f)
    return []


def _save_subs(subs):
    with open(SUBS_FILE, "w") as f:
        json.dump(subs, f, indent=2)


def subscribe(subscription_info: dict):
    subs = _load_subs()
    for s in subs:
        if s.get("endpoint") == subscription_info.get("endpoint"):
            return
    subs.append(subscription_info)
    _save_subs(subs)


def send_push(title: str, body: str, url: str = "/", tag: str = "default"):
    """Envoie une notification push à tous les abonnés."""
    subs = _load_subs()
    payload = json.dumps({"title": title, "body": body, "url": url, "tag": tag})
    sent = 0
    expired = []

    for sub in subs:
        try:
            webpush(
                subscription_info=sub, data=payload,
                vapid_private_key=VAPID_KEYS["private_key"],
                vapid_claims={"sub": VAPID_KEYS["contact"]},
            )
            sent += 1
        except WebPushException as e:
            if "410" in str(e) or "404" in str(e):
                expired.append(sub.get("endpoint"))
        except Exception as e:
            logger.error(f"Push error: {e}")

    if expired:
        subs = [s for s in subs if s.get("endpoint") not in expired]
        _save_subs(subs)

    return sent


# ─── Alertes spécifiques ──────────────────────────────────

def notify_arbitrage(path_name: str, symbol: str, action: str, raison: str):
    body = f"{action.upper()} {symbol}: {raison}"
    return send_push(f"Arbitrage - {path_name}", body, url="/invest", tag=f"arb-{symbol}")


def notify_objectif_atteint(path_name: str, objectif_type: str, symbol: str = None):
    if objectif_type == "take_profit":
        body = f"{symbol} a atteint l'objectif haut. Prenez vos gains."
    elif objectif_type == "stop_loss":
        body = f"{symbol} a franchi le stop loss. Coupez la position."
    else:
        body = f"Objectif du parcours atteint !"
    return send_push(f"Alerte - {path_name}", body, url="/invest", tag=f"obj-{symbol or 'path'}")


def notify_variation(symbol: str, variation_pct: float):
    direction = "hausse" if variation_pct > 0 else "baisse"
    body = f"{symbol}: {variation_pct:+.1f}% ({direction} importante)"
    return send_push(f"Mouvement - {symbol}", body, url="/invest", tag=f"var-{symbol}")
