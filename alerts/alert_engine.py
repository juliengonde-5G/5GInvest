"""
Moteur d'alertes: surveille le portefeuille et génère des alertes actionnables.
Respecte les contraintes horaires France.
"""

import datetime
import json
import os
import time
from typing import List, Dict

from config.settings import ALERT_CONFIG, ASSET_CLASSES
from utils.time_guard import can_trade_now, is_user_awake, next_trading_window


class AlertEngine:
    """Moteur d'alertes pour le suivi du portefeuille."""

    URGENCY_EMOJI = {
        "CRITICAL": "[!!!]",
        "HIGH": "[!!]",
        "MEDIUM": "[!]",
        "LOW": "[i]",
    }

    def __init__(self, log_file: str = None):
        self.log_file = log_file or ALERT_CONFIG.get("log_file", "alerts.log")
        self.pending_alerts: List[dict] = []  # Alertes en attente (hors horaires)
        self.sent_alerts: List[dict] = []

    def create_alert(self, alert_type: str, symbol: str, message: str,
                     urgency: str = "MEDIUM", action: str = None,
                     asset_class: str = "stocks_us", data: dict = None) -> dict:
        """
        Crée une alerte. Si l'utilisateur dort, la met en file d'attente.
        """
        alert = {
            "timestamp": datetime.datetime.now().isoformat(),
            "type": alert_type,
            "symbol": symbol,
            "message": message,
            "urgency": urgency,
            "action": action,
            "asset_class": asset_class,
            "data": data or {},
        }

        can_trade, reason = can_trade_now(asset_class)

        if not is_user_awake():
            alert["status"] = "QUEUED"
            alert["queue_reason"] = reason
            alert["next_window"] = next_trading_window(asset_class)
            self.pending_alerts.append(alert)
            self._log(alert, queued=True)
            return alert

        if action == "SELL" and not can_trade:
            # On peut pas vendre maintenant - mettre en attente
            alert["status"] = "QUEUED_MARKET_CLOSED"
            alert["queue_reason"] = reason
            alert["next_window"] = next_trading_window(asset_class)
            self.pending_alerts.append(alert)
            self._log(alert, queued=True)
        else:
            alert["status"] = "SENT"
            self.sent_alerts.append(alert)
            self._log(alert, queued=False)
            self._display(alert)

        return alert

    def check_pending_alerts(self) -> List[dict]:
        """
        Vérifie et envoie les alertes en file d'attente quand c'est possible.
        À appeler régulièrement.
        """
        if not is_user_awake():
            return []

        released = []
        still_pending = []

        for alert in self.pending_alerts:
            can_trade, _ = can_trade_now(alert.get("asset_class", "stocks_us"))
            if can_trade or alert.get("urgency") == "CRITICAL":
                alert["status"] = "SENT"
                alert["released_at"] = datetime.datetime.now().isoformat()
                self.sent_alerts.append(alert)
                self._display(alert, was_queued=True)
                released.append(alert)
            else:
                still_pending.append(alert)

        self.pending_alerts = still_pending
        return released

    def _display(self, alert: dict, was_queued: bool = False):
        """Affiche une alerte en console."""
        prefix = self.URGENCY_EMOJI.get(alert.get("urgency", "MEDIUM"), "[?]")
        queued_tag = " (FILE D'ATTENTE)" if was_queued else ""

        print(f"\n{'='*60}")
        print(f"{prefix} ALERTE {alert['type'].upper()}{queued_tag}")
        print(f"{'='*60}")
        print(f"  Actif:   {alert['symbol']}")
        print(f"  Action:  {alert.get('action', 'INFO')}")
        print(f"  Message: {alert['message']}")
        if alert.get("data", {}).get("pnl_pct") is not None:
            pnl = alert["data"]["pnl_pct"]
            print(f"  P&L:     {pnl:+.1f}%")
        if alert.get("data", {}).get("replacement"):
            print(f"  Remplacement suggéré: {alert['data']['replacement']}")
        if alert.get("next_window"):
            print(f"  Prochaine fenêtre: {alert['next_window']}")
        print(f"  Heure:   {alert['timestamp']}")
        print(f"{'='*60}\n")

    def _log(self, alert: dict, queued: bool = False):
        """Écrit l'alerte dans le fichier de log."""
        try:
            with open(self.log_file, "a") as f:
                status = "QUEUED" if queued else "SENT"
                f.write(f"[{alert['timestamp']}] [{status}] [{alert.get('urgency', '?')}] "
                        f"{alert['symbol']}: {alert['message']}\n")
        except Exception:
            pass

    def get_summary(self) -> dict:
        """Résumé de l'état des alertes."""
        return {
            "pending_count": len(self.pending_alerts),
            "sent_today": len([a for a in self.sent_alerts
                             if a["timestamp"][:10] == datetime.datetime.now().strftime("%Y-%m-%d")]),
            "pending_alerts": self.pending_alerts,
            "critical_pending": [a for a in self.pending_alerts if a.get("urgency") == "CRITICAL"],
        }

    def suggest_replacement(self, sold_symbol: str, scan_results: List[dict]) -> dict:
        """
        Après une vente, suggère le meilleur remplacement parmi les actifs scannés.
        """
        candidates = [r for r in scan_results
                      if r["symbol"] != sold_symbol
                      and r["signal"] == "BUY"
                      and r["score"] >= 20]

        if not candidates:
            candidates = [r for r in scan_results
                          if r["symbol"] != sold_symbol and r["score"] > 0]

        if candidates:
            best = candidates[0]
            return {
                "symbol": best["symbol"],
                "score": best["score"],
                "reasons": best.get("reasons", []),
                "message": f"Remplacer {sold_symbol} par {best['symbol']} (score: {best['score']})",
            }

        return {"symbol": None, "message": f"Pas de remplacement immédiat pour {sold_symbol}. Garder en cash."}
