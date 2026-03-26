"""Tests unitaires des modèles et calculs."""

import pytest
import os
import sys
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


def test_real_estate_plus_value():
    """Test du calcul de plus-value immobilière."""
    from models import RealEstate
    prop = RealEstate(
        nom="Test",
        type_bien="locatif_nu",
        prix_achat_net=200000,
        frais_notaire=15000,
        frais_agence=5000,
        prix_achat_total=220000,
        valeur_estimee=300000,
        date_acquisition=date.today() - timedelta(days=365 * 8),  # 8 ans
        montant_travaux_total=0,
        mode_detention="pleine_propriete",
        quote_part_pct=100,
    )
    assert prop.plus_value_brute == 80000  # 300k - 220k
    assert prop.duree_detention_ans >= 7.5
    assert prop.abattement_pv_ir_pct > 0  # 6% par an dès la 6ème année
    assert prop.valeur_nette == 300000  # pas de crédit


def test_real_estate_residence_principale():
    """La résidence principale est exonérée de PV."""
    from models import RealEstate
    prop = RealEstate(
        nom="RP",
        type_bien="residence_principale",
        prix_achat_total=200000,
        valeur_estimee=350000,
    )
    pv = prop.impot_pv_estime
    assert pv["exonere"] is True
    assert pv["total"] == 0


def test_real_estate_rendement():
    """Test du calcul de rendement."""
    from models import RealEstate
    prop = RealEstate(
        nom="Locatif",
        valeur_estimee=100000,
        loyer_mensuel_hc=500,
        charges_copro_mensuelles=50,
        taxe_fonciere_annuelle=600,
    )
    assert prop.rendement_brut == 6.0  # 500*12 / 100000
    assert prop.rendement_net < prop.rendement_brut


def test_cash_types():
    """Test des types de comptes avec taux par défaut."""
    from models import TYPES_COMPTE
    assert TYPES_COMPTE["livret_a"]["taux_defaut"] == 2.4
    assert TYPES_COMPTE["livret_a"]["plafond"] == 22950
    assert TYPES_COMPTE["lep"]["taux_defaut"] == 3.5


def test_investment_path_progression():
    """Test du calcul de progression vers objectif."""
    from models import InvestmentPath
    path = InvestmentPath(
        nom="Test", mise_depart=1000, objectif_sortie=1500,
        valeur_actuelle=1250,
    )
    assert path.rendement_actuel_pct == 25.0
    assert path.progression_objectif_pct == 50.0


def test_investment_position_pnl():
    """Test du calcul P&L d'une position."""
    from models import InvestmentPosition
    pos = InvestmentPosition(
        symbol="BTC", quantite=0.1, prix_entree=30000, prix_actuel=35000,
    )
    assert pos.investi == 3000.0
    assert pos.valeur_actuelle == 3500.0
    assert pos.pnl_eur == 500.0
    assert abs(pos.pnl_pct - 16.67) < 0.1


def test_position_objectif_atteint():
    """Test de détection take profit / stop loss."""
    from models import InvestmentPosition
    pos = InvestmentPosition(
        symbol="ETH", quantite=1, prix_entree=2000,
        prix_actuel=2500, objectif_cours_haut=2400,
    )
    assert pos.objectif_atteint == "take_profit"

    pos2 = InvestmentPosition(
        symbol="ETH", quantite=1, prix_entree=2000,
        prix_actuel=1800, objectif_cours_bas=1900,
    )
    assert pos2.objectif_atteint == "stop_loss"


def test_cash_engine_categorize():
    """Test de la catégorisation automatique."""
    from cash_engine import categorize_transaction
    assert categorize_transaction("SALAIRE ENTREPRISE")["categorie"] == "revenus"
    assert categorize_transaction("CARREFOUR MARKET")["categorie"] == "courses"
    assert categorize_transaction("NETFLIX")["categorie"] == "abonnements"
    assert categorize_transaction("SNCF")["categorie"] == "transport"
    assert categorize_transaction("RANDOM THING")["categorie"] == "autre"


def test_cash_engine_recurring():
    """Test de la détection des récurrences."""
    from cash_engine import detect_recurring
    txs = []
    for i in range(4):
        txs.append({
            "libelle": "LOYER APPARTEMENT",
            "montant": -800,
            "date": (date.today() - timedelta(days=30 * (3 - i))).isoformat(),
        })
    recurring = detect_recurring(txs)
    assert len(recurring) >= 1
    assert recurring[0]["frequence"] == "mensuel"


def test_cash_engine_forecast():
    """Test du prévisionnel."""
    from cash_engine import build_forecast
    recurring = [
        {"libelle": "Salaire", "montant_moyen": 2500, "frequence": "mensuel", "categorie": "revenus", "derniere_date": date.today().isoformat()},
        {"libelle": "Loyer", "montant_moyen": -800, "frequence": "mensuel", "categorie": "logement", "derniere_date": date.today().isoformat()},
    ]
    forecast = build_forecast(5000, recurring, horizon_mois=3)
    assert len(forecast) > 0
    # Le solde devrait augmenter (2500 - 800 = +1700/mois)
    assert forecast[-1]["solde_prevu"] > 5000


def test_patrimoine_opinion():
    """Test de l'opinion patrimoniale."""
    from patrimoine_engine import generate_patrimoine_opinion
    profile = {"age": 35, "profil_risque": "equilibre", "charges_fixes_mensuelles": 1500,
               "epargne_precaution_mois": 3, "capacite_epargne_mensuelle": 500,
               "objectif_principal": "constitution"}
    dashboard = {
        "net_worth": 150000,
        "allocation": {"immo": 100000, "crypto": 20000, "commodity": 5000, "cash": 25000,
                       "immo_pct": 66.7, "crypto_pct": 13.3, "commodity_pct": 3.3, "cash_pct": 16.7},
        "real_estate": [{"cashflow_mensuel": 200, "capital_restant_du_total": 80000, "credit_mensuel_total": 600}],
    }
    opinion = generate_patrimoine_opinion(profile, dashboard)
    assert "score_sante" in opinion
    assert 0 <= opinion["score_sante"] <= 100
    assert len(opinion["opinions"]) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
