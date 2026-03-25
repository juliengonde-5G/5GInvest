"""
Indicateurs techniques pour l'analyse court terme.
Implémentation pure Python (pas de dépendance lourde type TA-Lib).
"""

from typing import List, Optional


def sma(data: List[float], period: int) -> List[Optional[float]]:
    """Simple Moving Average."""
    result = [None] * len(data)
    for i in range(period - 1, len(data)):
        result[i] = sum(data[i - period + 1:i + 1]) / period
    return result


def ema(data: List[float], period: int) -> List[Optional[float]]:
    """Exponential Moving Average."""
    result = [None] * len(data)
    if len(data) < period:
        return result
    k = 2 / (period + 1)
    result[period - 1] = sum(data[:period]) / period
    for i in range(period, len(data)):
        result[i] = data[i] * k + result[i - 1] * (1 - k)
    return result


def rsi(closes: List[float], period: int = 14) -> List[Optional[float]]:
    """Relative Strength Index."""
    result = [None] * len(closes)
    if len(closes) < period + 1:
        return result

    gains = []
    losses = []
    for i in range(1, len(closes)):
        change = closes[i] - closes[i - 1]
        gains.append(max(change, 0))
        losses.append(max(-change, 0))

    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period

    if avg_loss == 0:
        result[period] = 100.0
    else:
        rs = avg_gain / avg_loss
        result[period] = 100 - (100 / (1 + rs))

    for i in range(period, len(gains)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
        if avg_loss == 0:
            result[i + 1] = 100.0
        else:
            rs = avg_gain / avg_loss
            result[i + 1] = 100 - (100 / (1 + rs))

    return result


def macd(closes: List[float], fast: int = 12, slow: int = 26, signal: int = 9) -> dict:
    """MACD (Moving Average Convergence Divergence)."""
    ema_fast = ema(closes, fast)
    ema_slow = ema(closes, slow)

    macd_line = [None] * len(closes)
    for i in range(len(closes)):
        if ema_fast[i] is not None and ema_slow[i] is not None:
            macd_line[i] = ema_fast[i] - ema_slow[i]

    macd_values = [v for v in macd_line if v is not None]
    signal_line_raw = ema(macd_values, signal) if macd_values else []

    signal_line = [None] * len(closes)
    offset = len(closes) - len(macd_values)
    for i, v in enumerate(signal_line_raw):
        if v is not None:
            signal_line[offset + i] = v

    histogram = [None] * len(closes)
    for i in range(len(closes)):
        if macd_line[i] is not None and signal_line[i] is not None:
            histogram[i] = macd_line[i] - signal_line[i]

    return {"macd": macd_line, "signal": signal_line, "histogram": histogram}


def bollinger_bands(closes: List[float], period: int = 20, std_dev: float = 2.0) -> dict:
    """Bandes de Bollinger."""
    middle = sma(closes, period)
    upper = [None] * len(closes)
    lower = [None] * len(closes)

    for i in range(period - 1, len(closes)):
        window = closes[i - period + 1:i + 1]
        mean = middle[i]
        variance = sum((x - mean) ** 2 for x in window) / period
        std = variance ** 0.5
        upper[i] = mean + std_dev * std
        lower[i] = mean - std_dev * std

    return {"upper": upper, "middle": middle, "lower": lower}


def momentum(closes: List[float], period: int = 5) -> List[Optional[float]]:
    """Momentum en pourcentage sur N jours."""
    result = [None] * len(closes)
    for i in range(period, len(closes)):
        if closes[i - period] != 0:
            result[i] = ((closes[i] - closes[i - period]) / closes[i - period]) * 100
    return result


def volume_ratio(volumes: List[float], period: int = 20) -> List[Optional[float]]:
    """Ratio volume actuel / moyenne volume sur N jours."""
    avg_vol = sma(volumes, period)
    result = [None] * len(volumes)
    for i in range(len(volumes)):
        if avg_vol[i] and avg_vol[i] > 0:
            result[i] = volumes[i] / avg_vol[i]
    return result
