"""
Page d'accueil: note de marché du jour + résumé des programmes.
Récupère les indices majeurs et donne un aperçu rapide.
"""

import datetime
import time
from typing import Dict, List


def display_home(profile: dict = None, programs: list = None):
    """Affiche la page d'accueil complète."""
    _print_banner()
    _print_market_note()
    if profile:
        _print_user_summary(profile)
    if programs:
        _print_programs_summary(programs)
    _print_menu()


def _print_banner():
    now = datetime.datetime.now()
    jour_fr = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
    mois_fr = ["", "janvier", "février", "mars", "avril", "mai", "juin",
               "juillet", "août", "septembre", "octobre", "novembre", "décembre"]

    print(f"\n{'='*65}")
    print(f"  5GInvest - Module d'investissement guidé")
    print(f"  {jour_fr[now.weekday()]} {now.day} {mois_fr[now.month]} {now.year} - {now.strftime('%H:%M')}")
    print(f"{'='*65}")


def _print_market_note():
    """Récupère et affiche une note de marché du jour."""
    print(f"\n  SITUATION DES MARCHÉS")
    print(f"  {'─'*55}")

    indices = _fetch_indices()

    if not indices:
        print("  Données de marché indisponibles. Vérifiez votre connexion.")
        return

    # Affichage des indices
    print(f"  {'Indice':<22} {'Dernier':>10} {'Var. Jour':>10} {'Tendance':>10}")
    print(f"  {'─'*55}")

    for idx in indices:
        var = idx.get("change_pct", 0)
        tendance = "HAUSSIER" if var > 0.3 else "BAISSIER" if var < -0.3 else "NEUTRE"
        arrow = "+" if var > 0 else ""
        print(f"  {idx['nom']:<22} {idx.get('price', 'N/A'):>10} "
              f"{arrow}{var:>8.2f}% {tendance:>10}")

    # Note contextuelle
    print(f"\n  {'─'*55}")
    _print_market_commentary(indices)


def _fetch_indices() -> list:
    """Récupère les indices majeurs via yfinance."""
    index_symbols = {
        "^GSPC": "S&P 500",
        "^IXIC": "Nasdaq Composite",
        "^FCHI": "CAC 40",
        "^STOXX50E": "Euro Stoxx 50",
        "^GDAXI": "DAX 40",
        "BTC-EUR": "Bitcoin (EUR)",
        "GC=F": "Or (USD/oz)",
        "EURUSD=X": "EUR/USD",
    }

    indices = []
    try:
        import yfinance as yf
        for symbol, nom in index_symbols.items():
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="2d")
                if len(hist) >= 2:
                    current = hist["Close"].iloc[-1]
                    previous = hist["Close"].iloc[-2]
                    change_pct = ((current - previous) / previous) * 100
                    indices.append({
                        "symbol": symbol,
                        "nom": nom,
                        "price": f"{current:,.2f}",
                        "change_pct": round(change_pct, 2),
                    })
                elif len(hist) == 1:
                    indices.append({
                        "symbol": symbol,
                        "nom": nom,
                        "price": f"{hist['Close'].iloc[-1]:,.2f}",
                        "change_pct": 0,
                    })
                time.sleep(0.2)
            except Exception:
                pass
    except ImportError:
        pass

    return indices


def _print_market_commentary(indices: list):
    """Génère un commentaire contextuel sur les marchés."""
    now = datetime.datetime.now()
    weekday = now.weekday()

    # Analyser la tendance globale
    changes = [idx["change_pct"] for idx in indices if "change_pct" in idx]
    if not changes:
        print("  Pas assez de données pour un commentaire.")
        return

    avg_change = sum(changes) / len(changes)
    sp500 = next((i for i in indices if i["symbol"] == "^GSPC"), None)
    cac = next((i for i in indices if i["symbol"] == "^FCHI"), None)
    btc = next((i for i in indices if i["symbol"] == "BTC-EUR"), None)
    gold = next((i for i in indices if i["symbol"] == "GC=F"), None)

    commentary = []

    # Tendance générale
    if avg_change > 1:
        commentary.append("Marchés en forte hausse. Momentum positif, attention à ne pas acheter les sommets.")
    elif avg_change > 0.3:
        commentary.append("Marchés en légère hausse. Tendance favorable pour les achats progressifs.")
    elif avg_change < -1:
        commentary.append("Marchés en forte baisse. Opportunités possibles pour les profils dynamiques, prudence pour les autres.")
    elif avg_change < -0.3:
        commentary.append("Marchés en léger repli. Phase de consolidation, surveiller les supports techniques.")
    else:
        commentary.append("Marchés stables. Pas de signal directionnel fort, bon moment pour analyser.")

    # Contexte spécifique
    if sp500 and cac:
        if sp500["change_pct"] > 0 and cac["change_pct"] < 0:
            commentary.append("Divergence US/Europe: les marchés US surperforment l'Europe.")
        elif cac["change_pct"] > sp500["change_pct"] + 0.5:
            commentary.append("L'Europe surperforme les US: rotation sectorielle possible.")

    if btc:
        if btc["change_pct"] > 3:
            commentary.append(f"Bitcoin en forte hausse ({btc['change_pct']:+.1f}%). Appétit pour le risque élevé.")
        elif btc["change_pct"] < -3:
            commentary.append(f"Bitcoin en forte baisse ({btc['change_pct']:+.1f}%). Aversion au risque sur le crypto.")

    if gold and gold["change_pct"] > 1:
        commentary.append("L'or progresse: signe de recherche de valeurs refuges.")

    # Weekend
    if weekday >= 5:
        commentary.append("Weekend: marchés actions fermés. Seules les cryptos sont tradables.")
        commentary.append("Préparez vos ordres pour lundi matin.")

    # Horaire
    hour = now.hour
    if 9 <= hour < 10:
        commentary.append("Ouverture des marchés européens: volatilité accrue possible.")
    elif 15 <= hour < 16:
        commentary.append("Ouverture de Wall Street imminente: surveiller l'impact sur les indices EU.")
    elif hour >= 22:
        commentary.append("Marchés fermés. Bilan de la journée disponible.")

    for c in commentary:
        print(f"  > {c}")


def _print_user_summary(profile: dict):
    """Résumé du profil utilisateur."""
    print(f"\n  VOTRE PROFIL")
    print(f"  {'─'*55}")
    print(f"  {profile.get('prenom', 'Investisseur')} | "
          f"TMI: {profile.get('tmi', 0)*100:.0f}% | "
          f"Risque: {profile.get('profil_risque', '?')} | "
          f"Fiscalité: {profile.get('option_fiscale', 'PFU').upper()}")
    banques = profile.get("banques", [])
    if banques:
        print(f"  Banques: {', '.join(banques)}")
    enveloppes = []
    if profile.get("has_pea"):
        enveloppes.append(f"PEA ({profile.get('pea_age_ans', 0)} ans)")
    if profile.get("has_assurance_vie"):
        enveloppes.append(f"AV ({profile.get('av_age_ans', 0)} ans)")
    if profile.get("has_per"):
        enveloppes.append("PER")
    if profile.get("has_cto"):
        enveloppes.append("CTO")
    if enveloppes:
        print(f"  Enveloppes: {', '.join(enveloppes)}")


def _print_programs_summary(programs: list):
    """Résumé des programmes actifs."""
    active = [p for p in programs if p.get("status") == "active"]
    if not active:
        print(f"\n  Aucun programme actif. Créez-en un: python main.py program create")
        return

    total_budget = sum(p.get("budget_initial", 0) for p in active)

    print(f"\n  VOS PROGRAMMES ({len(active)} actifs, {total_budget:.0f}€ total)")
    print(f"  {'─'*55}")
    print(f"  {'Nom':<20} {'Budget':>8} {'Risque':<10} {'Horizon':<8} {'Envel.'}")
    print(f"  {'─'*55}")

    for p in active:
        print(f"  {p['nom']:<20} {p['budget_initial']:>7.0f}€ "
              f"{p['risque']:<10} {p['horizon']:<8} {p.get('enveloppe_preferee', 'CTO')}")


def _print_menu():
    """Affiche le menu principal."""
    print(f"\n  {'='*55}")
    print("  COMMANDES DISPONIBLES")
    print(f"  {'─'*55}")
    print("  python main.py home             Page d'accueil")
    print("  python main.py profile          Configurer votre profil")
    print("  python main.py banks            Voir vos banques et produits")
    print("  python main.py program create   Créer un programme")
    print("  python main.py program list     Lister les programmes")
    print("  python main.py program ID       Détail d'un programme")
    print("  python main.py scan             Scanner les opportunités")
    print("  python main.py recommend        Recommandation rapide")
    print("  python main.py monitor          Surveillance continue")
    print("  python main.py portfolio        État du portefeuille")
    print("  python main.py fiscal GAIN      Simulation fiscale")
    print(f"  {'='*55}\n")
