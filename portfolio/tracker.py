"""
Suivi du portefeuille: positions, P&L, historique des trades.
Persistance JSON locale.
"""

import datetime
import json
import os
from typing import List, Dict, Optional


PORTFOLIO_FILE = "portfolio.json"


class PortfolioTracker:
    """Gestionnaire de portefeuille avec persistance locale."""

    def __init__(self, initial_budget: float = 100.0, filepath: str = None):
        self.filepath = filepath or PORTFOLIO_FILE
        self.data = self._load()
        if not self.data.get("initialized"):
            self.data = {
                "initialized": True,
                "initial_budget": initial_budget,
                "cash_eur": initial_budget,
                "positions": {},
                "trade_history": [],
                "created_at": datetime.datetime.now().isoformat(),
            }
            self._save()

    def buy(self, symbol: str, amount_eur: float, price: float,
            asset_class: str = "stocks_us", notes: str = "") -> dict:
        """Enregistre un achat."""
        if amount_eur > self.data["cash_eur"]:
            return {"error": f"Cash insuffisant: {self.data['cash_eur']:.2f}€ dispo, {amount_eur:.2f}€ demandé"}

        quantity = amount_eur / price if price > 0 else 0

        if symbol in self.data["positions"]:
            pos = self.data["positions"][symbol]
            total_cost = pos["entry_price"] * pos["quantity"] + amount_eur
            pos["quantity"] += quantity
            pos["entry_price"] = total_cost / pos["quantity"]
            pos["invested_eur"] += amount_eur
        else:
            self.data["positions"][symbol] = {
                "symbol": symbol,
                "quantity": quantity,
                "entry_price": price,
                "invested_eur": amount_eur,
                "asset_class": asset_class,
                "highest_price": price,
                "bought_at": datetime.datetime.now().isoformat(),
            }

        self.data["cash_eur"] -= amount_eur
        self.data["cash_eur"] = round(self.data["cash_eur"], 2)

        trade = {
            "action": "BUY",
            "symbol": symbol,
            "quantity": quantity,
            "price": price,
            "amount_eur": amount_eur,
            "timestamp": datetime.datetime.now().isoformat(),
            "notes": notes,
        }
        self.data["trade_history"].append(trade)
        self._save()

        return {
            "status": "OK",
            "action": "BUY",
            "symbol": symbol,
            "quantity": round(quantity, 6),
            "price": price,
            "amount_eur": amount_eur,
            "cash_remaining": self.data["cash_eur"],
        }

    def sell(self, symbol: str, price: float, notes: str = "") -> dict:
        """Vend la totalité d'une position."""
        if symbol not in self.data["positions"]:
            return {"error": f"Pas de position sur {symbol}"}

        pos = self.data["positions"][symbol]
        sell_value = pos["quantity"] * price
        pnl = sell_value - pos["invested_eur"]
        pnl_pct = (pnl / pos["invested_eur"]) * 100 if pos["invested_eur"] > 0 else 0

        trade = {
            "action": "SELL",
            "symbol": symbol,
            "quantity": pos["quantity"],
            "price": price,
            "amount_eur": round(sell_value, 2),
            "pnl_eur": round(pnl, 2),
            "pnl_pct": round(pnl_pct, 2),
            "timestamp": datetime.datetime.now().isoformat(),
            "notes": notes,
        }
        self.data["trade_history"].append(trade)
        self.data["cash_eur"] += round(sell_value, 2)
        del self.data["positions"][symbol]
        self._save()

        return {
            "status": "OK",
            "action": "SELL",
            "symbol": symbol,
            "sell_value_eur": round(sell_value, 2),
            "pnl_eur": round(pnl, 2),
            "pnl_pct": round(pnl_pct, 2),
            "cash_after": self.data["cash_eur"],
        }

    def update_highest_price(self, symbol: str, current_price: float):
        """Met à jour le plus haut prix pour le trailing stop."""
        if symbol in self.data["positions"]:
            pos = self.data["positions"][symbol]
            if current_price > pos.get("highest_price", 0):
                pos["highest_price"] = current_price
                self._save()

    def get_position(self, symbol: str) -> Optional[dict]:
        """Récupère une position."""
        return self.data["positions"].get(symbol)

    def get_all_positions(self) -> Dict[str, dict]:
        """Retourne toutes les positions."""
        return self.data["positions"]

    def get_portfolio_value(self, current_prices: Dict[str, float]) -> dict:
        """Calcule la valeur totale du portefeuille."""
        total_invested = 0
        total_current = 0
        positions_detail = []

        for symbol, pos in self.data["positions"].items():
            price = current_prices.get(symbol, pos["entry_price"])
            current_value = pos["quantity"] * price
            pnl = current_value - pos["invested_eur"]
            pnl_pct = (pnl / pos["invested_eur"]) * 100 if pos["invested_eur"] > 0 else 0

            positions_detail.append({
                "symbol": symbol,
                "invested": round(pos["invested_eur"], 2),
                "current_value": round(current_value, 2),
                "pnl_eur": round(pnl, 2),
                "pnl_pct": round(pnl_pct, 2),
                "weight_pct": 0,  # Calculé après
            })
            total_invested += pos["invested_eur"]
            total_current += current_value

        total_portfolio = total_current + self.data["cash_eur"]
        for p in positions_detail:
            p["weight_pct"] = round((p["current_value"] / total_portfolio) * 100, 1) if total_portfolio > 0 else 0

        total_pnl = total_portfolio - self.data["initial_budget"]

        return {
            "total_value_eur": round(total_portfolio, 2),
            "cash_eur": self.data["cash_eur"],
            "invested_eur": round(total_invested, 2),
            "positions_value_eur": round(total_current, 2),
            "total_pnl_eur": round(total_pnl, 2),
            "total_pnl_pct": round((total_pnl / self.data["initial_budget"]) * 100, 2),
            "positions": positions_detail,
            "num_positions": len(positions_detail),
        }

    def get_trade_history(self) -> List[dict]:
        """Retourne l'historique des trades."""
        return self.data["trade_history"]

    def get_cash(self) -> float:
        """Cash disponible."""
        return self.data["cash_eur"]

    def _load(self) -> dict:
        """Charge le portefeuille depuis le fichier."""
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        return {}

    def _save(self):
        """Sauvegarde le portefeuille."""
        with open(self.filepath, "w") as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)
