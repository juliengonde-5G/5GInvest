"""
Configuration du module d'investissement guidé Revolut.
Budget: 100€ | Marché: Europe/Paris | Compte perso
"""

# --- Budget ---
INITIAL_BUDGET_EUR = 100.0
MAX_POSITION_PCT = 0.40  # Max 40% du portefeuille sur un seul actif
MIN_TRADE_EUR = 1.0  # Revolut permet les fractions dès 1€

# --- Contraintes horaires (Europe/Paris) ---
TIMEZONE = "Europe/Paris"
# Heures où l'utilisateur peut agir (pas de vente en pleine nuit)
TRADING_WINDOW_START = "07:30"  # Heure locale de début
TRADING_WINDOW_END = "22:00"   # Heure locale de fin
# Marchés US ouvrent à 15h30 Paris, ferment à 22h00
US_MARKET_OPEN_PARIS = "15:30"
US_MARKET_CLOSE_PARIS = "22:00"
# Marchés EU ouvrent à 09:00, ferment à 17:30
EU_MARKET_OPEN = "09:00"
EU_MARKET_CLOSE = "17:30"
# Crypto = 24/7 mais on respecte la fenêtre utilisateur
CRYPTO_ALWAYS_OPEN = True

# --- Produits disponibles sur Revolut ---
ASSET_CLASSES = {
    "crypto": {
        "enabled": True,
        "symbols": ["BTC", "ETH", "SOL", "XRP", "DOGE", "ADA", "AVAX", "MATIC"],
        "fees_pct": 1.49,  # Revolut standard plan
        "min_trade_eur": 1.0,
    },
    "stocks_us": {
        "enabled": True,
        "symbols": [
            "NVDA", "TSLA", "AAPL", "AMZN", "META", "MSFT", "GOOGL",
            "AMD", "PLTR", "COIN", "MARA", "RIOT", "SOFI",
        ],
        "fees_pct": 0.0,  # Revolut: 0 commission (1 trade/mois gratuit standard)
        "min_trade_eur": 1.0,
        "fractional": True,
    },
    "stocks_eu": {
        "enabled": True,
        "symbols": [
            "ASML.AS", "SAP.DE", "TTE.PA", "MC.PA", "AIR.PA",
            "SIE.DE", "BNP.PA", "SAN.PA",
        ],
        "fees_pct": 0.0,
        "min_trade_eur": 1.0,
        "fractional": True,
    },
    "etf": {
        "enabled": True,
        "symbols": [
            "IWDA.AS",   # iShares MSCI World
            "CSPX.AS",   # iShares S&P 500
            "EQQQ.DE",   # Invesco Nasdaq 100
            "IUIT.AS",   # iShares S&P 500 IT
            "IS3N.DE",   # iShares MSCI EM
            "XDWT.DE",   # Xtrackers MSCI World IT
        ],
        "fees_pct": 0.0,
        "min_trade_eur": 1.0,
        "fractional": True,
    },
    "commodities_etf": {
        "enabled": True,
        "symbols": [
            "IGLN.AS",  # iShares Physical Gold
            "PHAG.AS",  # WisdomTree Physical Silver
        ],
        "fees_pct": 0.0,
        "min_trade_eur": 1.0,
    },
}

# --- Stratégie court terme ---
SHORT_TERM_CONFIG = {
    "lookback_days": 14,          # Analyse sur 14 jours
    "rsi_period": 14,
    "rsi_oversold": 30,           # Signal achat si RSI < 30
    "rsi_overbought": 70,         # Signal vente si RSI > 70
    "ma_fast": 9,                 # Moyenne mobile rapide
    "ma_slow": 21,                # Moyenne mobile lente
    "take_profit_pct": 5.0,       # Prendre les gains à +5%
    "stop_loss_pct": 3.0,         # Couper les pertes à -3%
    "trailing_stop_pct": 2.5,     # Trailing stop à 2.5%
    "min_volume_ratio": 1.2,      # Volume > 1.2x moyenne = confirmation
    "momentum_days": 5,           # Momentum sur 5 jours
}

# --- Alertes ---
ALERT_CONFIG = {
    "check_interval_minutes": 15,  # Vérifier toutes les 15 min
    "price_change_alert_pct": 2.0, # Alerte si mouvement > 2%
    "console_output": True,
    "log_file": "alerts.log",
}

# --- API Sources (gratuites) ---
DATA_SOURCES = {
    "stocks": "yfinance",       # Yahoo Finance via yfinance
    "crypto": "coingecko",      # CoinGecko API gratuite
    "fallback": "yfinance",     # Fallback universel
}
