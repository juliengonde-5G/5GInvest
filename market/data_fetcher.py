"""
Récupération des données de marché via APIs gratuites.
Sources: yfinance (stocks/ETF) + CoinGecko (crypto)
"""

import datetime
import json
import urllib.request
import urllib.error
from typing import Optional


def fetch_stock_data(symbol: str, period: str = "1mo", interval: str = "1d") -> dict:
    """
    Récupère les données historiques d'un titre via yfinance.
    Retourne un dict avec: dates, open, high, low, close, volume.
    """
    try:
        import yfinance as yf
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=period, interval=interval)
        if hist.empty:
            return {"error": f"Pas de données pour {symbol}", "symbol": symbol}
        return {
            "symbol": symbol,
            "dates": [d.strftime("%Y-%m-%d") for d in hist.index],
            "open": hist["Open"].tolist(),
            "high": hist["High"].tolist(),
            "low": hist["Low"].tolist(),
            "close": hist["Close"].tolist(),
            "volume": hist["Volume"].tolist(),
            "current_price": round(hist["Close"].iloc[-1], 4),
            "currency": _get_currency(symbol),
        }
    except Exception as e:
        return {"error": str(e), "symbol": symbol}


def fetch_crypto_price(symbol: str) -> dict:
    """
    Récupère le prix actuel d'une crypto via CoinGecko API (gratuit, sans clé).
    """
    coin_map = {
        "BTC": "bitcoin", "ETH": "ethereum", "SOL": "solana",
        "XRP": "ripple", "DOGE": "dogecoin", "ADA": "cardano",
        "AVAX": "avalanche-2", "MATIC": "matic-network",
    }
    coin_id = coin_map.get(symbol.upper())
    if not coin_id:
        return {"error": f"Crypto inconnue: {symbol}", "symbol": symbol}

    url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=eur&include_24hr_change=true&include_24hr_vol=true"
    try:
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
        info = data.get(coin_id, {})
        return {
            "symbol": symbol,
            "price_eur": info.get("eur"),
            "change_24h_pct": info.get("eur_24h_change"),
            "volume_24h_eur": info.get("eur_24h_vol"),
        }
    except Exception as e:
        return {"error": str(e), "symbol": symbol}


def fetch_crypto_history(symbol: str, days: int = 30) -> dict:
    """
    Récupère l'historique crypto via CoinGecko pour l'analyse technique.
    """
    coin_map = {
        "BTC": "bitcoin", "ETH": "ethereum", "SOL": "solana",
        "XRP": "ripple", "DOGE": "dogecoin", "ADA": "cardano",
        "AVAX": "avalanche-2", "MATIC": "matic-network",
    }
    coin_id = coin_map.get(symbol.upper())
    if not coin_id:
        return {"error": f"Crypto inconnue: {symbol}", "symbol": symbol}

    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart?vs_currency=eur&days={days}&interval=daily"
    try:
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
        prices = data.get("prices", [])
        volumes = data.get("total_volumes", [])
        return {
            "symbol": symbol,
            "dates": [datetime.datetime.fromtimestamp(p[0] / 1000).strftime("%Y-%m-%d") for p in prices],
            "close": [p[1] for p in prices],
            "volume": [v[1] for v in volumes],
            "current_price": prices[-1][1] if prices else None,
            "currency": "EUR",
        }
    except Exception as e:
        return {"error": str(e), "symbol": symbol}


def fetch_current_price(symbol: str, asset_class: str = "stocks") -> Optional[float]:
    """
    Récupère le prix actuel d'un actif. Retourne le prix en EUR ou None.
    """
    if asset_class == "crypto":
        data = fetch_crypto_price(symbol)
        return data.get("price_eur")
    else:
        data = fetch_stock_data(symbol, period="1d", interval="1m")
        if "error" not in data and data.get("close"):
            price = data["close"][-1]
            currency = data.get("currency", "EUR")
            if currency == "USD":
                rate = _get_eur_usd_rate()
                return round(price / rate, 4) if rate else price
            return round(price, 4)
    return None


def _get_currency(symbol: str) -> str:
    """Détermine la devise d'un symbole."""
    if symbol.endswith((".AS", ".DE", ".PA")):
        return "EUR"
    return "USD"


def _get_eur_usd_rate() -> Optional[float]:
    """Récupère le taux EUR/USD via yfinance."""
    try:
        import yfinance as yf
        ticker = yf.Ticker("EURUSD=X")
        hist = ticker.history(period="1d")
        if not hist.empty:
            return round(hist["Close"].iloc[-1], 4)
    except Exception:
        pass
    return 1.08  # Fallback approximatif
