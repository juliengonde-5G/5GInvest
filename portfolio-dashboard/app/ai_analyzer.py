"""
Analyse IA du portefeuille via Claude API.
Génère: score de risque, insights, recommandations.
"""

import os
import json
from typing import Optional


def analyze_portfolio(portfolio_data: dict) -> dict:
    """
    Envoie le portefeuille complet à Claude pour analyse.
    Retourne: risk_score, insights[], recommendations[].
    """
    api_key = os.environ.get("CLAUDE_API_KEY")
    if not api_key:
        return _fallback_analysis(portfolio_data)

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)

        prompt = _build_prompt(portfolio_data)

        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}],
            system=(
                "Tu es un analyste financier expert en gestion de patrimoine personnel français. "
                "Tu analyses un portefeuille multi-actifs (immobilier, crypto, matières premières, cash). "
                "Réponds UNIQUEMENT en JSON valide avec les clés: "
                "risk_score (1-10), risk_label (string), insights (array de strings), "
                "recommendations (array de strings), allocation_opinion (string). "
                "Sois concis, actionnable, en français. "
                "DISCLAIMER: Rappelle que ce n'est pas un conseil en investissement."
            ),
        )

        text = message.content[0].text.strip()
        # Extraire le JSON
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]

        result = json.loads(text)
        result["source"] = "claude"
        return result

    except Exception as e:
        return _fallback_analysis(portfolio_data, error=str(e))


def _build_prompt(data: dict) -> str:
    """Construit le prompt pour Claude avec les données du portefeuille."""
    net_worth = data.get("net_worth", 0)
    allocation = data.get("allocation", {})

    prompt = f"""Analyse ce portefeuille personnel (valeur nette: {net_worth:,.0f}€):

ALLOCATION:
- Immobilier: {allocation.get('immo', 0):,.0f}€ ({allocation.get('immo_pct', 0):.1f}%)
- Crypto: {allocation.get('crypto', 0):,.0f}€ ({allocation.get('crypto_pct', 0):.1f}%)
- Matières premières: {allocation.get('commodity', 0):,.0f}€ ({allocation.get('commodity_pct', 0):.1f}%)
- Cash: {allocation.get('cash', 0):,.0f}€ ({allocation.get('cash_pct', 0):.1f}%)

DÉTAILS IMMOBILIER:
"""
    for prop in data.get("real_estate", []):
        prompt += (
            f"- {prop.get('nom', '?')}: valeur {prop.get('valeur_estimee', 0):,.0f}€, "
            f"rendement brut {prop.get('rendement_brut', 0)}%, "
            f"cashflow {prop.get('cashflow_mensuel', 0):+,.0f}€/mois\n"
        )

    prompt += "\nDÉTAILS CRYPTO:\n"
    for pos in data.get("crypto", []):
        prompt += (
            f"- {pos.get('symbol', '?')}: {pos.get('current_value', 0):,.0f}€ "
            f"(P&L: {pos.get('pnl_pct', 0):+.1f}%)\n"
        )

    prompt += "\nDÉTAILS MATIÈRES PREMIÈRES:\n"
    for pos in data.get("commodities", []):
        prompt += (
            f"- {pos.get('nom', pos.get('symbol', '?'))}: {pos.get('current_value', 0):,.0f}€ "
            f"(P&L: {pos.get('pnl_pct', 0):+.1f}%)\n"
        )

    prompt += f"\nCASH TOTAL: {allocation.get('cash', 0):,.0f}€\n"

    prompt += """
Donne ton analyse JSON avec:
1. risk_score (1=très prudent à 10=très risqué)
2. risk_label ("Faible", "Modéré", "Élevé", "Très élevé")
3. insights (3-5 observations clés)
4. recommendations (3-5 actions concrètes)
5. allocation_opinion (1 phrase sur l'allocation globale)
"""
    return prompt


def _fallback_analysis(data: dict, error: str = None) -> dict:
    """Analyse basique sans Claude API."""
    allocation = data.get("allocation", {})
    net_worth = data.get("net_worth", 0)

    insights = []
    recommendations = []
    risk_score = 5

    # Analyse automatique de l'allocation
    crypto_pct = allocation.get("crypto_pct", 0)
    immo_pct = allocation.get("immo_pct", 0)
    cash_pct = allocation.get("cash_pct", 0)

    if crypto_pct > 30:
        risk_score += 2
        insights.append(f"Surpondération crypto ({crypto_pct:.0f}%). Volatilité élevée.")
        recommendations.append("Réduire l'exposition crypto à 15-20% max pour un profil équilibré.")

    if crypto_pct > 0 and crypto_pct < 5:
        insights.append(f"Faible exposition crypto ({crypto_pct:.0f}%). Position exploratoire.")

    if immo_pct > 70:
        insights.append(f"Portefeuille très concentré en immobilier ({immo_pct:.0f}%). Peu liquide.")
        recommendations.append("Diversifier vers des actifs plus liquides (ETF, cash).")
    elif immo_pct > 40:
        insights.append(f"Bonne base immobilière ({immo_pct:.0f}%). Patrimoine tangible.")

    if cash_pct > 40:
        risk_score -= 1
        insights.append(f"Cash élevé ({cash_pct:.0f}%). Sécurité mais rendement faible.")
        recommendations.append("Placer une partie du cash en livrets rémunérés ou ETF monétaire.")
    elif cash_pct < 5:
        risk_score += 1
        insights.append(f"Cash très faible ({cash_pct:.0f}%). Pas de coussin de sécurité.")
        recommendations.append("Constituer une épargne de précaution (3-6 mois de charges).")

    if not insights:
        insights.append("Portefeuille diversifié. Allocation correcte.")

    if not recommendations:
        recommendations.append("Maintenir l'allocation actuelle. Réévaluer trimestriellement.")

    risk_score = max(1, min(10, risk_score))
    risk_labels = {1: "Très faible", 2: "Très faible", 3: "Faible", 4: "Faible",
                   5: "Modéré", 6: "Modéré", 7: "Élevé", 8: "Élevé",
                   9: "Très élevé", 10: "Très élevé"}

    result = {
        "risk_score": risk_score,
        "risk_label": risk_labels.get(risk_score, "Modéré"),
        "insights": insights,
        "recommendations": recommendations,
        "allocation_opinion": f"Patrimoine de {net_worth:,.0f}€ avec allocation {_describe_alloc(allocation)}.",
        "source": "fallback" if not error else f"fallback (API error: {error[:50]})",
        "disclaimer": "Analyse automatique. Ne constitue pas un conseil en investissement.",
    }
    return result


def _describe_alloc(alloc: dict) -> str:
    """Décrit l'allocation en mots."""
    parts = []
    for key, label in [("immo_pct", "immobilier"), ("crypto_pct", "crypto"),
                        ("commodity_pct", "commodities"), ("cash_pct", "cash")]:
        pct = alloc.get(key, 0)
        if pct > 0:
            parts.append(f"{pct:.0f}% {label}")
    return ", ".join(parts) if parts else "non définie"
