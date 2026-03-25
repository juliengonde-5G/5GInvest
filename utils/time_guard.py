"""
Gestion des contraintes horaires pour le trading.
Empêche les actions en dehors des heures actives (France).
"""

import datetime
from typing import Tuple
from config.settings import (
    TIMEZONE, TRADING_WINDOW_START, TRADING_WINDOW_END,
    US_MARKET_OPEN_PARIS, US_MARKET_CLOSE_PARIS,
    EU_MARKET_OPEN, EU_MARKET_CLOSE,
)


def _now_paris() -> datetime.datetime:
    """Heure actuelle à Paris (sans pytz, utilise zoneinfo si dispo)."""
    try:
        from zoneinfo import ZoneInfo
        return datetime.datetime.now(ZoneInfo(TIMEZONE))
    except ImportError:
        # Fallback: UTC+1 (hiver) ou UTC+2 (été) - approximation
        import time
        utc_now = datetime.datetime.utcnow()
        # Détection simplifiée heure d'été (dernier dimanche mars -> dernier dimanche octobre)
        month = utc_now.month
        if 4 <= month <= 10:
            offset = datetime.timedelta(hours=2)
        else:
            offset = datetime.timedelta(hours=1)
        return utc_now + offset


def _parse_time(t: str) -> datetime.time:
    """Parse 'HH:MM' en objet time."""
    h, m = map(int, t.split(":"))
    return datetime.time(h, m)


def is_user_awake() -> bool:
    """L'utilisateur est-il dans sa fenêtre de trading (07:30 - 22:00)?"""
    now = _now_paris()
    start = _parse_time(TRADING_WINDOW_START)
    end = _parse_time(TRADING_WINDOW_END)
    return start <= now.time() <= end


def is_market_open(market: str = "us") -> bool:
    """Vérifie si un marché est ouvert (heure de Paris)."""
    now = _now_paris()
    weekday = now.weekday()  # 0=lundi, 6=dimanche

    if market == "crypto":
        return True  # 24/7

    # Pas de bourse le weekend
    if weekday >= 5:
        return False

    if market == "us":
        return _parse_time(US_MARKET_OPEN_PARIS) <= now.time() <= _parse_time(US_MARKET_CLOSE_PARIS)
    elif market == "eu":
        return _parse_time(EU_MARKET_OPEN) <= now.time() <= _parse_time(EU_MARKET_CLOSE)

    return False


def can_trade_now(asset_class: str) -> Tuple[bool, str]:
    """
    Peut-on trader maintenant? Retourne (bool, raison).
    Combine: utilisateur éveillé + marché ouvert.
    """
    if not is_user_awake():
        next_open = TRADING_WINDOW_START
        return False, f"Hors fenêtre utilisateur. Prochaine ouverture: {next_open} (Paris)"

    if asset_class in ("crypto",):
        return True, "Crypto: marché 24/7, utilisateur disponible"

    if asset_class in ("stocks_us", "etf"):
        if is_market_open("us"):
            return True, "Marché US ouvert"
        return False, f"Marché US fermé. Ouverture: {US_MARKET_OPEN_PARIS} (Paris)"

    if asset_class == "stocks_eu":
        if is_market_open("eu"):
            return True, "Marché EU ouvert"
        return False, f"Marché EU fermé. Ouverture: {EU_MARKET_OPEN} (Paris)"

    if asset_class == "commodities_etf":
        if is_market_open("eu"):
            return True, "Marché EU ouvert (ETF commodities)"
        return False, f"Marché EU fermé. Ouverture: {EU_MARKET_OPEN} (Paris)"

    return True, "Classe d'actif non contrainte"


def next_trading_window(asset_class: str) -> str:
    """Retourne quand la prochaine fenêtre de trading sera ouverte."""
    now = _now_paris()
    weekday = now.weekday()

    if asset_class == "crypto":
        if is_user_awake():
            return "Maintenant"
        return f"Demain {TRADING_WINDOW_START} (Paris)"

    if weekday >= 5:
        days_until_monday = 7 - weekday
        next_day = now + datetime.timedelta(days=days_until_monday)
        if asset_class in ("stocks_us", "etf"):
            return f"Lundi {next_day.strftime('%d/%m')} à {US_MARKET_OPEN_PARIS} (Paris)"
        return f"Lundi {next_day.strftime('%d/%m')} à {EU_MARKET_OPEN} (Paris)"

    if asset_class in ("stocks_us", "etf"):
        if now.time() < _parse_time(US_MARKET_OPEN_PARIS):
            return f"Aujourd'hui {US_MARKET_OPEN_PARIS} (Paris)"
        return f"Demain {US_MARKET_OPEN_PARIS} (Paris)"

    if now.time() < _parse_time(EU_MARKET_OPEN):
        return f"Aujourd'hui {EU_MARKET_OPEN} (Paris)"
    return f"Demain {EU_MARKET_OPEN} (Paris)"
