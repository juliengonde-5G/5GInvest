"""
Moteur de justification des propositions d'investissement.
Chaque recommandation est accompagnée d'une explication structurée:
pourquoi cet actif, pourquoi cette enveloppe, pourquoi cette banque,
impact fiscal, risques identifiés.
"""

from typing import Dict, List
from fiscal.engine import FiscalEngine


def justifier_allocation(allocation: list, program: dict, profile: dict) -> list:
    """
    Génère une justification complète pour chaque ligne d'allocation.
    Retourne la liste d'allocations enrichie avec les justifications.
    """
    fiscal = FiscalEngine(profile)
    justified = []

    for item in allocation:
        j = build_justification(item, program, profile, fiscal)
        item["justification"] = j
        justified.append(item)

    return justified


def build_justification(item: dict, program: dict, profile: dict,
                        fiscal: FiscalEngine) -> dict:
    """Construit la justification complète d'une ligne d'allocation."""
    categorie = item["categorie"]
    instrument = item.get("instrument", {})
    montant = item["montant_eur"]
    risque = program["risque"]
    horizon = program["horizon"]

    justif = {
        "pourquoi_cet_actif": _justifier_actif(categorie, risque, horizon),
        "pourquoi_cette_proportion": _justifier_proportion(item["pct"], categorie, risque),
        "pourquoi_cette_enveloppe": _justifier_enveloppe(
            program.get("enveloppe_preferee", "cto"), categorie, profile
        ),
        "pourquoi_cette_banque": _justifier_banque(
            item.get("banques_disponibles", []), categorie, instrument
        ),
        "impact_fiscal": _impact_fiscal(montant, program, profile, fiscal),
        "risques": _identifier_risques(categorie, montant, program),
        "alternatives": _proposer_alternatives(categorie, risque),
    }

    return justif


def _justifier_actif(categorie: str, risque: str, horizon: str) -> str:
    """Pourquoi cet actif est recommandé."""
    justifications = {
        "etf_monde": (
            "Diversification mondiale sur ~1500 entreprises. Historiquement ~8%/an. "
            "Pilier de tout portefeuille, réduit le risque spécifique. "
            "Corrélation faible entre zones géographiques = amortisseur."
        ),
        "etf_sp500": (
            "Exposition aux 500 plus grandes entreprises US. Moteur de performance "
            "mondial, dominé par la tech. Rendement historique ~10%/an. "
            "Liquidité maximale."
        ),
        "etf_nasdaq": (
            "Exposition concentrée sur la tech US (FAANG+). Volatilité plus élevée "
            "mais potentiel de surperformance sur le court/moyen terme. "
            "Secteur leader de l'innovation (IA, cloud, semi-conducteurs)."
        ),
        "etf_emergents": (
            "Diversification géographique vers Chine, Inde, Brésil. Valorisations "
            "souvent décotées vs marchés développés. Potentiel de rattrapage. "
            "Décorrélation partielle avec les marchés US/EU."
        ),
        "obligations_etf": (
            "Stabilisateur de portefeuille. Rendement modéré mais prévisible. "
            "Corrélation négative avec les actions en période de stress. "
            "Protection contre la récession."
        ),
        "or_etf": (
            "Valeur refuge historique. Protection contre l'inflation et les crises "
            "géopolitiques. Décorrélé des actions et obligations. "
            "Rôle de diversification et de couverture."
        ),
        "crypto_btc": (
            "Bitcoin: actif numérique le plus établi. Supply limité (21M). "
            "Adoption institutionnelle croissante (ETF spot US). "
            "Très volatil mais potentiel asymétrique. Décorrélation partielle."
        ),
        "crypto_alt": (
            "Ethereum: blockchain smart contracts n°1. Écosystème DeFi/NFT. "
            "Plus risqué que BTC mais potentiel de hausse supérieur. "
            "Staking possible (rendement supplémentaire)."
        ),
        "actions_growth": (
            "Actions de croissance (ex: NVIDIA). Potentiel de plus-value élevé "
            "porté par des mégatendances (IA, data centers). "
            "Volatilité élevée, adapté au profil dynamique/agressif."
        ),
        "actions_momentum": (
            "Actions à fort momentum (ex: Tesla). Stratégie de suivi de tendance. "
            "Rendement potentiel élevé à court terme. "
            "Risque élevé de retournement, nécessite un suivi actif."
        ),
        "actions_small_cap": (
            "Small caps (ex: Palantir). Potentiel de croissance supérieur aux "
            "large caps. Moins suivies par les analystes = opportunités. "
            "Volatilité et risque de liquidité plus élevés."
        ),
        "fonds_euro": (
            "Capital garanti (brut de frais). Rendement 2024: 2.5-4%. "
            "Liquidité totale. Idéal pour la partie sécurisée du portefeuille. "
            "Fiscalité avantageuse via l'assurance-vie après 8 ans."
        ),
        "monetaire": (
            "ETF monétaire (ex: Xtrackers EUR Overnight). Quasi sans risque. "
            "Rendement proche du taux BCE (~3%). Alternative au livret A "
            "pour la trésorerie d'investissement."
        ),
        "scpi": (
            "Immobilier papier. Rendement 4-6% via les loyers. "
            "Diversification immobilière sans gestion. "
            "Ticket d'entrée réduit en AV. Peu liquide."
        ),
    }
    base = justifications.get(categorie, f"Catégorie {categorie}: allocation standard pour profil {risque}.")

    # Ajustement selon le contexte
    if risque == "agressif":
        base += " Allocation renforcée vu votre appétit pour le risque."
    elif risque == "prudent" and categorie in ("crypto_btc", "crypto_alt"):
        base += " Position réduite par prudence, mais inclusion pour diversification."

    return base


def _justifier_proportion(pct: float, categorie: str, risque: str) -> str:
    """Pourquoi cette proportion."""
    if pct >= 30:
        return (f"{pct}%: Position cœur du portefeuille. Poids important car "
                f"c'est le moteur principal de performance pour un profil {risque}.")
    elif pct >= 15:
        return (f"{pct}%: Position significative. Bon équilibre entre contribution "
                f"au rendement et maîtrise du risque global.")
    elif pct >= 10:
        return (f"{pct}%: Position satellite. Apporte de la diversification et "
                f"du potentiel sans trop exposer le portefeuille.")
    else:
        return (f"{pct}%: Position tactique. Allocation mesurée pour capturer "
                f"une opportunité tout en limitant l'impact en cas de baisse.")


def _justifier_enveloppe(enveloppe: str, categorie: str, profile: dict) -> str:
    """Pourquoi cette enveloppe fiscale."""
    if enveloppe == "pea" and profile.get("has_pea"):
        anc = profile.get("pea_age_ans", 0)
        if anc >= 5:
            return ("PEA > 5 ans: plus-values exonérées d'IR (17.2% PS uniquement). "
                    "Fiscalité optimale pour les ETF éligibles EU.")
        else:
            return (f"PEA ({anc} ans): pas encore à maturité fiscale (5 ans requis). "
                    "Mais chaque versement compte pour atteindre l'exonération.")

    if enveloppe == "assurance_vie" and profile.get("has_assurance_vie"):
        anc = profile.get("av_age_ans", 0)
        if anc >= 8:
            return ("AV > 8 ans: abattement annuel (4600€ solo / 9200€ couple) sur les gains. "
                    "Taux réduit 7.5% + PS. Fiscalité très avantageuse.")
        else:
            return (f"AV ({anc} ans): en route vers la maturité fiscale (8 ans). "
                    "Idéale pour fonds euro et UC avec horizon long.")

    if categorie in ("crypto_btc", "crypto_alt"):
        return ("CTO obligatoire pour la crypto (pas éligible PEA/AV). "
                "Flat tax 30% sur les plus-values. Garder les justificatifs.")

    return ("CTO: enveloppe par défaut, accès à tous les produits. "
            "Flat tax 30% sur les gains. Pas de contrainte de versement.")


def _justifier_banque(banques_dispo: list, categorie: str, instrument: dict) -> str:
    """Pourquoi cette banque."""
    if not banques_dispo:
        return "Aucune banque compatible identifiée pour cet instrument."

    bank = banques_dispo[0]
    if "Revolut" in bank:
        return (f"{bank}: 0 commission, actions fractionnées dès 1€, "
                "parfait pour les petits montants et le trading actif.")
    elif "Trade Republic" in bank:
        return (f"{bank}: 1€ fixe par ordre, plans d'épargne gratuits (DCA), "
                "2.75% sur le cash, très compétitif pour les ETF.")
    elif "Bourso" in bank:
        return (f"{bank}: PEA compétitif, AV Bourso Vie (bon fonds euro), "
                "IFU fourni, idéal pour l'investissement long terme.")
    elif "Fortuneo" in bank:
        return (f"{bank}: 1 ordre gratuit/mois, AV Fortuneo Vie à 0.60% de frais, "
                "excellent pour les ETF en PEA.")
    elif "Bourse Direct" in bank:
        return (f"{bank}: PEA le moins cher (0.99€/ordre), "
                "parfait pour optimiser les frais sur petits ordres.")
    elif "DEGIRO" in bank:
        return (f"{bank}: ETF core selection gratuit, actions US à 0.50€, "
                "très compétitif pour les marchés internationaux.")
    else:
        return f"{bank}: disponible pour {categorie}."


def _impact_fiscal(montant: float, program: dict, profile: dict,
                   fiscal: FiscalEngine) -> dict:
    """Calcule et explique l'impact fiscal."""
    rendement_vise = program["objectif_rendement_pct"]
    duree_ans = program["duree_mois"] / 12
    gain_estime = montant * (rendement_vise / 100) * duree_ans

    enveloppe = program.get("enveloppe_preferee", "cto")
    impact = fiscal.calculer_impot_plus_value(gain_estime, enveloppe)

    return {
        "gain_brut_estime": round(gain_estime, 2),
        "impot_estime": impact["impot"],
        "gain_net_estime": impact["gain_net"],
        "taux_effectif": impact["taux_effectif"],
        "detail": impact["detail"],
        "conseil": _conseil_fiscal(enveloppe, profile),
    }


def _conseil_fiscal(enveloppe: str, profile: dict) -> str:
    """Conseil fiscal personnalisé."""
    tmi = profile.get("tmi", 0.30)
    if tmi <= 0.11 and profile.get("option_fiscale") == "pfu":
        return ("Avec votre TMI à 11%, le barème progressif pourrait être "
                "plus avantageux que le PFU. À étudier avec un conseiller.")
    if enveloppe == "cto" and profile.get("has_pea") and profile.get("pea_age_ans", 0) >= 5:
        return ("Votre PEA est mature (>5 ans). Privilégiez-le pour les ETF "
                "éligibles afin de ne payer que 17.2% au lieu de 30%.")
    return "Flat tax 30% appliquée. Optimisation possible via PEA/AV selon les produits."


def _identifier_risques(categorie: str, montant: float, program: dict) -> list:
    """Identifie les risques spécifiques."""
    risques = []

    # Risques par catégorie
    risk_map = {
        "crypto_btc": ["Volatilité extrême (±20% en quelques jours)", "Risque réglementaire"],
        "crypto_alt": ["Volatilité très élevée", "Risque de projet", "Liquidité variable"],
        "actions_growth": ["Valorisation élevée (ratio P/E)", "Sensible aux taux d'intérêt"],
        "actions_momentum": ["Retournement de tendance brutal possible", "Forte volatilité"],
        "actions_small_cap": ["Liquidité faible", "Information limitée", "Volatilité élevée"],
        "etf_levier": ["Effet levier 2x = pertes amplifiées", "Beta slippage sur le long terme"],
        "etf_emergents": ["Risque politique", "Risque de change", "Volatilité supérieure"],
        "fonds_euro": ["Rendement réel possiblement négatif si inflation élevée"],
        "scpi": ["Liquidité faible", "Risque immobilier", "Frais élevés"],
    }
    risques.extend(risk_map.get(categorie, ["Risque de marché standard"]))

    # Risque de concentration
    if program.get("budget_initial", 0) < 500 and montant > program.get("budget_initial", 0) * 0.3:
        risques.append("Concentration: position > 30% sur un petit portefeuille")

    # Risque de change
    if categorie in ("etf_sp500", "etf_nasdaq", "actions_growth", "actions_momentum"):
        risques.append("Risque de change EUR/USD")

    return risques


def _proposer_alternatives(categorie: str, risque: str) -> list:
    """Propose des alternatives à la ligne d'allocation."""
    alternatives = {
        "etf_monde": ["VWCE.DE (Vanguard FTSE All-World)", "CW8.PA (Amundi MSCI World, éligible PEA)"],
        "etf_sp500": ["ESE.PA (BNP S&P 500 PEA)", "PE500.PA (Amundi S&P 500, éligible PEA)"],
        "etf_nasdaq": ["PANX.PA (Amundi Nasdaq, éligible PEA)", "UST.PA (Lyxor Nasdaq)"],
        "crypto_btc": ["IBIT (ETF Bitcoin spot, si disponible)", "Exposition indirecte via MARA/COIN"],
        "crypto_alt": ["SOL (Solana, alternative plus rapide)", "AVAX (Avalanche)"],
        "obligations_etf": ["DBZB.DE (Xtrackers Eurozone Gov)", "Fonds euro AV (si disponible)"],
        "or_etf": ["PHAU.AS (WisdomTree Physical Gold)", "GBS.AS (Gold Bullion Securities)"],
    }
    return alternatives.get(categorie, [])


def display_justification(item: dict):
    """Affiche la justification d'une ligne d'allocation."""
    j = item.get("justification", {})
    instr = item.get("instrument", {})

    print(f"\n  {'─'*55}")
    print(f"  {item['categorie']} → {instr.get('nom', '?')} ({instr.get('symbol', '?')})")
    print(f"  Allocation: {item['pct']}% = {item['montant_eur']:.2f}€")
    print(f"  {'─'*55}")

    print(f"\n  POURQUOI CET ACTIF:")
    _wrap_print(j.get("pourquoi_cet_actif", ""), indent=4)

    print(f"\n  POURQUOI {item['pct']}%:")
    _wrap_print(j.get("pourquoi_cette_proportion", ""), indent=4)

    print(f"\n  ENVELOPPE:")
    _wrap_print(j.get("pourquoi_cette_enveloppe", ""), indent=4)

    print(f"\n  BANQUE:")
    _wrap_print(j.get("pourquoi_cette_banque", ""), indent=4)

    fiscal = j.get("impact_fiscal", {})
    if fiscal:
        print(f"\n  IMPACT FISCAL:")
        print(f"    Gain brut estimé: {fiscal.get('gain_brut_estime', 0):.2f}€")
        print(f"    Impôt estimé:     {fiscal.get('impot_estime', 0):.2f}€")
        print(f"    Gain net estimé:  {fiscal.get('gain_net_estime', 0):.2f}€")
        print(f"    Taux effectif:    {fiscal.get('taux_effectif', 0):.1f}%")
        print(f"    Conseil:          {fiscal.get('conseil', '')}")

    risques = j.get("risques", [])
    if risques:
        print(f"\n  RISQUES:")
        for r in risques:
            print(f"    - {r}")

    alternatives = j.get("alternatives", [])
    if alternatives:
        print(f"\n  ALTERNATIVES:")
        for a in alternatives:
            print(f"    - {a}")


def _wrap_print(text: str, indent: int = 4, width: int = 70):
    """Affiche du texte avec retour à la ligne propre."""
    prefix = " " * indent
    words = text.split()
    line = prefix
    for word in words:
        if len(line) + len(word) + 1 > width:
            print(line)
            line = prefix + word
        else:
            line += (" " if line.strip() else "") + word
    if line.strip():
        print(line)
