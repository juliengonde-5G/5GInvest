"""
Récupération des prix live: crypto (CoinGecko), commodities (Alpha Vantage), EUR/USD.
"""

import os
import json
import time
import requests
from functools import lru_cache

ALPHA_VANTAGE_KEY = os.environ.get("ALPHA_VANTAGE_KEY", "")

# Cache simple en mémoire (TTL géré manuellement)
_cache = {}
CACHE_TTL = 300  # 5 minutes


def _cached(key, ttl=CACHE_TTL):
    """Retourne la valeur en cache si encore valide."""
    entry = _cache.get(key)
    if entry and time.time() - entry["t"] < ttl:
        return entry["v"]
    return None


def _set_cache(key, value):
    _cache[key] = {"v": value, "t": time.time()}


# ─── CRYPTO (CoinGecko) ──────────────────────────────────

COINGECKO_MAP = {
    "BTC": "bitcoin", "ETH": "ethereum", "SOL": "solana",
    "XRP": "ripple", "ADA": "cardano", "DOT": "polkadot",
    "AVAX": "avalanche-2", "MATIC": "matic-network", "DOGE": "dogecoin",
    "LINK": "chainlink", "UNI": "uniswap", "ATOM": "cosmos",
    "BNB": "binancecoin", "LTC": "litecoin",
}


def get_crypto_prices(symbols: list) -> dict:
    """Récupère les prix crypto en EUR via CoinGecko."""
    cached = _cached("crypto_prices")
    if cached:
        return {s: cached.get(COINGECKO_MAP.get(s, s.lower()), {}).get("eur") for s in symbols}

    ids = ",".join(COINGECKO_MAP.get(s, s.lower()) for s in symbols)
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={ids}&vs_currencies=eur&include_24hr_change=true"

    try:
        resp = requests.get(url, timeout=10, headers={"Accept": "application/json"})
        data = resp.json()
        _set_cache("crypto_prices", data)

        result = {}
        for sym in symbols:
            cg_id = COINGECKO_MAP.get(sym, sym.lower())
            info = data.get(cg_id, {})
            result[sym] = info.get("eur")
        return result
    except Exception as e:
        return {s: None for s in symbols}


def get_crypto_price(symbol: str) -> float:
    """Prix unique d'une crypto."""
    prices = get_crypto_prices([symbol])
    return prices.get(symbol)


# ─── COMMODITIES (Alpha Vantage) ─────────────────────────

COMMODITY_SYMBOLS = {
    "GOLD": {"av_func": "CURRENCY_EXCHANGE_RATE", "from": "XAU", "to": "EUR", "nom": "Or (once)"},
    "SILVER": {"av_func": "CURRENCY_EXCHANGE_RATE", "from": "XAG", "to": "EUR", "nom": "Argent (once)"},
    "OIL": {"av_func": "GLOBAL_QUOTE", "symbol": "CL=F", "nom": "Pétrole WTI (baril)"},
}


def get_commodity_price(symbol: str) -> float:
    """Récupère le prix d'une matière première."""
    cached = _cached(f"commodity_{symbol}")
    if cached is not None:
        return cached

    info = COMMODITY_SYMBOLS.get(symbol.upper())
    if not info or not ALPHA_VANTAGE_KEY:
        return _commodity_fallback(symbol)

    try:
        if info["av_func"] == "CURRENCY_EXCHANGE_RATE":
            url = (
                f"https://www.alphavantage.co/query?function=CURRENCY_EXCHANGE_RATE"
                f"&from_currency={info['from']}&to_currency={info['to']}"
                f"&apikey={ALPHA_VANTAGE_KEY}"
            )
            resp = requests.get(url, timeout=10)
            data = resp.json()
            rate = data.get("Realtime Currency Exchange Rate", {})
            price = float(rate.get("5. Exchange Rate", 0))
        else:
            url = (
                f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE"
                f"&symbol={info['symbol']}&apikey={ALPHA_VANTAGE_KEY}"
            )
            resp = requests.get(url, timeout=10)
            data = resp.json()
            quote = data.get("Global Quote", {})
            price = float(quote.get("05. price", 0))
            # Convertir USD → EUR approximatif
            eur_rate = get_eur_usd_rate()
            price = price / eur_rate if eur_rate else price

        _set_cache(f"commodity_{symbol}", price)
        return price
    except Exception:
        return _commodity_fallback(symbol)


def _commodity_fallback(symbol: str) -> float:
    """Fallback CoinGecko pour l'or."""
    if symbol.upper() == "GOLD":
        try:
            resp = requests.get(
                "https://api.coingecko.com/api/v3/simple/price?ids=pax-gold&vs_currencies=eur",
                timeout=10,
            )
            return resp.json().get("pax-gold", {}).get("eur")
        except Exception:
            pass
    return None


def get_commodity_prices(symbols: list) -> dict:
    """Récupère les prix de plusieurs commodities."""
    return {s: get_commodity_price(s) for s in symbols}


# ─── EUR/USD ──────────────────────────────────────────────

def get_eur_usd_rate() -> float:
    """Récupère le taux EUR/USD."""
    cached = _cached("eur_usd", ttl=600)
    if cached:
        return cached

    try:
        resp = requests.get(
            "https://api.coingecko.com/api/v3/simple/price?ids=tether&vs_currencies=eur",
            timeout=10,
        )
        rate = 1 / resp.json().get("tether", {}).get("eur", 0.92)
        _set_cache("eur_usd", rate)
        return round(rate, 4)
    except Exception:
        return 1.08  # fallback
