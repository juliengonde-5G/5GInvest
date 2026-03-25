"""
Scheduler: surveillance automatique du portefeuille en arrière-plan.
Envoie des notifications push quand il faut agir.
Respecte les horaires France (07:30-22:00).
"""

import logging
import datetime
import time
from apscheduler.schedulers.background import BackgroundScheduler

from config.settings import ASSET_CLASSES, ALERT_CONFIG
from market.data_fetcher import fetch_stock_data, fetch_crypto_history, fetch_current_price
from strategy.short_term import analyze_asset, scan_all_assets, check_exit_signals
from alerts.alert_engine import AlertEngine
from portfolio.tracker import PortfolioTracker
from utils.time_guard import is_user_awake, can_trade_now
from api.push_service import PushService

logger = logging.getLogger(__name__)

push = PushService()
alert_engine = AlertEngine()


def check_portfolio():
    """
    Vérifie toutes les positions et envoie des alertes push si nécessaire.
    Appelé automatiquement toutes les 15 minutes.
    """
    now = datetime.datetime.now()
    logger.info(f"[{now.strftime('%H:%M')}] Vérification du portefeuille...")

    # Ne pas déranger la nuit (sauf alerte critique)
    if not is_user_awake():
        logger.info("Utilisateur hors fenêtre de trading. Report.")
        return

    portfolio = PortfolioTracker()
    positions = portfolio.get_all_positions()

    if not positions:
        return

    alerts_sent = 0

    for symbol, pos in positions.items():
        asset_class = pos.get("asset_class", "stocks_us")

        # Vérifier si le marché est ouvert
        can_act, reason = can_trade_now(asset_class)

        # Récupérer les données
        if asset_class == "crypto":
            data = fetch_crypto_history(symbol, days=14)
        else:
            data = fetch_stock_data(symbol, period="5d", interval="1h")

        if "error" in data or not data.get("close"):
            continue

        data["asset_class"] = asset_class
        current_price = data["close"][-1]

        # Mettre à jour le plus haut
        portfolio.update_highest_price(symbol, current_price)

        # Vérifier les signaux de sortie
        exit_signal = check_exit_signals(pos, data)

        if exit_signal["action"] == "SELL":
            pnl_pct = exit_signal.get("pnl_pct", 0)

            # Trouver un remplacement
            replacement_msg = _find_replacement(symbol)

            if can_act:
                # Notification immédiate - l'utilisateur peut agir maintenant
                push.send_trade_alert(
                    symbol=symbol,
                    action="SELL",
                    reason=exit_signal["reason"],
                    pnl_pct=pnl_pct,
                    replacement=replacement_msg,
                )
                logger.info(f"ALERTE SELL envoyée: {symbol} ({exit_signal['reason']})")
            else:
                # Marché fermé - mettre en file d'attente
                alert_engine.create_alert(
                    alert_type="EXIT_SIGNAL",
                    symbol=symbol,
                    message=exit_signal["reason"],
                    urgency=exit_signal.get("urgency", "HIGH"),
                    action="SELL",
                    asset_class=asset_class,
                    data={"pnl_pct": pnl_pct, "replacement": replacement_msg},
                )
                logger.info(f"Alerte SELL en file d'attente: {symbol} (marché fermé)")

            alerts_sent += 1

        # Alerte si gros mouvement de prix
        entry_price = pos.get("entry_price", 0)
        if entry_price > 0:
            move_pct = ((current_price - entry_price) / entry_price) * 100
            threshold = ALERT_CONFIG["price_change_alert_pct"]

            if abs(move_pct) > threshold * 2:
                direction = "hausse" if move_pct > 0 else "baisse"
                push.send_trade_alert(
                    symbol=symbol,
                    action="HOLD",
                    reason=f"Mouvement important: {move_pct:+.1f}% ({direction})",
                    pnl_pct=move_pct,
                )
                alerts_sent += 1

        time.sleep(0.3)

    # Libérer les alertes en file d'attente
    released = alert_engine.check_pending_alerts()
    for alert in released:
        push.send_trade_alert(
            symbol=alert["symbol"],
            action=alert.get("action", "INFO"),
            reason=f"[DIFFÉRÉ] {alert['message']}",
            pnl_pct=alert.get("data", {}).get("pnl_pct"),
            replacement=alert.get("data", {}).get("replacement"),
        )

    if alerts_sent > 0:
        logger.info(f"{alerts_sent} alerte(s) envoyée(s)")


def morning_briefing():
    """
    Briefing matinal envoyé à 08:00.
    Résumé des marchés + état du portefeuille + alertes en attente.
    """
    now = datetime.datetime.now()
    if now.weekday() >= 5:
        # Weekend: briefing light
        push.send_market_alert(
            "Bon weekend ! Marchés actions fermés. "
            "Seules les cryptos bougent. Prochain briefing lundi."
        )
        return

    portfolio = PortfolioTracker()
    positions = portfolio.get_all_positions()
    pending = alert_engine.get_summary()

    lines = ["Bonjour ! Briefing du jour:"]

    if positions:
        # Récupérer la valeur du portefeuille
        prices = {}
        for sym, pos in positions.items():
            p = fetch_current_price(sym, pos.get("asset_class", "stocks_us"))
            if p:
                prices[sym] = p

        pf = portfolio.get_portfolio_value(prices)
        lines.append(
            f"Portefeuille: {pf['total_value_eur']:.2f}EUR "
            f"(P&L: {pf['total_pnl_eur']:+.2f}EUR)"
        )

    if pending["pending_count"] > 0:
        lines.append(f"{pending['pending_count']} alerte(s) en attente de la nuit !")

    push.send_notification(
        title="5GInvest - Briefing",
        body="\n".join(lines),
        data={"url": "/"},
        tag="briefing",
    )


def _find_replacement(sold_symbol: str) -> str:
    """Trouve un remplacement rapide."""
    try:
        from market.data_fetcher import fetch_stock_data, fetch_crypto_history
        all_data = {}
        # Scan rapide sur les principaux actifs
        quick_symbols = [
            ("NVDA", "stocks_us"), ("TSLA", "stocks_us"), ("BTC", "crypto"),
            ("ETH", "crypto"), ("CSPX.AS", "etf"), ("EQQQ.DE", "etf"),
        ]
        for sym, ac in quick_symbols:
            if sym == sold_symbol:
                continue
            if ac == "crypto":
                d = fetch_crypto_history(sym, days=14)
            else:
                d = fetch_stock_data(sym, period="14d", interval="1d")
            if "error" not in d:
                d["asset_class"] = ac
                all_data[sym] = d
            time.sleep(0.2)

        results = scan_all_assets(all_data)
        buys = [r for r in results if r["signal"] == "BUY" and r["symbol"] != sold_symbol]
        if buys:
            return f"{buys[0]['symbol']} (score: {buys[0]['score']})"
    except Exception as e:
        logger.error(f"Erreur remplacement: {e}")

    return "Garder en cash"


def start_scheduler() -> BackgroundScheduler:
    """Démarre le scheduler APScheduler."""
    scheduler = BackgroundScheduler()

    interval = ALERT_CONFIG.get("check_interval_minutes", 15)

    # Vérification portefeuille toutes les 15 min
    scheduler.add_job(
        check_portfolio,
        "interval",
        minutes=interval,
        id="check_portfolio",
        name="Surveillance portefeuille",
        misfire_grace_time=300,
    )

    # Briefing matinal à 08:00
    scheduler.add_job(
        morning_briefing,
        "cron",
        hour=8,
        minute=0,
        id="morning_briefing",
        name="Briefing matinal",
    )

    scheduler.start()
    logger.info(f"Scheduler démarré: vérification toutes les {interval} min")
    return scheduler
