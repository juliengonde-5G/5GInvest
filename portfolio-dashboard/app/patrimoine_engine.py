"""
Moteur d'opinion patrimoniale globale.
Analyse l'ensemble du patrimoine et formule des recommandations.
"""

from datetime import date
from typing import Dict, List


def generate_patrimoine_opinion(profile: dict, dashboard: dict) -> dict:
    """
    Génère une opinion de gestionnaire de patrimoine sur l'ensemble du patrimoine.
    Prend en compte: âge, objectifs, allocation, endettement, revenus.
    """
    opinions = []
    alertes = []
    recommandations = []

    net_worth = dashboard.get("net_worth", 0)
    allocation = dashboard.get("allocation", {})
    age = profile.get("age", 35)
    objectif = profile.get("objectif_principal", "constitution")
    capacite_epargne = profile.get("capacite_epargne_mensuelle", 0)
    profil_risque = profile.get("profil_risque", "equilibre")

    # ─── 1. Vue globale patrimoine ────────────────────────

    opinions.append({
        "type": "patrimoine",
        "message": f"Patrimoine net: {net_worth:,.0f}€.",
        "detail": _patrimoine_context(net_worth, age),
    })

    # ─── 2. Analyse de l'allocation ───────────────────────

    immo_pct = allocation.get("immo_pct", 0)
    crypto_pct = allocation.get("crypto_pct", 0)
    cash_pct = allocation.get("cash_pct", 0)
    commodity_pct = allocation.get("commodity_pct", 0)

    # Allocation cible selon âge
    target = _target_allocation(age, profil_risque)

    # Immobilier
    if immo_pct > 70:
        alertes.append({
            "niveau": "attention",
            "message": f"Patrimoine très concentré en immobilier ({immo_pct:.0f}%). Risque de liquidité.",
        })
        recommandations.append("Diversifiez vers des actifs liquides (ETF, épargne) pour réduire le risque de concentration.")
    elif immo_pct > 0 and immo_pct < 20 and age > 30:
        recommandations.append("L'immobilier représente moins de 20% de votre patrimoine. C'est un bon levier d'endettement pour constituer du patrimoine.")

    # Cash
    charges_mensuelles = profile.get("charges_fixes_mensuelles", 0)
    epargne_precaution_cible = charges_mensuelles * profile.get("epargne_precaution_mois", 3)
    cash_total = allocation.get("cash", 0)

    if cash_total < epargne_precaution_cible and epargne_precaution_cible > 0:
        alertes.append({
            "niveau": "important",
            "message": f"Épargne de précaution insuffisante: {cash_total:,.0f}€ vs {epargne_precaution_cible:,.0f}€ recommandés ({profile.get('epargne_precaution_mois', 3)} mois de charges).",
        })
        recommandations.append(f"Constituez {epargne_precaution_cible - cash_total:,.0f}€ d'épargne de précaution avant d'investir.")
    elif cash_pct > 40 and net_worth > 10000:
        recommandations.append(f"Cash élevé ({cash_pct:.0f}%). Placez l'excédent: Livret A, LDDS, ou ETF monétaire pour ne pas perdre en pouvoir d'achat.")

    # Crypto
    crypto_max = {"prudent": 5, "equilibre": 15, "dynamique": 25, "agressif": 40}.get(profil_risque, 15)
    if crypto_pct > crypto_max:
        alertes.append({
            "niveau": "attention",
            "message": f"Crypto surpondérée ({crypto_pct:.0f}% vs {crypto_max}% max pour profil {profil_risque}).",
        })
        recommandations.append(f"Réduisez la crypto à {crypto_max}% max. Arbitrez vers des ETF diversifiés.")

    # ─── 3. Endettement ───────────────────────────────────

    immo_data = dashboard.get("real_estate", [])
    total_credit = sum(p.get("capital_restant_du_total", 0) for p in immo_data)
    total_mensualites = sum(p.get("credit_mensuel_total", 0) for p in immo_data)
    revenu_mensuel = (profile.get("revenu_net_annuel", 0) or 0) / 12

    if revenu_mensuel > 0 and total_mensualites > 0:
        taux_endettement = total_mensualites / revenu_mensuel * 100
        opinions.append({
            "type": "endettement",
            "message": f"Taux d'endettement: {taux_endettement:.0f}%.",
            "detail": _endettement_context(taux_endettement),
        })
        if taux_endettement > 35:
            alertes.append({
                "niveau": "critique",
                "message": f"Taux d'endettement à {taux_endettement:.0f}% (seuil HCSF: 35%). Capacité d'emprunt bloquée.",
            })
        elif taux_endettement > 25:
            recommandations.append(f"Endettement à {taux_endettement:.0f}%. Marge restante pour un investissement immobilier si opportunité.")

    # ─── 4. Objectifs ─────────────────────────────────────

    if objectif == "retraite" and profile.get("age_objectif"):
        annees = profile.get("annees_avant_objectif", 0)
        if annees and profile.get("montant_objectif"):
            gap = profile["montant_objectif"] - net_worth
            if gap > 0:
                epargne_requise = gap / (annees * 12) if annees > 0 else gap
                opinions.append({
                    "type": "objectif",
                    "message": f"Objectif retraite à {profile['age_objectif']} ans: {profile['montant_objectif']:,.0f}€. Gap: {gap:,.0f}€.",
                    "detail": f"Épargne mensuelle requise: {epargne_requise:,.0f}€/mois sur {annees} ans (hors rendement).",
                })
                if capacite_epargne < epargne_requise:
                    recommandations.append(f"Votre capacité d'épargne ({capacite_epargne:,.0f}€/mois) est inférieure au besoin ({epargne_requise:,.0f}€/mois). Augmentez l'épargne ou acceptez un objectif ajusté.")
            else:
                opinions.append({
                    "type": "objectif",
                    "message": f"Objectif retraite atteint ! Patrimoine ({net_worth:,.0f}€) > objectif ({profile['montant_objectif']:,.0f}€).",
                    "detail": "Sécurisez progressivement votre patrimoine.",
                })
    elif objectif == "liberte_financiere":
        revenu_passif_mensuel = sum(p.get("cashflow_mensuel", 0) for p in immo_data if p.get("cashflow_mensuel", 0) > 0)
        opinions.append({
            "type": "objectif",
            "message": f"Revenus passifs actuels: {revenu_passif_mensuel:,.0f}€/mois.",
            "detail": f"vs charges: {charges_mensuelles:,.0f}€/mois. Couverture: {revenu_passif_mensuel/charges_mensuelles*100:.0f}%." if charges_mensuelles > 0 else "",
        })

    # ─── 5. Recommandations adaptées à l'âge ─────────────

    if age < 30:
        recommandations.append("À votre âge, privilégiez la prise de risque mesurée (ETF actions mondiales) et l'effet de levier immobilier.")
    elif age > 55:
        recommandations.append("Approche de la retraite: sécurisez progressivement (fonds euro, obligations, réduction crypto).")

    # Enveloppes fiscales
    if not profile.get("has_pea") and profil_risque in ("equilibre", "dynamique", "agressif"):
        recommandations.append("Ouvrez un PEA pour bénéficier de l'exonération IR après 5 ans sur les ETF EU.")
    if not profile.get("has_assurance_vie"):
        recommandations.append("Ouvrez une assurance-vie: prise de date pour l'abattement après 8 ans + transmission avantageuse.")

    # ─── 6. Score global ──────────────────────────────────

    score = _compute_health_score(net_worth, allocation, profile, alertes)

    return {
        "score_sante": score,
        "score_label": _score_label(score),
        "opinions": opinions,
        "alertes": alertes,
        "recommandations": recommandations,
        "allocation_cible": target,
        "disclaimer": "Analyse automatique. Ne constitue pas un conseil en investissement ni en gestion de patrimoine.",
    }


def _patrimoine_context(net_worth: float, age: int) -> str:
    # Patrimoine médian par âge en France (INSEE 2021, actualisé)
    medians = {25: 15000, 30: 45000, 35: 95000, 40: 155000, 45: 200000,
               50: 250000, 55: 280000, 60: 300000, 65: 310000, 70: 290000}
    closest_age = min(medians.keys(), key=lambda a: abs(a - age))
    median = medians[closest_age]
    if net_worth > median * 1.5:
        return f"Nettement au-dessus de la médiane française pour votre tranche d'âge ({median:,.0f}€)."
    elif net_worth > median:
        return f"Au-dessus de la médiane française ({median:,.0f}€ pour ~{closest_age} ans)."
    else:
        return f"En-dessous de la médiane française ({median:,.0f}€ pour ~{closest_age} ans). Accélérez la constitution."


def _endettement_context(taux: float) -> str:
    if taux > 35:
        return "Au-dessus du seuil HCSF (35%). Plus d'emprunt immobilier possible sauf exception."
    elif taux > 25:
        return "Endettement modéré. Marge pour un crédit supplémentaire."
    elif taux > 10:
        return "Endettement maîtrisé. Bonne capacité d'emprunt."
    return "Très faible endettement. Capacité d'emprunt maximale."


def _target_allocation(age: int, profil: str) -> dict:
    """Allocation cible selon âge et profil (règle du 100 - âge adaptée)."""
    actions_pct = max(20, min(80, 100 - age))
    if profil == "prudent":
        actions_pct = max(10, actions_pct - 20)
    elif profil == "agressif":
        actions_pct = min(90, actions_pct + 15)

    return {
        "actions_etf": actions_pct,
        "obligations_fonds_euro": max(10, 100 - actions_pct - 10),
        "immobilier": 20,  # en sus si levier
        "cash_epargne": 10,
        "note": f"Allocation indicative pour {age} ans, profil {profil}.",
    }


def _compute_health_score(net_worth, allocation, profile, alertes) -> int:
    """Score de santé patrimoniale sur 100."""
    score = 50  # base

    # Patrimoine positif
    if net_worth > 0:
        score += 10
    if net_worth > 100000:
        score += 5

    # Diversification
    classes = [allocation.get("immo_pct", 0) > 5, allocation.get("crypto_pct", 0) > 0,
               allocation.get("cash_pct", 0) > 5, allocation.get("commodity_pct", 0) > 0]
    score += sum(classes) * 5

    # Épargne
    if profile.get("capacite_epargne_mensuelle", 0) > 0:
        score += 10

    # Pénalités alertes
    for a in alertes:
        if a["niveau"] == "critique":
            score -= 15
        elif a["niveau"] == "important":
            score -= 10
        elif a["niveau"] == "attention":
            score -= 5

    return max(0, min(100, score))


def _score_label(score: int) -> str:
    if score >= 80:
        return "Excellent"
    elif score >= 60:
        return "Bon"
    elif score >= 40:
        return "À améliorer"
    elif score >= 20:
        return "Fragile"
    return "Critique"
