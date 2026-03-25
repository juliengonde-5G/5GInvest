"""
API Routes - Portfolio Dashboard.
CRUD pour chaque classe d'actifs + dashboard + AI.
"""

from flask import Blueprint, request, jsonify
from models import db, RealEstate, CryptoPosition, CommodityPosition, CashAccount, Transaction, PortfolioSnapshot
from market_data import get_crypto_prices, get_commodity_price, get_commodity_prices
from ai_analyzer import analyze_portfolio
from datetime import date

api = Blueprint("api", __name__, url_prefix="/api")


# ─── DASHBOARD (agrégé) ──────────────────────────────────

@api.route("/dashboard")
def get_dashboard():
    """Données complètes du dashboard: net worth, allocation, positions."""
    # Immobilier
    properties = RealEstate.query.all()
    immo_data = [p.to_dict() for p in properties]
    immo_total = sum(p.valeur_nette for p in properties)

    # Crypto
    crypto_positions = CryptoPosition.query.all()
    crypto_symbols = list(set(p.symbol for p in crypto_positions))
    crypto_prices = get_crypto_prices(crypto_symbols) if crypto_symbols else {}
    crypto_data = [p.to_dict(crypto_prices.get(p.symbol)) for p in crypto_positions]
    crypto_total = sum(d["current_value"] for d in crypto_data)

    # Commodities
    commodity_positions = CommodityPosition.query.all()
    commodity_data = []
    commodity_total = 0
    for p in commodity_positions:
        price = get_commodity_price(p.symbol)
        d = p.to_dict(price)
        commodity_data.append(d)
        commodity_total += d["current_value"]

    # Cash
    cash_accounts = CashAccount.query.all()
    cash_data = [a.to_dict() for a in cash_accounts]
    cash_total = sum(a.solde for a in cash_accounts)

    # Net worth
    net_worth = immo_total + crypto_total + commodity_total + cash_total

    # Allocation
    allocation = {
        "immo": round(immo_total, 2),
        "crypto": round(crypto_total, 2),
        "commodity": round(commodity_total, 2),
        "cash": round(cash_total, 2),
        "immo_pct": round(immo_total / net_worth * 100, 1) if net_worth > 0 else 0,
        "crypto_pct": round(crypto_total / net_worth * 100, 1) if net_worth > 0 else 0,
        "commodity_pct": round(commodity_total / net_worth * 100, 1) if net_worth > 0 else 0,
        "cash_pct": round(cash_total / net_worth * 100, 1) if net_worth > 0 else 0,
    }

    # Historique
    snapshots = PortfolioSnapshot.query.order_by(PortfolioSnapshot.date.desc()).limit(365).all()
    history = [s.to_dict() for s in reversed(snapshots)]

    return jsonify({
        "net_worth": round(net_worth, 2),
        "allocation": allocation,
        "real_estate": immo_data,
        "crypto": crypto_data,
        "commodities": commodity_data,
        "cash": cash_data,
        "history": history,
    })


# ─── AI ANALYSIS ──────────────────────────────────────────

@api.route("/ai/analyze", methods=["POST"])
def ai_analyze():
    """Analyse IA du portefeuille."""
    dashboard = get_dashboard().get_json()
    result = analyze_portfolio(dashboard)
    return jsonify(result)


# ─── SNAPSHOT (appelé par cron daily) ─────────────────────

@api.route("/snapshot", methods=["POST"])
def take_snapshot():
    """Enregistre un snapshot quotidien du portefeuille."""
    today = date.today()
    existing = PortfolioSnapshot.query.filter_by(date=today).first()
    if existing:
        return jsonify({"status": "already_exists"})

    dashboard = get_dashboard().get_json()
    alloc = dashboard["allocation"]

    snap = PortfolioSnapshot(
        date=today,
        net_worth=dashboard["net_worth"],
        immo_value=alloc["immo"],
        crypto_value=alloc["crypto"],
        commodity_value=alloc["commodity"],
        cash_value=alloc["cash"],
    )
    db.session.add(snap)
    db.session.commit()
    return jsonify({"status": "ok", "snapshot": snap.to_dict()})


# ─── IMMOBILIER CRUD ──────────────────────────────────────

@api.route("/real-estate", methods=["GET"])
def list_real_estate():
    props = RealEstate.query.all()
    return jsonify([p.to_dict() for p in props])


@api.route("/real-estate", methods=["POST"])
def create_real_estate():
    data = request.get_json()
    prop = RealEstate(
        nom=data["nom"],
        adresse=data.get("adresse"),
        ville=data.get("ville"),
        code_postal=data.get("code_postal"),
        type_bien=data.get("type_bien"),
        surface_m2=data.get("surface_m2", 0),
        prix_achat=data.get("prix_achat", 0),
        date_achat=date.fromisoformat(data["date_achat"]) if data.get("date_achat") else None,
        prix_m2_estime=data.get("prix_m2_estime", 0),
        valeur_estimee=data.get("valeur_estimee") or data.get("surface_m2", 0) * data.get("prix_m2_estime", 0),
        travaux_realises=data.get("travaux_realises", 0),
        loyer_mensuel=data.get("loyer_mensuel", 0),
        charges_mensuelles=data.get("charges_mensuelles", 0),
        credit_mensuel=data.get("credit_mensuel", 0),
        capital_restant_du=data.get("capital_restant_du", 0),
        notes=data.get("notes"),
    )
    db.session.add(prop)
    db.session.commit()
    return jsonify(prop.to_dict()), 201


@api.route("/real-estate/<int:id>", methods=["PUT"])
def update_real_estate(id):
    prop = RealEstate.query.get_or_404(id)
    data = request.get_json()
    for key in ["nom", "adresse", "ville", "code_postal", "type_bien", "surface_m2",
                "prix_achat", "prix_m2_estime", "valeur_estimee", "travaux_realises",
                "loyer_mensuel", "charges_mensuelles", "credit_mensuel",
                "capital_restant_du", "notes"]:
        if key in data:
            setattr(prop, key, data[key])
    if "date_achat" in data and data["date_achat"]:
        prop.date_achat = date.fromisoformat(data["date_achat"])
    db.session.commit()
    return jsonify(prop.to_dict())


@api.route("/real-estate/<int:id>", methods=["DELETE"])
def delete_real_estate(id):
    prop = RealEstate.query.get_or_404(id)
    db.session.delete(prop)
    db.session.commit()
    return jsonify({"status": "ok"})


# ─── CRYPTO CRUD ──────────────────────────────────────────

@api.route("/crypto", methods=["GET"])
def list_crypto():
    positions = CryptoPosition.query.all()
    symbols = list(set(p.symbol for p in positions))
    prices = get_crypto_prices(symbols) if symbols else {}
    return jsonify([p.to_dict(prices.get(p.symbol)) for p in positions])


@api.route("/crypto", methods=["POST"])
def create_crypto():
    data = request.get_json()
    pos = CryptoPosition(
        symbol=data["symbol"].upper(),
        nom=data.get("nom"),
        quantite=data.get("quantite", 0),
        prix_achat_moyen=data.get("prix_achat_moyen", 0),
        plateforme=data.get("plateforme"),
        notes=data.get("notes"),
    )
    db.session.add(pos)
    db.session.commit()
    price = get_crypto_prices([pos.symbol]).get(pos.symbol)
    return jsonify(pos.to_dict(price)), 201


@api.route("/crypto/<int:id>", methods=["PUT"])
def update_crypto(id):
    pos = CryptoPosition.query.get_or_404(id)
    data = request.get_json()
    for key in ["symbol", "nom", "quantite", "prix_achat_moyen", "plateforme", "notes"]:
        if key in data:
            setattr(pos, key, data[key])
    db.session.commit()
    price = get_crypto_prices([pos.symbol]).get(pos.symbol)
    return jsonify(pos.to_dict(price))


@api.route("/crypto/<int:id>", methods=["DELETE"])
def delete_crypto(id):
    pos = CryptoPosition.query.get_or_404(id)
    db.session.delete(pos)
    db.session.commit()
    return jsonify({"status": "ok"})


# ─── COMMODITIES CRUD ────────────────────────────────────

@api.route("/commodities", methods=["GET"])
def list_commodities():
    positions = CommodityPosition.query.all()
    return jsonify([p.to_dict(get_commodity_price(p.symbol)) for p in positions])


@api.route("/commodities", methods=["POST"])
def create_commodity():
    data = request.get_json()
    pos = CommodityPosition(
        symbol=data["symbol"].upper(),
        nom=data.get("nom"),
        type_produit=data.get("type_produit"),
        quantite=data.get("quantite", 0),
        prix_achat_moyen=data.get("prix_achat_moyen", 0),
        devise=data.get("devise", "EUR"),
        plateforme=data.get("plateforme"),
        notes=data.get("notes"),
    )
    db.session.add(pos)
    db.session.commit()
    price = get_commodity_price(pos.symbol)
    return jsonify(pos.to_dict(price)), 201


@api.route("/commodities/<int:id>", methods=["PUT"])
def update_commodity(id):
    pos = CommodityPosition.query.get_or_404(id)
    data = request.get_json()
    for key in ["symbol", "nom", "type_produit", "quantite", "prix_achat_moyen", "devise", "plateforme", "notes"]:
        if key in data:
            setattr(pos, key, data[key])
    db.session.commit()
    price = get_commodity_price(pos.symbol)
    return jsonify(pos.to_dict(price))


@api.route("/commodities/<int:id>", methods=["DELETE"])
def delete_commodity(id):
    pos = CommodityPosition.query.get_or_404(id)
    db.session.delete(pos)
    db.session.commit()
    return jsonify({"status": "ok"})


# ─── CASH CRUD ────────────────────────────────────────────

@api.route("/cash", methods=["GET"])
def list_cash():
    accounts = CashAccount.query.all()
    return jsonify([a.to_dict() for a in accounts])


@api.route("/cash", methods=["POST"])
def create_cash():
    data = request.get_json()
    account = CashAccount(
        nom=data["nom"],
        type_compte=data.get("type_compte"),
        banque=data.get("banque"),
        solde=data.get("solde", 0),
        taux_interet=data.get("taux_interet", 0),
        plafond=data.get("plafond"),
        notes=data.get("notes"),
    )
    db.session.add(account)
    db.session.commit()
    return jsonify(account.to_dict()), 201


@api.route("/cash/<int:id>", methods=["PUT"])
def update_cash(id):
    account = CashAccount.query.get_or_404(id)
    data = request.get_json()
    for key in ["nom", "type_compte", "banque", "solde", "taux_interet", "plafond", "notes"]:
        if key in data:
            setattr(account, key, data[key])
    db.session.commit()
    return jsonify(account.to_dict())


@api.route("/cash/<int:id>", methods=["DELETE"])
def delete_cash(id):
    account = CashAccount.query.get_or_404(id)
    db.session.delete(account)
    db.session.commit()
    return jsonify({"status": "ok"})


# ─── TRANSACTIONS ─────────────────────────────────────────

@api.route("/transactions", methods=["GET"])
def list_transactions():
    txs = Transaction.query.order_by(Transaction.date.desc()).limit(100).all()
    return jsonify([t.to_dict() for t in txs])


@api.route("/transactions", methods=["POST"])
def create_transaction():
    data = request.get_json()
    tx = Transaction(
        date=date.fromisoformat(data["date"]) if data.get("date") else date.today(),
        type_actif=data.get("type_actif"),
        actif_id=data.get("actif_id"),
        action=data.get("action"),
        montant=data.get("montant", 0),
        quantite=data.get("quantite"),
        prix_unitaire=data.get("prix_unitaire"),
        frais=data.get("frais", 0),
        notes=data.get("notes"),
    )
    db.session.add(tx)
    db.session.commit()
    return jsonify(tx.to_dict()), 201
