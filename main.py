#!/usr/bin/env python3
"""
5GInvest - Module d'investissement guidé pour Revolut
Budget: 100€ | Stratégie: Court terme | Marché: France

Usage:
    python main.py scan          # Scanner les opportunités
    python main.py recommend     # Recommandation d'allocation 100€
    python main.py monitor       # Surveillance continue du portefeuille
    python main.py portfolio     # État du portefeuille
    python main.py buy SYMBOL    # Enregistrer un achat
    python main.py sell SYMBOL   # Enregistrer une vente
"""

import sys
import time
import datetime

from config.settings import (
    INITIAL_BUDGET_EUR, ASSET_CLASSES, ALERT_CONFIG, SHORT_TERM_CONFIG,
)
from market.data_fetcher import fetch_stock_data, fetch_crypto_history, fetch_current_price
from strategy.short_term import analyze_asset, scan_all_assets, get_buy_recommendations, check_exit_signals
from alerts.alert_engine import AlertEngine
from portfolio.tracker import PortfolioTracker
from utils.time_guard import can_trade_now, is_user_awake, next_trading_window


def print_header(title: str):
    print(f"\n{'='*60}")
    print(f"  5GInvest | {title}")
    print(f"  {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')} (Paris)")
    print(f"{'='*60}")


def fetch_all_market_data() -> dict:
    """Récupère les données de tous les actifs configurés."""
    all_data = {}
    total = sum(len(cfg["symbols"]) for cfg in ASSET_CLASSES.values() if cfg["enabled"])
    count = 0

    for asset_class, config in ASSET_CLASSES.items():
        if not config["enabled"]:
            continue
        for symbol in config["symbols"]:
            count += 1
            print(f"  [{count}/{total}] {symbol}...", end=" ", flush=True)
            if asset_class == "crypto":
                data = fetch_crypto_history(symbol, days=30)
            else:
                data = fetch_stock_data(symbol, period="1mo", interval="1d")

            if "error" not in data:
                data["asset_class"] = asset_class
                all_data[symbol] = data
                print("OK")
            else:
                print(f"SKIP ({data['error'][:40]})")
            time.sleep(0.3)  # Rate limiting

    return all_data


def cmd_scan():
    """Scanner les opportunités sur tous les actifs."""
    print_header("SCAN DES OPPORTUNITÉS")
    print("\nRécupération des données marché...")

    market_data = fetch_all_market_data()
    results = scan_all_assets(market_data)

    print(f"\n{'─'*60}")
    print(f"  {'Actif':<12} {'Signal':<8} {'Score':>6} {'Prix':>12} {'RSI':>6} {'Mom%':>8}  Raisons")
    print(f"{'─'*60}")

    for r in results:
        signal_color = {"BUY": "+", "SELL": "-", "HOLD": " "}.get(r["signal"], " ")
        rsi_str = f"{r['rsi']:.0f}" if r.get("rsi") else "N/A"
        mom_str = f"{r['momentum_pct']:.1f}" if r.get("momentum_pct") else "N/A"
        reasons_str = " | ".join(r.get("reasons", [])[:2])
        print(f" {signal_color}{r['symbol']:<11} {r['signal']:<8} {r['score']:>5} "
              f"{r.get('price', 0):>11.2f} {rsi_str:>6} {mom_str:>7}%  {reasons_str}")

    buys = [r for r in results if r["signal"] == "BUY"]
    sells = [r for r in results if r["signal"] == "SELL"]
    print(f"\n  Résumé: {len(buys)} BUY | {len(sells)} SELL | {len(results) - len(buys) - len(sells)} HOLD")

    return results, market_data


def cmd_recommend():
    """Recommandation d'allocation pour le budget initial."""
    print_header(f"RECOMMANDATION - BUDGET {INITIAL_BUDGET_EUR}€")

    results, market_data = cmd_scan()
    recommendations = get_buy_recommendations(results, INITIAL_BUDGET_EUR)

    print(f"\n{'='*60}")
    print(f"  ALLOCATION RECOMMANDÉE ({INITIAL_BUDGET_EUR}€)")
    print(f"{'='*60}")

    if not recommendations:
        print("\n  Pas de signal d'achat clair. Recommandation: attendre.")
        print("  Garder le cash et relancer le scan demain.\n")
        return

    total_allocated = 0
    for i, rec in enumerate(recommendations, 1):
        can_act, reason = can_trade_now(rec.get("asset_class", "stocks_us"))
        status = "ACTIONNABLE" if can_act else f"ATTENDRE ({reason})"
        total_allocated += rec["allocation_eur"]

        print(f"\n  {i}. {rec['symbol']}")
        print(f"     Action:     ACHETER {rec['allocation_eur']:.2f}€")
        print(f"     Prix:       {rec['price']:.4f}")
        print(f"     Score:      {rec['score']}")
        print(f"     Statut:     {status}")
        print(f"     Raisons:    {' | '.join(rec.get('reasons', []))}")
        print(f"     Stop loss:  -{SHORT_TERM_CONFIG['stop_loss_pct']}% ({rec['price'] * (1 - SHORT_TERM_CONFIG['stop_loss_pct']/100):.4f})")
        print(f"     Take profit: +{SHORT_TERM_CONFIG['take_profit_pct']}% ({rec['price'] * (1 + SHORT_TERM_CONFIG['take_profit_pct']/100):.4f})")

    cash_remaining = INITIAL_BUDGET_EUR - total_allocated
    print(f"\n  {'─'*40}")
    print(f"  Total alloué:    {total_allocated:.2f}€")
    print(f"  Cash restant:    {cash_remaining:.2f}€")
    print(f"\n  Rappel: Exécuter les achats manuellement sur Revolut.")
    print(f"  Puis enregistrer: python main.py buy SYMBOL")


def cmd_monitor():
    """Surveillance continue du portefeuille."""
    print_header("SURVEILLANCE CONTINUE")

    portfolio = PortfolioTracker()
    alert_engine = AlertEngine()
    positions = portfolio.get_all_positions()

    if not positions:
        print("\n  Aucune position enregistrée.")
        print("  Lancez d'abord: python main.py recommend")
        print("  Puis enregistrez vos achats: python main.py buy SYMBOL")
        return

    interval = ALERT_CONFIG["check_interval_minutes"]
    print(f"\n  Positions suivies: {len(positions)}")
    print(f"  Intervalle de vérification: {interval} min")
    print(f"  Ctrl+C pour arrêter\n")

    try:
        while True:
            now = datetime.datetime.now().strftime("%H:%M:%S")
            print(f"\n[{now}] Vérification en cours...")

            # Récupérer les alertes en attente
            released = alert_engine.check_pending_alerts()
            if released:
                print(f"  {len(released)} alerte(s) en attente libérée(s)")

            # Vérifier chaque position
            all_data = {}
            for symbol, pos in positions.items():
                asset_class = pos.get("asset_class", "stocks_us")
                if asset_class == "crypto":
                    data = fetch_crypto_history(symbol, days=14)
                else:
                    data = fetch_stock_data(symbol, period="5d", interval="1h")

                if "error" in data:
                    print(f"  {symbol}: Erreur données - {data['error'][:40]}")
                    continue

                data["asset_class"] = asset_class
                all_data[symbol] = data

                # Mettre à jour le plus haut
                if data.get("close"):
                    current_price = data["close"][-1]
                    portfolio.update_highest_price(symbol, current_price)

                    # Vérifier les signaux de sortie
                    exit_signal = check_exit_signals(pos, data)

                    if exit_signal["action"] == "SELL":
                        # Scanner pour trouver un remplacement
                        scan_data = fetch_all_market_data()
                        scan_results = scan_all_assets(scan_data)
                        replacement = alert_engine.suggest_replacement(symbol, scan_results)

                        alert_engine.create_alert(
                            alert_type="EXIT_SIGNAL",
                            symbol=symbol,
                            message=exit_signal["reason"],
                            urgency=exit_signal.get("urgency", "HIGH"),
                            action="SELL",
                            asset_class=asset_class,
                            data={
                                "pnl_pct": exit_signal.get("pnl_pct"),
                                "current_price": current_price,
                                "replacement": replacement.get("message"),
                            },
                        )
                    else:
                        print(f"  {symbol}: {exit_signal['reason']}")

                time.sleep(0.3)

            # Afficher résumé portefeuille
            prices = {}
            for sym, d in all_data.items():
                if d.get("close"):
                    prices[sym] = d["close"][-1]
            pf_value = portfolio.get_portfolio_value(prices)
            print(f"\n  Portefeuille: {pf_value['total_value_eur']:.2f}€ "
                  f"(P&L: {pf_value['total_pnl_eur']:+.2f}€ / {pf_value['total_pnl_pct']:+.1f}%)")

            alert_summary = alert_engine.get_summary()
            if alert_summary["pending_count"] > 0:
                print(f"  Alertes en attente: {alert_summary['pending_count']}")

            print(f"\n  Prochaine vérification dans {interval} min...")
            time.sleep(interval * 60)

    except KeyboardInterrupt:
        print("\n\n  Surveillance arrêtée.")


def cmd_portfolio():
    """Affiche l'état du portefeuille."""
    print_header("PORTEFEUILLE")

    portfolio = PortfolioTracker()
    positions = portfolio.get_all_positions()

    if not positions:
        print(f"\n  Cash: {portfolio.get_cash():.2f}€")
        print("  Aucune position ouverte.\n")
        return

    # Récupérer les prix actuels
    prices = {}
    for symbol, pos in positions.items():
        asset_class = pos.get("asset_class", "stocks_us")
        price = fetch_current_price(symbol, asset_class)
        if price:
            prices[symbol] = price
            portfolio.update_highest_price(symbol, price)

    pf = portfolio.get_portfolio_value(prices)

    print(f"\n  Valeur totale:  {pf['total_value_eur']:.2f}€")
    print(f"  Cash:           {pf['cash_eur']:.2f}€")
    print(f"  Investi:        {pf['invested_eur']:.2f}€")
    print(f"  P&L total:      {pf['total_pnl_eur']:+.2f}€ ({pf['total_pnl_pct']:+.1f}%)")
    print(f"\n  {'─'*50}")
    print(f"  {'Actif':<10} {'Investi':>8} {'Actuel':>8} {'P&L':>8} {'P&L%':>7} {'Poids':>6}")
    print(f"  {'─'*50}")

    for p in pf["positions"]:
        print(f"  {p['symbol']:<10} {p['invested']:>7.2f}€ {p['current_value']:>7.2f}€ "
              f"{p['pnl_eur']:>+7.2f}€ {p['pnl_pct']:>+6.1f}% {p['weight_pct']:>5.1f}%")

    # Historique
    history = portfolio.get_trade_history()
    if history:
        print(f"\n  Derniers trades:")
        for t in history[-5:]:
            print(f"    {t['timestamp'][:16]} {t['action']} {t['symbol']} "
                  f"{t['amount_eur']:.2f}€ @ {t['price']:.4f}")


def cmd_buy(symbol: str):
    """Enregistrer un achat effectué sur Revolut."""
    portfolio = PortfolioTracker()

    # Déterminer la classe d'actif
    asset_class = _find_asset_class(symbol)
    price = fetch_current_price(symbol, asset_class)

    if not price:
        print(f"\n  Impossible de récupérer le prix de {symbol}.")
        print("  Entrez le prix manuellement:")
        try:
            price = float(input("  Prix (EUR): "))
        except (ValueError, EOFError):
            print("  Prix invalide. Abandon.")
            return

    print(f"\n  {symbol} - Prix actuel: {price:.4f}€")
    print(f"  Cash disponible: {portfolio.get_cash():.2f}€")

    try:
        amount = float(input("  Montant à investir (EUR): "))
    except (ValueError, EOFError):
        print("  Montant invalide. Abandon.")
        return

    result = portfolio.buy(symbol, amount, price, asset_class)
    if "error" in result:
        print(f"\n  Erreur: {result['error']}")
    else:
        print(f"\n  Achat enregistré!")
        print(f"  {result['symbol']}: {result['quantity']:.6f} unités @ {result['price']:.4f}€")
        print(f"  Cash restant: {result['cash_remaining']:.2f}€")


def cmd_sell(symbol: str):
    """Enregistrer une vente effectuée sur Revolut."""
    portfolio = PortfolioTracker()
    pos = portfolio.get_position(symbol)

    if not pos:
        print(f"\n  Pas de position sur {symbol}.")
        return

    asset_class = pos.get("asset_class", "stocks_us")
    price = fetch_current_price(symbol, asset_class)

    if not price:
        print(f"\n  Impossible de récupérer le prix de {symbol}.")
        try:
            price = float(input("  Prix de vente (EUR): "))
        except (ValueError, EOFError):
            print("  Prix invalide. Abandon.")
            return

    print(f"\n  {symbol} - Prix actuel: {price:.4f}€")
    print(f"  Position: {pos['quantity']:.6f} unités, investi: {pos['invested_eur']:.2f}€")

    confirm = input("  Confirmer la vente? (o/n): ").strip().lower()
    if confirm != "o":
        print("  Vente annulée.")
        return

    result = portfolio.sell(symbol, price)
    if "error" in result:
        print(f"\n  Erreur: {result['error']}")
    else:
        print(f"\n  Vente enregistrée!")
        print(f"  {result['symbol']}: {result['sell_value_eur']:.2f}€")
        print(f"  P&L: {result['pnl_eur']:+.2f}€ ({result['pnl_pct']:+.1f}%)")
        print(f"  Cash après vente: {result['cash_after']:.2f}€")

        # Suggérer un remplacement
        print("\n  Recherche d'un remplacement...")
        market_data = fetch_all_market_data()
        results = scan_all_assets(market_data)
        alert_engine = AlertEngine()
        replacement = alert_engine.suggest_replacement(symbol, results)
        print(f"  {replacement['message']}")


def _find_asset_class(symbol: str) -> str:
    """Trouve la classe d'actif d'un symbole."""
    for asset_class, config in ASSET_CLASSES.items():
        if symbol.upper() in [s.upper() for s in config["symbols"]]:
            return asset_class
    return "stocks_us"


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    command = sys.argv[1].lower()

    if command == "scan":
        cmd_scan()
    elif command == "recommend":
        cmd_recommend()
    elif command == "monitor":
        cmd_monitor()
    elif command == "portfolio":
        cmd_portfolio()
    elif command == "buy":
        if len(sys.argv) < 3:
            print("Usage: python main.py buy SYMBOL")
            return
        cmd_buy(sys.argv[2].upper())
    elif command == "sell":
        if len(sys.argv) < 3:
            print("Usage: python main.py sell SYMBOL")
            return
        cmd_sell(sys.argv[2].upper())
    else:
        print(f"Commande inconnue: {command}")
        print(__doc__)


if __name__ == "__main__":
    main()
