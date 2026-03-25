"""
Service de notifications push Web Push (VAPID).
Envoie des alertes sur le téléphone Android via le Service Worker PWA.
"""

import json
import os
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)

from config.paths import SUBSCRIPTIONS_FILE, VAPID_FILE


class PushService:
    """Gère les abonnements push et l'envoi de notifications."""

    def __init__(self):
        self.subscriptions = self._load_subscriptions()
        self.vapid_keys = self._load_or_create_vapid()

    def get_public_key(self) -> str:
        """Retourne la clé publique VAPID pour le frontend."""
        return self.vapid_keys.get("public_key", "")

    def save_subscription(self, subscription: dict):
        """Enregistre un nouvel abonnement push."""
        # Éviter les doublons
        for existing in self.subscriptions:
            if existing.get("endpoint") == subscription.get("endpoint"):
                return
        self.subscriptions.append(subscription)
        self._save_subscriptions()
        logger.info(f"Nouvel abonnement push enregistré. Total: {len(self.subscriptions)}")

    def remove_subscription(self, endpoint: str):
        """Supprime un abonnement."""
        self.subscriptions = [s for s in self.subscriptions if s.get("endpoint") != endpoint]
        self._save_subscriptions()

    def send_notification(self, title: str, body: str, data: dict = None,
                          urgency: str = "normal", tag: str = None) -> int:
        """
        Envoie une notification à tous les abonnés.
        Retourne le nombre de notifications envoyées.
        """
        if not self.subscriptions:
            logger.warning("Aucun abonné push.")
            return 0

        payload = json.dumps({
            "title": title,
            "body": body,
            "data": data or {},
            "tag": tag or "5ginvest",
            "urgency": urgency,
            "timestamp": __import__("datetime").datetime.now().isoformat(),
        })

        sent = 0
        failed_endpoints = []

        try:
            from pywebpush import webpush, WebPushException
        except ImportError:
            logger.error("pywebpush non installé. pip install pywebpush")
            return 0

        vapid_claims = {
            "sub": self.vapid_keys.get("contact", "mailto:admin@5ginvest.local"),
        }

        for sub in self.subscriptions:
            try:
                webpush(
                    subscription_info=sub,
                    data=payload,
                    vapid_private_key=self.vapid_keys["private_key"],
                    vapid_claims=vapid_claims,
                )
                sent += 1
            except WebPushException as e:
                logger.warning(f"Erreur push: {e}")
                if "410" in str(e) or "404" in str(e):
                    failed_endpoints.append(sub.get("endpoint"))
            except Exception as e:
                logger.error(f"Erreur push inattendue: {e}")

        # Nettoyage des abonnements expirés
        if failed_endpoints:
            self.subscriptions = [
                s for s in self.subscriptions
                if s.get("endpoint") not in failed_endpoints
            ]
            self._save_subscriptions()

        logger.info(f"Notifications envoyées: {sent}/{len(self.subscriptions)}")
        return sent

    def send_trade_alert(self, symbol: str, action: str, reason: str,
                         pnl_pct: float = None, replacement: str = None):
        """Envoie une alerte de trading."""
        emoji = {"BUY": "BUY", "SELL": "SELL", "HOLD": "HOLD"}.get(action, "INFO")
        title = f"5GInvest [{emoji}] {symbol}"

        body = reason
        if pnl_pct is not None:
            body += f" (P&L: {pnl_pct:+.1f}%)"
        if replacement:
            body += f"\nRemplacement: {replacement}"

        urgency = "high" if action == "SELL" else "normal"

        return self.send_notification(
            title=title,
            body=body,
            data={
                "url": f"/portfolio",
                "action": action,
                "symbol": symbol,
            },
            urgency=urgency,
            tag=f"trade-{symbol}",
        )

    def send_market_alert(self, message: str):
        """Envoie une alerte marché."""
        return self.send_notification(
            title="5GInvest - Marché",
            body=message,
            data={"url": "/"},
            tag="market",
        )

    def _load_or_create_vapid(self) -> dict:
        """Charge ou génère les clés VAPID."""
        if os.path.exists(VAPID_FILE):
            try:
                with open(VAPID_FILE, "r") as f:
                    return json.load(f)
            except Exception:
                pass

        # Générer de nouvelles clés
        try:
            from py_vapid import Vapid
            vapid = Vapid()
            vapid.generate_keys()
            keys = {
                "public_key": vapid.public_key_urlsafe_base64,
                "private_key": vapid.private_key_urlsafe_base64,
                "contact": "mailto:admin@5ginvest.local",
            }
        except ImportError:
            # Fallback: clés placeholder (l'utilisateur devra les générer)
            logger.warning("py_vapid non installé. Générez les clés VAPID manuellement.")
            keys = {
                "public_key": "GENERATE_WITH_vapid_gen",
                "private_key": "GENERATE_WITH_vapid_gen",
                "contact": "mailto:admin@5ginvest.local",
            }

        with open(VAPID_FILE, "w") as f:
            json.dump(keys, f, indent=2)
        return keys

    def _load_subscriptions(self) -> list:
        if os.path.exists(SUBSCRIPTIONS_FILE):
            try:
                with open(SUBSCRIPTIONS_FILE, "r") as f:
                    return json.load(f)
            except Exception:
                pass
        return []

    def _save_subscriptions(self):
        with open(SUBSCRIPTIONS_FILE, "w") as f:
            json.dump(self.subscriptions, f, indent=2)
