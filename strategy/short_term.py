"""
Stratégie court terme : scoring multi-critères pour Revolut.
Génère des signaux BUY / SELL / HOLD avec un score de confiance.
"""

from typing import List, Dict, Optional
from config.settings import SHORT_TERM_CONFIG as CFG
from strategy.indicators import rsi, sma, ema, macd, bollinger_bands, momentum, volume_ratio


def analyze_asset(data: dict) -> dict:
    """
    Analyse technique complète d'un actif.
    Retourne un signal (BUY/SELL/HOLD) avec score et justification.
    """
    closes = data.get("close", [])
    volumes = data.get("volume", [])
    symbol = data.get("symbol", "???")

    if len(closes) < 21:
        return {
            "symbol": symbol,
            "signal": "HOLD",
            "score": 0,
            "reason": "Données insuffisantes pour l'analyse",
        }

    # Calcul des indicateurs
    rsi_values = rsi(closes, CFG["rsi_period"])
    ma_fast = ema(closes, CFG["ma_fast"])
    ma_slow = ema(closes, CFG["ma_slow"])
    macd_data = macd(closes)
    bb = bollinger_bands(closes)
    mom = momentum(closes, CFG["momentum_days"])
    vol_ratio = volume_ratio(volumes) if volumes else [None] * len(closes)

    current_price = closes[-1]
    current_rsi = rsi_values[-1]
    current_ma_fast = ma_fast[-1]
    current_ma_slow = ma_slow[-1]
    current_macd = macd_data["macd"][-1]
    current_signal = macd_data["signal"][-1]
    current_histogram = macd_data["histogram"][-1]
    current_bb_upper = bb["upper"][-1]
    current_bb_lower = bb["lower"][-1]
    current_mom = mom[-1]
    current_vol_ratio = vol_ratio[-1]

    # --- Scoring multi-critères ---
    score = 0
    reasons = []

    # 1. RSI
    if current_rsi is not None:
        if current_rsi < CFG["rsi_oversold"]:
            score += 25
            reasons.append(f"RSI survendu ({current_rsi:.1f})")
        elif current_rsi > CFG["rsi_overbought"]:
            score -= 25
            reasons.append(f"RSI suracheté ({current_rsi:.1f})")
        elif current_rsi < 45:
            score += 10
            reasons.append(f"RSI favorable ({current_rsi:.1f})")
        elif current_rsi > 60:
            score -= 10

    # 2. Croisement moyennes mobiles
    if current_ma_fast is not None and current_ma_slow is not None:
        prev_ma_fast = ma_fast[-2] if len(ma_fast) > 1 else None
        prev_ma_slow = ma_slow[-2] if len(ma_slow) > 1 else None
        if prev_ma_fast and prev_ma_slow:
            if current_ma_fast > current_ma_slow and prev_ma_fast <= prev_ma_slow:
                score += 20
                reasons.append("Croisement haussier MA9/MA21")
            elif current_ma_fast < current_ma_slow and prev_ma_fast >= prev_ma_slow:
                score -= 20
                reasons.append("Croisement baissier MA9/MA21")
            elif current_ma_fast > current_ma_slow:
                score += 10
                reasons.append("Tendance haussière (MA9 > MA21)")
            else:
                score -= 10

    # 3. MACD
    if current_macd is not None and current_signal is not None:
        if current_histogram is not None:
            prev_hist = macd_data["histogram"][-2] if len(macd_data["histogram"]) > 1 else None
            if prev_hist is not None and prev_hist < 0 and current_histogram > 0:
                score += 15
                reasons.append("MACD croise au-dessus du signal")
            elif prev_hist is not None and prev_hist > 0 and current_histogram < 0:
                score -= 15
                reasons.append("MACD croise en-dessous du signal")

    # 4. Bollinger Bands
    if current_bb_lower is not None and current_bb_upper is not None:
        if current_price <= current_bb_lower:
            score += 15
            reasons.append("Prix sur bande Bollinger basse")
        elif current_price >= current_bb_upper:
            score -= 15
            reasons.append("Prix sur bande Bollinger haute")

    # 5. Momentum
    if current_mom is not None:
        if current_mom > 3:
            score += 10
            reasons.append(f"Momentum positif ({current_mom:.1f}%)")
        elif current_mom < -3:
            score -= 10
            reasons.append(f"Momentum négatif ({current_mom:.1f}%)")

    # 6. Volume
    if current_vol_ratio is not None:
        if current_vol_ratio > CFG["min_volume_ratio"] and score > 0:
            score += 10
            reasons.append(f"Volume élevé ({current_vol_ratio:.1f}x)")

    # --- Signal final ---
    if score >= 30:
        signal = "BUY"
    elif score <= -30:
        signal = "SELL"
    else:
        signal = "HOLD"

    return {
        "symbol": symbol,
        "signal": signal,
        "score": score,
        "price": round(current_price, 4),
        "rsi": round(current_rsi, 1) if current_rsi else None,
        "momentum_pct": round(current_mom, 2) if current_mom else None,
        "volume_ratio": round(current_vol_ratio, 2) if current_vol_ratio else None,
        "reasons": reasons,
    }


def scan_all_assets(market_data: Dict[str, dict]) -> List[dict]:
    """
    Scanne tous les actifs et retourne la liste triée par score.
    market_data: {symbol: data_dict}
    """
    results = []
    for symbol, data in market_data.items():
        analysis = analyze_asset(data)
        results.append(analysis)
    results.sort(key=lambda x: x["score"], reverse=True)
    return results


def get_buy_recommendations(scan_results: List[dict], budget: float, max_positions: int = 4) -> List[dict]:
    """
    Sélectionne les meilleures opportunités d'achat dans le budget.
    Diversification: max 4 positions, max 40% par position.
    """
    from config.settings import MAX_POSITION_PCT

    buys = [r for r in scan_results if r["signal"] == "BUY" and r["score"] >= 30]
    if not buys:
        # Fallback: prendre les meilleurs HOLD avec score positif
        buys = [r for r in scan_results if r["score"] > 10]

    recommendations = []
    remaining_budget = budget
    position_count = 0
    max_per_position = budget * MAX_POSITION_PCT

    for asset in buys[:max_positions]:
        if remaining_budget < 1 or position_count >= max_positions:
            break
        allocation = min(max_per_position, remaining_budget / (max_positions - position_count))
        allocation = round(allocation, 2)
        recommendations.append({
            **asset,
            "action": "BUY",
            "allocation_eur": allocation,
        })
        remaining_budget -= allocation
        position_count += 1

    return recommendations


def check_exit_signals(position: dict, current_data: dict) -> dict:
    """
    Vérifie si une position existante doit être vendue.
    Retourne le signal de sortie avec la raison.
    """
    entry_price = position.get("entry_price", 0)
    current_price = current_data.get("close", [0])[-1] if current_data.get("close") else 0
    highest_since_entry = position.get("highest_price", entry_price)

    if entry_price == 0:
        return {"action": "HOLD", "reason": "Prix d'entrée inconnu"}

    pnl_pct = ((current_price - entry_price) / entry_price) * 100
    drawdown_from_high = ((current_price - highest_since_entry) / highest_since_entry) * 100

    # Take profit
    if pnl_pct >= CFG["take_profit_pct"]:
        return {
            "action": "SELL",
            "reason": f"Take profit atteint (+{pnl_pct:.1f}%)",
            "pnl_pct": pnl_pct,
            "urgency": "HIGH",
        }

    # Stop loss
    if pnl_pct <= -CFG["stop_loss_pct"]:
        return {
            "action": "SELL",
            "reason": f"Stop loss déclenché ({pnl_pct:.1f}%)",
            "pnl_pct": pnl_pct,
            "urgency": "CRITICAL",
        }

    # Trailing stop
    if highest_since_entry > entry_price and drawdown_from_high <= -CFG["trailing_stop_pct"]:
        return {
            "action": "SELL",
            "reason": f"Trailing stop ({drawdown_from_high:.1f}% depuis le plus haut)",
            "pnl_pct": pnl_pct,
            "urgency": "HIGH",
        }

    # Analyse technique pour sortie
    analysis = analyze_asset(current_data)
    if analysis["signal"] == "SELL" and analysis["score"] <= -40:
        return {
            "action": "SELL",
            "reason": f"Signal technique de vente (score: {analysis['score']})",
            "pnl_pct": pnl_pct,
            "urgency": "MEDIUM",
        }

    return {
        "action": "HOLD",
        "reason": f"Position OK (P&L: {pnl_pct:+.1f}%)",
        "pnl_pct": pnl_pct,
    }
