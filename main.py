#!/usr/bin/env python3
"""
5GInvest - Module d'investissement guidé multi-banques

Usage:
    python main.py                     # Page d'accueil + note marché
    python main.py home                # Page d'accueil + note marché
    python main.py profile             # Configurer votre profil investisseur
    python main.py banks               # Voir vos banques et produits
    python main.py program create      # Créer un programme d'investissement
    python main.py program list        # Lister tous les programmes
    python main.py program ID          # Détail d'un programme
    python main.py program ID justify  # Justification détaillée d'un programme
    python main.py program delete ID   # Supprimer un programme
    python main.py scan                # Scanner les opportunités
    python main.py recommend           # Recommandation rapide
    python main.py monitor             # Surveillance continue
    python main.py portfolio           # État du portefeuille
    python main.py buy SYMBOL          # Enregistrer un achat
    python main.py sell SYMBOL         # Enregistrer une vente
    python main.py fiscal GAIN         # Simulation fiscale sur un gain
"""

import sys
import time
import datetime

from config.settings import (
    INITIAL_BUDGET_EUR, ASSET_CLASSES, ALERT_CONFIG, SHORT_TERM_CONFIG,
)
from config.user_profile import get_or_create_profile, load_profile, questionnaire_interactif
from market.data_fetcher import fetch_stock_data, fetch_crypto_history, fetch_current_price
from strategy.short_term import analyze_asset, scan_all_assets, get_buy_recommendations, check_exit_signals
from strategy.justifier import justifier_allocation, display_justification
from alerts.alert_engine import AlertEngine
from portfolio.tracker import PortfolioTracker
from utils.time_guard import can_trade_now, is_user_awake, next_trading_window
from banks.catalog import display_bank_selector, get_bank, get_user_banks
from programs.engine import ProgramManager
from fiscal.engine import FiscalEngine, display_fiscal_comparison
from dashboard.home import display_home


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
            time.sleep(0.3)

    return all_data


# ─── PAGE D'ACCUEIL ────────────────────────────────────────

def cmd_home():
    """Page d'accueil avec note marché."""
    profile = load_profile()
    pm = ProgramManager()
    programs = pm.list_programs()
    display_home(profile, programs)


# ─── PROFIL ────────────────────────────────────────────────

def cmd_profile():
    """Configurer ou mettre à jour le profil."""
    profile = get_or_create_profile()
    print(f"\n  Profil configuré pour {profile.get('prenom', 'Utilisateur')}.")
    print(f"  TMI: {profile.get('tmi', 0)*100:.0f}% | "
          f"Fiscalité gains: {profile.get('taux_imposition_gains', 0.30)*100:.1f}% | "
          f"Profil: {profile.get('profil_risque', '?')}")


# ─── BANQUES ───────────────────────────────────────────────

def cmd_banks():
    """Affiche les banques et produits de l'utilisateur."""
    profile = load_profile()
    if not profile:
        print("\n  Profil non configuré. Lancez: python main.py profile")
        return
    display_bank_selector(profile.get("banques", ["Revolut"]))


# ─── PROGRAMMES ────────────────────────────────────────────

def cmd_program(args: list):
    """Gestion des programmes d'investissement."""
    pm = ProgramManager()

    if not args:
        pm.display_all_programs()
        return

    subcmd = args[0].lower()

    if subcmd == "create":
        profile = load_profile()
        if not profile:
            print("\n  Profil requis. Lancement du questionnaire...")
            profile = questionnaire_interactif()

        program = pm.create_program(profile)
        print(f"\n  Programme '{program['nom']}' créé (ID: {program['id']})")

        # Afficher le programme avec allocation
        pm.display_program(program)

        # Justifier chaque ligne
        print(f"\n{'='*65}")
        print(f"  JUSTIFICATION DES CHOIX")
        print(f"{'='*65}")
        justified = justifier_allocation(program["allocation"], program, profile)
        for item in justified:
            display_justification(item)

        # Impact fiscal global
        total_gain_estime = sum(
            item.get("justification", {}).get("impact_fiscal", {}).get("gain_brut_estime", 0)
            for item in justified
        )
        if total_gain_estime > 0:
            print(f"\n  {'='*55}")
            display_fiscal_comparison(total_gain_estime, profile,
                                       duree_ans=int(program["duree_mois"] / 12))

    elif subcmd == "list":
        pm.display_all_programs()

    elif subcmd == "delete":
        if len(args) < 2:
            print("  Usage: python main.py program delete ID")
            return
        deleted = pm.delete_program(args[1])
        if deleted:
            print(f"  Programme {args[1]} supprimé.")
        else:
            print(f"  Programme {args[1]} non trouvé.")

    else:
        # Soit un ID de programme, soit un nom
        program = pm.get_program(subcmd)
        if not program:
            print(f"  Programme '{subcmd}' non trouvé.")
            pm.display_all_programs()
            return

        # Vérifier si "justify" est demandé
        if len(args) > 1 and args[1].lower() in ("justify", "justifier", "detail"):
            profile = load_profile()
            if profile:
                pm.display_program(program)
                print(f"\n{'='*65}")
                print(f"  JUSTIFICATION DÉTAILLÉE")
                print(f"{'='*65}")
                justified = justifier_allocation(program["allocation"], program, profile)
                for item in justified:
                    display_justification(item)
            else:
                print("  Profil requis pour la justification. Lancez: python main.py profile")
        else:
            pm.display_program(program)


# ─── SCAN ──────────────────────────────────────────────────

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


# ─── RECOMMANDATION ────────────────────────────────────────

def cmd_recommend():
    """Recommandation d'allocation pour le budget initial."""
    profile = load_profile()
    budget = INITIAL_BUDGET_EUR
    if profile:
        print(f"\n  Profil: {profile.get('prenom', '?')} | Risque: {profile.get('profil_risque', '?')}")

    print_header(f"RECOMMANDATION - BUDGET {budget}€")

    results, market_data = cmd_scan()
    recommendations = get_buy_recommendations(results, budget)

    print(f"\n{'='*60}")
    print(f"  ALLOCATION RECOMMANDÉE ({budget}€)")
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
        print(f"     Stop loss:  -{SHORT_TERM_CONFIG['stop_loss_pct']}% "
              f"({rec['price'] * (1 - SHORT_TERM_CONFIG['stop_loss_pct']/100):.4f})")
        print(f"     Take profit: +{SHORT_TERM_CONFIG['take_profit_pct']}% "
              f"({rec['price'] * (1 + SHORT_TERM_CONFIG['take_profit_pct']/100):.4f})")

    cash_remaining = budget - total_allocated
    print(f"\n  {'─'*40}")
    print(f"  Total alloué:    {total_allocated:.2f}€")
    print(f"  Cash restant:    {cash_remaining:.2f}€")

    # Impact fiscal si profil disponible
    if profile:
        print(f"\n  Impact fiscal (PFU): ~{total_allocated * 0.05 * 0.30:.2f}€ d'impôt "
              f"sur un gain de 5%")

    print(f"\n  Exécuter les achats sur votre banque, puis: python main.py buy SYMBOL")


# ─── MONITOR ──────────────────────────────────────────────

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

            released = alert_engine.check_pending_alerts()
            if released:
                print(f"  {len(released)} alerte(s) en attente libérée(s)")

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

                if data.get("close"):
                    current_price = data["close"][-1]
                    portfolio.update_highest_price(symbol, current_price)

                    exit_signal = check_exit_signals(pos, data)

                    if exit_signal["action"] == "SELL":
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


# ─── PORTFOLIO ─────────────────────────────────────────────

def cmd_portfolio():
    """Affiche l'état du portefeuille."""
    print_header("PORTEFEUILLE")

    portfolio = PortfolioTracker()
    positions = portfolio.get_all_positions()

    if not positions:
        print(f"\n  Cash: {portfolio.get_cash():.2f}€")
        print("  Aucune position ouverte.\n")
        return

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

    history = portfolio.get_trade_history()
    if history:
        print(f"\n  Derniers trades:")
        for t in history[-5:]:
            print(f"    {t['timestamp'][:16]} {t['action']} {t['symbol']} "
                  f"{t['amount_eur']:.2f}€ @ {t['price']:.4f}")


# ─── BUY / SELL ────────────────────────────────────────────

def cmd_buy(symbol: str):
    """Enregistrer un achat."""
    portfolio = PortfolioTracker()
    asset_class = _find_asset_class(symbol)
    price = fetch_current_price(symbol, asset_class)

    if not price:
        print(f"\n  Impossible de récupérer le prix de {symbol}.")
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

        # Info fiscale
        profile = load_profile()
        if profile:
            fiscal = FiscalEngine(profile)
            gain_5pct = amount * 0.05
            impact = fiscal.calculer_impot_plus_value(gain_5pct, "cto")
            print(f"\n  Info fiscale: sur un gain de +5% ({gain_5pct:.2f}€), "
                  f"impôt estimé: {impact['impot']:.2f}€ ({impact['detail']})")


def cmd_sell(symbol: str):
    """Enregistrer une vente."""
    portfolio = PortfolioTracker()
    pos = portfolio.get_position(symbol)

    if not pos:
        print(f"\n  Pas de position sur {symbol}.")
        return

    asset_class = pos.get("asset_class", "stocks_us")
    price = fetch_current_price(symbol, asset_class)

    if not price:
        try:
            price = float(input("  Prix de vente (EUR): "))
        except (ValueError, EOFError):
            print("  Prix invalide. Abandon.")
            return

    print(f"\n  {symbol} - Prix actuel: {price:.4f}€")
    print(f"  Position: {pos['quantity']:.6f} unités, investi: {pos['invested_eur']:.2f}€")

    pnl_estime = pos['quantity'] * price - pos['invested_eur']
    print(f"  P&L estimé: {pnl_estime:+.2f}€")

    # Impact fiscal avant vente
    profile = load_profile()
    if profile and pnl_estime > 0:
        fiscal = FiscalEngine(profile)
        impact = fiscal.calculer_impot_plus_value(pnl_estime, "cto")
        print(f"  Impôt estimé: {impact['impot']:.2f}€ → Net: {impact['gain_net']:.2f}€")

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

        print("\n  Recherche d'un remplacement...")
        market_data = fetch_all_market_data()
        results = scan_all_assets(market_data)
        alert_engine = AlertEngine()
        replacement = alert_engine.suggest_replacement(symbol, results)
        print(f"  {replacement['message']}")


# ─── FISCAL ────────────────────────────────────────────────

def cmd_fiscal(gain_str: str):
    """Simulation fiscale sur un gain."""
    try:
        gain = float(gain_str)
    except ValueError:
        print(f"  Gain invalide: {gain_str}")
        return

    profile = load_profile()
    if not profile:
        print("  Profil requis. Lancez: python main.py profile")
        return

    display_fiscal_comparison(gain, profile)


# ─── UTILS ─────────────────────────────────────────────────

def _find_asset_class(symbol: str) -> str:
    """Trouve la classe d'actif d'un symbole."""
    for asset_class, config in ASSET_CLASSES.items():
        if symbol.upper() in [s.upper() for s in config["symbols"]]:
            return asset_class
    return "stocks_us"


# ─── MAIN ──────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        cmd_home()
        return

    command = sys.argv[1].lower()

    if command == "home":
        cmd_home()
    elif command == "profile":
        cmd_profile()
    elif command == "banks":
        cmd_banks()
    elif command == "program":
        cmd_program(sys.argv[2:] if len(sys.argv) > 2 else [])
    elif command == "scan":
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
    elif command == "fiscal":
        if len(sys.argv) < 3:
            print("Usage: python main.py fiscal MONTANT_GAIN")
            return
        cmd_fiscal(sys.argv[2])
    else:
        print(f"  Commande inconnue: {command}")
        cmd_home()


if __name__ == "__main__":
    main()
