"""
Prompts Claude spécialisés par domaine.
Chaque module a son propre persona et expertise.
"""

import os
import json

CLAUDE_KEY = os.environ.get("CLAUDE_API_KEY", "")


def _call_claude(system_prompt: str, user_prompt: str, max_tokens: int = 1200) -> str:
    """Appel générique à Claude."""
    if not CLAUDE_KEY:
        return None
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=CLAUDE_KEY)
        msg = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=max_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        return msg.content[0].text.strip()
    except Exception as e:
        return None


# ─── EXPERT IMMOBILIER ────────────────────────────────────

def analyze_property(property_data: dict) -> dict:
    """Analyse d'un bien immobilier par un expert."""
    system = (
        "Tu es un expert immobilier français spécialisé dans l'estimation et le conseil patrimonial. "
        "Tu connais parfaitement les prix de marché par zone, les mécanismes de plus-value, "
        "la fiscalité immobilière (micro-foncier, réel, LMNP, SCI), les indices de référence des loyers, "
        "et les tendances du marché FR. "
        "Réponds en JSON: {avis: string, points_forts: [], points_faibles: [], "
        "estimation_vente_min: number, estimation_vente_max: number, "
        "conseil_travaux: string, conseil_fiscal: string, horizon_vente: string}"
    )
    prompt = f"""Analyse ce bien immobilier:
Nom: {property_data.get('nom')}
Adresse: {property_data.get('adresse')}, {property_data.get('code_postal')} {property_data.get('ville')}
Type: {property_data.get('type_bien')} | Surface: {property_data.get('surface_habitable_m2')}m²
DPE: {property_data.get('dpe')} | Année: {property_data.get('annee_construction')}
Prix achat: {property_data.get('prix_achat_total')}€ | Valeur estimée: {property_data.get('valeur_estimee')}€
Détention: {property_data.get('mode_detention')} ({property_data.get('duree_detention_ans')} ans)
Rendement brut: {property_data.get('rendement_brut')}% | Cashflow: {property_data.get('cashflow_mensuel')}€/mois
Plus-value brute: {property_data.get('plus_value_brute')}€
Crédit restant: {property_data.get('capital_restant_du_total')}€"""

    text = _call_claude(system, prompt)
    return _parse_json(text, {"avis": "Analyse indisponible (clé API manquante)"})


# ─── ANALYSTE FINANCIER ──────────────────────────────────

def analyze_investment_path(path_data: dict) -> dict:
    """Analyse d'un parcours d'investissement par un analyste."""
    system = (
        "Tu es un analyste financier spécialisé dans la gestion de portefeuille pour particuliers français. "
        "Tu maîtrises les ETF, actions, crypto, la fiscalité PEA/AV/CTO, les frais des courtiers, "
        "et les stratégies (DCA, momentum, value). "
        "Réponds en JSON: {avis_global: string, positions_a_renforcer: [], positions_a_alleguer: [], "
        "produits_suggeres: [{symbol, nom, raison}], risques: [], prochain_arbitrage: string}"
    )
    positions_str = "\n".join(
        f"- {p.get('symbol')}: {p.get('quantite')} × {p.get('prix_entree')}€ → {p.get('prix_actuel')}€ (P&L: {p.get('pnl_pct')}%)"
        for p in path_data.get("positions", []) if not p.get("date_sortie")
    )
    prompt = f"""Analyse ce parcours d'investissement:
Nom: {path_data.get('nom')} | Profil: {path_data.get('profil_risque')}
Réactivité: {path_data.get('reactivite')} | Horizon: {path_data.get('maturite_mois')} mois
Mise: {path_data.get('mise_depart')}€ | Valeur: {path_data.get('valeur_actuelle')}€
Objectif: {path_data.get('objectif_sortie')}€ | Progression: {path_data.get('progression_objectif_pct')}%
Enveloppe: {path_data.get('enveloppe')} | Banque: {path_data.get('banque')}

Positions ouvertes:
{positions_str or 'Aucune position'}"""

    text = _call_claude(system, prompt)
    return _parse_json(text, {"avis_global": "Analyse indisponible"})


# ─── CONSEILLER BANCAIRE ─────────────────────────────────

def analyze_cash_situation(cash_data: dict) -> dict:
    """Analyse de la situation cash par un conseiller bancaire."""
    system = (
        "Tu es un conseiller bancaire expert en optimisation de l'épargne réglementée française. "
        "Tu connais les plafonds, taux et conditions de tous les livrets (Livret A 2.4%, LDDS 2.4%, "
        "LEP 3.5%, PEL 2.25%), les comptes à terme, et les alternatives (ETF monétaire, fonds euro). "
        "Réponds en JSON: {avis: string, optimisations: [{action, montant, de, vers, gain_annuel}], "
        "epargne_precaution_ok: bool, taux_epargne_avis: string, budget_avis: string}"
    )
    comptes_str = "\n".join(
        f"- {c.get('nom')}: {c.get('solde')}€ ({c.get('type_compte')}, {c.get('taux_interet')}%)"
        for c in cash_data.get("comptes", [])
    )
    budget = cash_data.get("budget", {})
    prompt = f"""Analyse cette situation cash:
Comptes:
{comptes_str or 'Aucun compte'}

Total: {cash_data.get('total_solde', 0)}€ | Intérêts/an: {cash_data.get('total_interet_annuel', 0)}€
Revenus mensuels: {budget.get('total_revenus', 0) / 3:.0f}€
Dépenses mensuelles: {budget.get('total_depenses', 0) / 3:.0f}€
Taux épargne: {budget.get('taux_epargne_pct', 0)}%"""

    text = _call_claude(system, prompt)
    return _parse_json(text, {"avis": "Analyse indisponible"})


# ─── GESTIONNAIRE DE PATRIMOINE ──────────────────────────

def weekly_patrimoine_digest(dashboard: dict, profile: dict) -> dict:
    """Digest hebdomadaire complet du patrimoine."""
    system = (
        "Tu es un gestionnaire de patrimoine certifié (CGP) français. "
        "Tu analyses le patrimoine global d'un client: immobilier, investissements, cash, "
        "endettement, fiscalité, et objectifs de vie. "
        "Tu adaptes ton analyse à l'âge et aux objectifs du client. "
        "Réponds en JSON: {resume_semaine: string, points_attention: [], "
        "actions_prioritaires: [{action, urgence, impact}], "
        "perspective_6_mois: string, note_globale: string}"
    )
    prompt = f"""Digest hebdomadaire patrimoine:
Profil: {profile.get('prenom')}, {profile.get('age')} ans, {profile.get('situation_familiale')}
Objectif: {profile.get('objectif_principal')} | Horizon: {profile.get('horizon_global')}
Revenu: {profile.get('revenu_net_annuel')}€/an | Épargne: {profile.get('capacite_epargne_mensuelle')}€/mois

Patrimoine net: {dashboard.get('net_worth', 0):,.0f}€
- Immobilier: {dashboard.get('allocation', {}).get('immo', 0):,.0f}€ ({dashboard.get('allocation', {}).get('immo_pct', 0):.0f}%)
- Crypto: {dashboard.get('allocation', {}).get('crypto', 0):,.0f}€ ({dashboard.get('allocation', {}).get('crypto_pct', 0):.0f}%)
- Commodities: {dashboard.get('allocation', {}).get('commodity', 0):,.0f}€ ({dashboard.get('allocation', {}).get('commodity_pct', 0):.0f}%)
- Cash: {dashboard.get('allocation', {}).get('cash', 0):,.0f}€ ({dashboard.get('allocation', {}).get('cash_pct', 0):.0f}%)"""

    text = _call_claude(system, prompt)
    return _parse_json(text, {"resume_semaine": "Digest indisponible"})


def _parse_json(text, fallback):
    if not text:
        return fallback
    try:
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]
        return json.loads(text)
    except Exception:
        return {**fallback, "raw": text[:500]}
