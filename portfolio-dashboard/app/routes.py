"""
API Routes - Portfolio Dashboard.
CRUD pour chaque classe d'actifs + dashboard + AI.
"""

from flask import Blueprint, request, jsonify
from models import db, UserProfile, RealEstate, RealEstateLoan, RealEstateWork, CryptoPosition, CommodityPosition, CashAccount, BankTransaction, Transaction, PortfolioSnapshot, InvestmentPath, InvestmentPosition, Arbitrage
from market_data import get_crypto_prices, get_commodity_price, get_commodity_prices
from ai_analyzer import analyze_portfolio
from dvf_service import geocode_address, estimate_price_m2, get_dvf_transactions, get_dvf_history_10y
from patrimoine_engine import generate_patrimoine_opinion
from datetime import date, datetime

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


# ─── PROFIL UTILISATEUR ───────────────────────────────────

@api.route("/profile", methods=["GET"])
def get_profile():
    profile = UserProfile.query.first()
    if not profile:
        return jsonify({"exists": False})
    return jsonify({"exists": True, "profile": profile.to_dict()})


@api.route("/profile", methods=["POST"])
def save_profile():
    data = request.get_json()
    profile = UserProfile.query.first()
    if not profile:
        profile = UserProfile()
        db.session.add(profile)

    import json
    for key in ["prenom", "nom", "email", "age", "situation_familiale", "nb_enfants",
                "nb_parts_fiscales", "regime_matrimonial", "revenu_net_annuel",
                "revenu_foncier_annuel", "autres_revenus_annuel", "charges_fixes_mensuelles",
                "tmi", "option_fiscale", "objectif_principal", "objectif_description",
                "age_objectif", "montant_objectif", "profil_risque", "experience_investissement",
                "horizon_global", "capacite_epargne_mensuelle", "epargne_precaution_mois",
                "has_pea", "has_assurance_vie", "has_per", "has_cto",
                "rgpd_consent"]:
        if key in data:
            setattr(profile, key, data[key])

    if "banques" in data:
        profile.banques = json.dumps(data["banques"]) if isinstance(data["banques"], list) else data["banques"]

    for df in ["date_naissance", "pea_date_ouverture", "av_date_ouverture"]:
        if df in data and data[df]:
            setattr(profile, df, date.fromisoformat(data[df]))

    if data.get("rgpd_consent"):
        profile.rgpd_consent_date = datetime.utcnow()

    db.session.commit()
    return jsonify({"status": "ok", "profile": profile.to_dict()})


@api.route("/profile", methods=["DELETE"])
def delete_profile():
    profile = UserProfile.query.first()
    if profile:
        db.session.delete(profile)
        db.session.commit()
    return jsonify({"status": "ok"})


# ─── OPINION PATRIMOINE GLOBALE ──────────────────────────

@api.route("/patrimoine/opinion")
def patrimoine_opinion():
    """Opinion de gestionnaire de patrimoine sur l'ensemble."""
    profile = UserProfile.query.first()
    if not profile:
        return jsonify({"error": "Profil requis. Configurez votre profil d'abord."})

    dashboard = get_dashboard().get_json()
    opinion = generate_patrimoine_opinion(profile.to_dict(), dashboard)
    return jsonify(opinion)


# ─── GEOCODAGE + DVF ─────────────────────────────────────

@api.route("/geo/geocode")
def api_geocode():
    """Géocode une adresse → lat/lon/code_insee."""
    adresse = request.args.get("adresse", "")
    cp = request.args.get("code_postal", "")
    ville = request.args.get("ville", "")
    return jsonify(geocode_address(adresse, cp, ville))


@api.route("/geo/dvf/estimate")
def api_dvf_estimate():
    """Estimation prix/m² DVF pour un secteur."""
    return jsonify(estimate_price_m2(
        code_insee=request.args.get("code_insee"),
        code_postal=request.args.get("code_postal"),
        lat=float(request.args["lat"]) if request.args.get("lat") else None,
        lon=float(request.args["lon"]) if request.args.get("lon") else None,
        type_bien=request.args.get("type_bien", "appartement"),
        surface_m2=float(request.args.get("surface_m2", 0)),
    ))


@api.route("/geo/dvf/transactions")
def api_dvf_transactions():
    """Transactions DVF récentes autour d'une localisation."""
    txs = get_dvf_transactions(
        code_insee=request.args.get("code_insee"),
        code_postal=request.args.get("code_postal"),
        lat=float(request.args["lat"]) if request.args.get("lat") else None,
        lon=float(request.args["lon"]) if request.args.get("lon") else None,
        type_bien=request.args.get("type_bien"),
    )
    return jsonify(txs[:50])


@api.route("/geo/dvf/history")
def api_dvf_history():
    """Historique DVF 10 ans pour graphique."""
    return jsonify(get_dvf_history_10y(
        code_insee=request.args.get("code_insee"),
        code_postal=request.args.get("code_postal"),
        type_bien=request.args.get("type_bien", "appartement"),
    ))


# ─── IMMOBILIER CRUD ──────────────────────────────────────

@api.route("/real-estate", methods=["GET"])
def list_real_estate():
    props = RealEstate.query.all()
    return jsonify([p.to_dict() for p in props])


@api.route("/real-estate/<int:id>", methods=["GET"])
def get_real_estate(id):
    prop = RealEstate.query.get_or_404(id)
    return jsonify(prop.to_dict())


@api.route("/real-estate", methods=["POST"])
def create_real_estate():
    data = request.get_json()

    # Auto-géocodage si adresse fournie
    lat = data.get("latitude")
    lon = data.get("longitude")
    code_insee = None
    if not lat and data.get("adresse"):
        geo = geocode_address(data.get("adresse", ""), data.get("code_postal", ""), data.get("ville", ""))
        if "error" not in geo:
            lat = geo["latitude"]
            lon = geo["longitude"]
            code_insee = geo.get("code_insee")
            if not data.get("ville"):
                data["ville"] = geo.get("ville", "")
            if not data.get("code_postal"):
                data["code_postal"] = geo.get("code_postal", "")

    # Auto-estimation DVF si surface fournie
    surface = data.get("surface_habitable_m2") or data.get("surface_carrez_m2", 0)
    prix_m2_dvf = 0
    valeur_estimee = data.get("valeur_estimee", 0)
    if surface > 0 and not valeur_estimee:
        est = estimate_price_m2(
            code_insee=code_insee, code_postal=data.get("code_postal"),
            lat=lat, lon=lon,
            type_bien=data.get("type_bien", "appartement"),
            surface_m2=surface,
        )
        prix_m2_dvf = est.get("prix_m2_ajuste", 0)
        valeur_estimee = est.get("estimation_valeur", 0)

    # Calcul prix achat total
    prix_net = data.get("prix_achat_net", 0)
    frais_notaire = data.get("frais_notaire", 0)
    frais_agence = data.get("frais_agence", 0)
    prix_total = data.get("prix_achat_total") or (prix_net + frais_notaire + frais_agence)

    prop = RealEstate(
        nom=data["nom"],
        adresse=data.get("adresse"),
        complement_adresse=data.get("complement_adresse"),
        code_postal=data.get("code_postal"),
        ville=data.get("ville"),
        latitude=lat,
        longitude=lon,
        type_bien=data.get("type_bien"),
        usage=data.get("usage"),
        etage=data.get("etage"),
        nb_pieces=data.get("nb_pieces"),
        nb_chambres=data.get("nb_chambres"),
        nb_sdb=data.get("nb_sdb"),
        annee_construction=data.get("annee_construction"),
        dpe=data.get("dpe"),
        surface_habitable_m2=data.get("surface_habitable_m2", 0),
        surface_carrez_m2=data.get("surface_carrez_m2", 0),
        surface_terrain_m2=data.get("surface_terrain_m2", 0),
        surface_annexes_m2=data.get("surface_annexes_m2", 0),
        nb_parking=data.get("nb_parking", 0),
        mode_detention=data.get("mode_detention", "pleine_propriete"),
        quote_part_pct=data.get("quote_part_pct", 100),
        date_acquisition=date.fromisoformat(data["date_acquisition"]) if data.get("date_acquisition") else None,
        date_mise_en_location=date.fromisoformat(data["date_mise_en_location"]) if data.get("date_mise_en_location") else None,
        prix_achat_net=prix_net,
        frais_notaire=frais_notaire,
        frais_agence=frais_agence,
        prix_achat_total=prix_total,
        prix_m2_dvf=prix_m2_dvf,
        prix_m2_estime=data.get("prix_m2_estime") or prix_m2_dvf,
        valeur_estimee=valeur_estimee,
        date_derniere_estimation=date.today(),
        taxe_fonciere_annuelle=data.get("taxe_fonciere_annuelle", 0),
        charges_copro_mensuelles=data.get("charges_copro_mensuelles", 0),
        assurance_pno_mensuelle=data.get("assurance_pno_mensuelle", 0),
        gestion_locative_pct=data.get("gestion_locative_pct", 0),
        autres_charges_mensuelles=data.get("autres_charges_mensuelles", 0),
        loyer_mensuel_hc=data.get("loyer_mensuel_hc", 0),
        charges_locataire_mensuel=data.get("charges_locataire_mensuel", 0),
        regime_fiscal=data.get("regime_fiscal"),
        notes=data.get("notes"),
    )
    db.session.add(prop)
    db.session.commit()
    return jsonify(prop.to_dict()), 201


@api.route("/real-estate/<int:id>", methods=["PUT"])
def update_real_estate(id):
    prop = RealEstate.query.get_or_404(id)
    data = request.get_json()

    updatable = [
        "nom", "adresse", "complement_adresse", "code_postal", "ville",
        "latitude", "longitude", "type_bien", "usage", "etage",
        "nb_pieces", "nb_chambres", "nb_sdb", "annee_construction", "dpe",
        "surface_habitable_m2", "surface_carrez_m2", "surface_terrain_m2",
        "surface_annexes_m2", "nb_parking", "mode_detention", "quote_part_pct",
        "prix_achat_net", "frais_notaire", "frais_agence", "prix_achat_total",
        "prix_m2_dvf", "prix_m2_estime", "valeur_estimee",
        "montant_travaux_total", "travaux_deductibles",
        "taxe_fonciere_annuelle", "charges_copro_mensuelles",
        "assurance_pno_mensuelle", "gestion_locative_pct", "autres_charges_mensuelles",
        "loyer_mensuel_hc", "charges_locataire_mensuel", "regime_fiscal", "notes",
    ]
    for key in updatable:
        if key in data:
            setattr(prop, key, data[key])

    for date_field in ["date_acquisition", "date_mise_en_location", "date_derniere_estimation"]:
        if date_field in data and data[date_field]:
            setattr(prop, date_field, date.fromisoformat(data[date_field]))

    db.session.commit()
    return jsonify(prop.to_dict())


@api.route("/real-estate/<int:id>", methods=["DELETE"])
def delete_real_estate(id):
    prop = RealEstate.query.get_or_404(id)
    db.session.delete(prop)
    db.session.commit()
    return jsonify({"status": "ok"})


@api.route("/real-estate/<int:id>/refresh-estimate", methods=["POST"])
def refresh_estimate(id):
    """Rafraîchit l'estimation DVF d'un bien."""
    prop = RealEstate.query.get_or_404(id)
    surface = prop.surface_carrez_m2 or prop.surface_habitable_m2
    if surface <= 0:
        return jsonify({"error": "Surface requise pour l'estimation"}), 400

    est = estimate_price_m2(
        code_postal=prop.code_postal,
        lat=prop.latitude, lon=prop.longitude,
        type_bien=prop.type_bien or "appartement",
        surface_m2=surface,
    )

    if est.get("prix_m2_ajuste"):
        prop.prix_m2_dvf = est["prix_m2_ajuste"]
        prop.prix_m2_estime = est["prix_m2_ajuste"]
        prop.valeur_estimee = est["estimation_valeur"]
        prop.date_derniere_estimation = date.today()
        db.session.commit()

    return jsonify({**est, "property": prop.to_dict()})


# ─── PRÊTS IMMOBILIERS ───────────────────────────────────

@api.route("/real-estate/<int:prop_id>/loans", methods=["GET"])
def list_loans(prop_id):
    RealEstate.query.get_or_404(prop_id)
    loans = RealEstateLoan.query.filter_by(property_id=prop_id).all()
    return jsonify([l.to_dict() for l in loans])


@api.route("/real-estate/<int:prop_id>/loans", methods=["POST"])
def create_loan(prop_id):
    RealEstate.query.get_or_404(prop_id)
    data = request.get_json()
    loan = RealEstateLoan(
        property_id=prop_id,
        nom=data.get("nom", "Prêt"),
        type_pret=data.get("type_pret", "classique"),
        banque=data.get("banque"),
        montant_emprunte=data.get("montant_emprunte", 0),
        taux_nominal=data.get("taux_nominal", 0),
        taux_assurance=data.get("taux_assurance", 0),
        duree_mois=data.get("duree_mois", 240),
        date_debut=date.fromisoformat(data["date_debut"]) if data.get("date_debut") else None,
        mensualite_hors_assurance=data.get("mensualite_hors_assurance", 0),
        mensualite_assurance=data.get("mensualite_assurance", 0),
        capital_restant_du=data.get("capital_restant_du", 0),
        en_cours=data.get("en_cours", True),
        notes=data.get("notes"),
    )
    db.session.add(loan)
    db.session.commit()
    return jsonify(loan.to_dict()), 201


@api.route("/real-estate/<int:prop_id>/loans/<int:loan_id>", methods=["PUT"])
def update_loan(prop_id, loan_id):
    loan = RealEstateLoan.query.filter_by(id=loan_id, property_id=prop_id).first_or_404()
    data = request.get_json()
    for key in ["nom", "type_pret", "banque", "montant_emprunte", "taux_nominal",
                "taux_assurance", "duree_mois", "mensualite_hors_assurance",
                "mensualite_assurance", "capital_restant_du", "en_cours", "notes"]:
        if key in data:
            setattr(loan, key, data[key])
    if "date_debut" in data and data["date_debut"]:
        loan.date_debut = date.fromisoformat(data["date_debut"])
    db.session.commit()
    return jsonify(loan.to_dict())


@api.route("/real-estate/<int:prop_id>/loans/<int:loan_id>", methods=["DELETE"])
def delete_loan(prop_id, loan_id):
    loan = RealEstateLoan.query.filter_by(id=loan_id, property_id=prop_id).first_or_404()
    db.session.delete(loan)
    db.session.commit()
    return jsonify({"status": "ok"})


# ─── TRAVAUX ─────────────────────────────────────────────

@api.route("/real-estate/<int:prop_id>/works", methods=["GET"])
def list_works(prop_id):
    RealEstate.query.get_or_404(prop_id)
    works = RealEstateWork.query.filter_by(property_id=prop_id).all()
    return jsonify([w.to_dict() for w in works])


@api.route("/real-estate/<int:prop_id>/works", methods=["POST"])
def create_work(prop_id):
    prop = RealEstate.query.get_or_404(prop_id)
    data = request.get_json()
    work = RealEstateWork(
        property_id=prop_id,
        description=data.get("description"),
        type_travaux=data.get("type_travaux"),
        montant=data.get("montant", 0),
        date_travaux=date.fromisoformat(data["date_travaux"]) if data.get("date_travaux") else None,
        deductible_fiscalement=data.get("deductible_fiscalement", False),
        notes=data.get("notes"),
    )
    db.session.add(work)
    # Mettre à jour le total travaux sur le bien
    prop.montant_travaux_total = sum(w.montant for w in prop.works) + work.montant
    prop.travaux_deductibles = any(w.deductible_fiscalement for w in prop.works) or work.deductible_fiscalement
    db.session.commit()
    return jsonify(work.to_dict()), 201


@api.route("/real-estate/<int:prop_id>/works/<int:work_id>", methods=["DELETE"])
def delete_work(prop_id, work_id):
    work = RealEstateWork.query.filter_by(id=work_id, property_id=prop_id).first_or_404()
    prop = RealEstate.query.get_or_404(prop_id)
    db.session.delete(work)
    db.session.flush()
    prop.montant_travaux_total = sum(w.montant for w in prop.works)
    db.session.commit()
    return jsonify({"status": "ok"})


# ─── RÉSUMÉ IMMOBILIER (pour page d'accueil immo) ────────

@api.route("/real-estate/summary")
def real_estate_summary():
    """Résumé du patrimoine immobilier + historique DVF."""
    props = RealEstate.query.all()

    total_valeur = sum(p.valeur_estimee for p in props)
    total_nette = sum(p.valeur_nette for p in props)
    total_credit = sum(p.capital_restant_du_total for p in props)
    total_loyers = sum(p.loyer_mensuel_hc for p in props)
    total_cashflow = sum(p.cashflow_mensuel for p in props)

    # Historique DVF agrégé (premier bien comme référence)
    dvf_history = []
    if props:
        ref = props[0]
        dvf_history = get_dvf_history_10y(
            code_postal=ref.code_postal,
            type_bien=ref.type_bien or "appartement",
        )

    return jsonify({
        "nb_biens": len(props),
        "total_valeur_estimee": round(total_valeur, 2),
        "total_valeur_nette": round(total_nette, 2),
        "total_credit_restant": round(total_credit, 2),
        "total_loyers_mensuels": round(total_loyers, 2),
        "total_cashflow_mensuel": round(total_cashflow, 2),
        "biens": [p.to_dict() for p in props],
        "dvf_history": dvf_history,
    })


# ─── PARCOURS D'INVESTISSEMENT ────────────────────────────

@api.route("/paths", methods=["GET"])
def list_paths():
    paths = InvestmentPath.query.all()
    return jsonify([p.to_dict() for p in paths])


@api.route("/paths/<int:id>", methods=["GET"])
def get_path(id):
    path = InvestmentPath.query.get_or_404(id)
    return jsonify(path.to_dict())


@api.route("/paths", methods=["POST"])
def create_path():
    data = request.get_json()
    path = InvestmentPath(
        nom=data["nom"],
        description=data.get("description"),
        profil_risque=data.get("profil_risque", "equilibre"),
        reactivite=data.get("reactivite", "moderee"),
        maturite_mois=data.get("maturite_mois", 12),
        mise_depart=data.get("mise_depart", 0),
        objectif_sortie=data.get("objectif_sortie", 0),
        objectif_rendement_pct=data.get("objectif_rendement_pct", 0),
        banque=data.get("banque"),
        enveloppe=data.get("enveloppe", "cto"),
        date_ouverture_enveloppe=date.fromisoformat(data["date_ouverture_enveloppe"]) if data.get("date_ouverture_enveloppe") else None,
        valeur_actuelle=data.get("mise_depart", 0),
    )
    db.session.add(path)
    db.session.commit()
    return jsonify(path.to_dict()), 201


@api.route("/paths/<int:id>", methods=["PUT"])
def update_path(id):
    path = InvestmentPath.query.get_or_404(id)
    data = request.get_json()
    for key in ["nom", "description", "profil_risque", "reactivite", "maturite_mois",
                "mise_depart", "objectif_sortie", "objectif_rendement_pct",
                "banque", "enveloppe", "statut", "valeur_actuelle"]:
        if key in data:
            setattr(path, key, data[key])
    if "date_ouverture_enveloppe" in data and data["date_ouverture_enveloppe"]:
        path.date_ouverture_enveloppe = date.fromisoformat(data["date_ouverture_enveloppe"])
    _recalculate_path(path)
    db.session.commit()
    return jsonify(path.to_dict())


@api.route("/paths/<int:id>", methods=["DELETE"])
def delete_path(id):
    path = InvestmentPath.query.get_or_404(id)
    db.session.delete(path)
    db.session.commit()
    return jsonify({"status": "ok"})


# ─── POSITIONS DANS UN PARCOURS ───────────────────────────

@api.route("/paths/<int:path_id>/positions", methods=["GET"])
def list_positions(path_id):
    InvestmentPath.query.get_or_404(path_id)
    positions = InvestmentPosition.query.filter_by(path_id=path_id).all()
    return jsonify([p.to_dict() for p in positions])


@api.route("/paths/<int:path_id>/positions", methods=["POST"])
def create_position(path_id):
    path = InvestmentPath.query.get_or_404(path_id)
    data = request.get_json()
    pos = InvestmentPosition(
        path_id=path_id,
        symbol=data["symbol"].upper(),
        nom=data.get("nom"),
        type_produit=data.get("type_produit", "etf"),
        quantite=data.get("quantite", 0),
        prix_entree=data.get("prix_entree", 0),
        prix_actuel=data.get("prix_actuel") or data.get("prix_entree", 0),
        date_entree=date.fromisoformat(data["date_entree"]) if data.get("date_entree") else date.today(),
        objectif_cours_haut=data.get("objectif_cours_haut"),
        objectif_cours_bas=data.get("objectif_cours_bas"),
        staking_actif=data.get("staking_actif", False),
        notes=data.get("notes"),
    )
    db.session.add(pos)
    _recalculate_path(path)
    db.session.commit()
    return jsonify(pos.to_dict()), 201


@api.route("/paths/<int:path_id>/positions/<int:pos_id>", methods=["PUT"])
def update_position(path_id, pos_id):
    pos = InvestmentPosition.query.filter_by(id=pos_id, path_id=path_id).first_or_404()
    data = request.get_json()
    for key in ["symbol", "nom", "type_produit", "quantite", "prix_entree",
                "prix_actuel", "prix_sortie", "objectif_cours_haut",
                "objectif_cours_bas", "staking_actif", "rewards_cumules", "notes"]:
        if key in data:
            setattr(pos, key, data[key])
    for df in ["date_entree", "date_sortie"]:
        if df in data and data[df]:
            setattr(pos, df, date.fromisoformat(data[df]))
    path = InvestmentPath.query.get(path_id)
    _recalculate_path(path)
    db.session.commit()
    return jsonify(pos.to_dict())


@api.route("/paths/<int:path_id>/positions/<int:pos_id>/sell", methods=["POST"])
def sell_position(path_id, pos_id):
    """L'utilisateur a vendu : il renseigne le prix de sortie."""
    pos = InvestmentPosition.query.filter_by(id=pos_id, path_id=path_id).first_or_404()
    data = request.get_json()
    pos.prix_sortie = data.get("prix_sortie", pos.prix_actuel)
    pos.date_sortie = date.fromisoformat(data["date_sortie"]) if data.get("date_sortie") else date.today()
    path = InvestmentPath.query.get(path_id)
    _recalculate_path(path)
    db.session.commit()
    return jsonify(pos.to_dict())


# ─── ARBITRAGES ───────────────────────────────────────────

@api.route("/paths/<int:path_id>/arbitrages", methods=["GET"])
def list_arbitrages(path_id):
    InvestmentPath.query.get_or_404(path_id)
    arbs = Arbitrage.query.filter_by(path_id=path_id).order_by(Arbitrage.date_proposition.desc()).all()
    return jsonify([a.to_dict() for a in arbs])


@api.route("/paths/<int:path_id>/arbitrages", methods=["POST"])
def create_arbitrage(path_id):
    """Créer une proposition d'arbitrage (par le système ou manuellement)."""
    InvestmentPath.query.get_or_404(path_id)
    data = request.get_json()
    arb = Arbitrage(
        path_id=path_id,
        type_action=data.get("type_action", "buy"),
        symbol=data.get("symbol"),
        nom_produit=data.get("nom_produit"),
        montant_suggere=data.get("montant_suggere", 0),
        prix_cible=data.get("prix_cible"),
        raison=data.get("raison"),
        symbol_remplacement=data.get("symbol_remplacement"),
        nom_remplacement=data.get("nom_remplacement"),
    )
    db.session.add(arb)
    db.session.commit()
    return jsonify(arb.to_dict()), 201


@api.route("/paths/<int:path_id>/arbitrages/<int:arb_id>", methods=["PUT"])
def update_arbitrage(path_id, arb_id):
    """Accepter/refuser/exécuter un arbitrage."""
    arb = Arbitrage.query.filter_by(id=arb_id, path_id=path_id).first_or_404()
    data = request.get_json()
    if "statut" in data:
        arb.statut = data["statut"]
    if "prix_execution" in data:
        arb.prix_execution = data["prix_execution"]
        arb.date_execution = datetime.utcnow() if not data.get("date_execution") else None
    if "date_execution" in data and data["date_execution"]:
        from datetime import datetime as dt
        arb.date_execution = dt.fromisoformat(data["date_execution"])
    db.session.commit()
    return jsonify(arb.to_dict())


# ─── OPINION QUOTIDIENNE ─────────────────────────────────

@api.route("/paths/<int:path_id>/opinion")
def path_opinion(path_id):
    """Opinion de l'analyste sur un parcours (appelé en page d'accueil)."""
    path = InvestmentPath.query.get_or_404(path_id)
    positions = InvestmentPosition.query.filter_by(path_id=path_id).filter(InvestmentPosition.date_sortie.is_(None)).all()

    opinions = []
    alertes = []

    if not positions:
        opinions.append(f"Parcours '{path.nom}' : aucune position. Lancez votre premier investissement.")
        return jsonify({"opinions": opinions, "alertes": alertes})

    # Analyse par position
    for pos in positions:
        # Vérifier objectifs
        if pos.objectif_atteint == "take_profit":
            alertes.append({
                "type": "take_profit",
                "symbol": pos.symbol,
                "message": f"{pos.symbol} a atteint l'objectif haut ({pos.objectif_cours_haut}€). Prenez vos gains.",
                "urgence": "haute",
            })
        elif pos.objectif_atteint == "stop_loss":
            alertes.append({
                "type": "stop_loss",
                "symbol": pos.symbol,
                "message": f"{pos.symbol} a franchi le stop loss ({pos.objectif_cours_bas}€). Coupez la position.",
                "urgence": "critique",
            })

        # P&L analyse
        if pos.pnl_pct > 10:
            opinions.append(f"{pos.symbol} : +{pos.pnl_pct:.1f}%. Belle performance. Sécurisez une partie des gains ?")
        elif pos.pnl_pct < -5:
            opinions.append(f"{pos.symbol} : {pos.pnl_pct:.1f}%. Sous pression. Vérifiez votre conviction.")

    # Parcours global
    pnl = path.rendement_actuel_pct
    if pnl > 0:
        opinions.append(f"Parcours '{path.nom}' : +{pnl:.1f}% de rendement. Progression vers l'objectif : {path.progression_objectif_pct:.0f}%.")
    elif pnl < -3:
        opinions.append(f"Parcours '{path.nom}' en recul ({pnl:.1f}%). Maintenez la stratégie si votre horizon le permet.")

    if path.progression_objectif_pct >= 100:
        alertes.append({
            "type": "objectif_atteint",
            "symbol": None,
            "message": f"Objectif du parcours '{path.nom}' atteint ! Sécurisez vos gains.",
            "urgence": "haute",
        })

    return jsonify({
        "path_id": path.id,
        "nom": path.nom,
        "rendement_pct": pnl,
        "progression_pct": path.progression_objectif_pct,
        "opinions": opinions,
        "alertes": alertes,
        "nb_positions": len(positions),
        "disclaimer": "Analyse automatique. Ne constitue pas un conseil en investissement.",
    })


# ─── HELPER ──────────────────────────────────────────────

def _recalculate_path(path):
    """Recalcule la valeur actuelle et le P&L d'un parcours."""
    positions = InvestmentPosition.query.filter_by(path_id=path.id).all()
    total = sum(p.valeur_actuelle for p in positions if p.date_sortie is None)
    # Ajouter les gains réalisés (positions vendues)
    realise = sum(p.pnl_eur for p in positions if p.date_sortie is not None)
    path.valeur_actuelle = round(total, 2)
    path.pnl_eur = round(total - path.mise_depart + realise, 2)
    path.pnl_pct = round(path.pnl_eur / path.mise_depart * 100, 2) if path.mise_depart > 0 else 0


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
    from models import TYPES_COMPTE
    type_info = TYPES_COMPTE.get(data.get("type_compte", "autre"), {})
    account = CashAccount(
        nom=data["nom"],
        type_compte=data.get("type_compte"),
        banque=data.get("banque"),
        numero_compte=data.get("numero_compte"),
        solde=data.get("solde", 0),
        solde_date=date.fromisoformat(data["solde_date"]) if data.get("solde_date") else date.today(),
        taux_interet=data.get("taux_interet") or type_info.get("taux_defaut", 0),
        plafond=data.get("plafond") or type_info.get("plafond"),
        date_ouverture=date.fromisoformat(data["date_ouverture"]) if data.get("date_ouverture") else None,
        est_compte_joint=data.get("est_compte_joint", False),
        notes=data.get("notes"),
    )
    db.session.add(account)
    db.session.commit()
    return jsonify(account.to_dict()), 201


@api.route("/cash/<int:id>", methods=["PUT"])
def update_cash(id):
    account = CashAccount.query.get_or_404(id)
    data = request.get_json()
    for key in ["nom", "type_compte", "banque", "numero_compte", "solde",
                "taux_interet", "plafond", "est_compte_joint", "notes"]:
        if key in data:
            setattr(account, key, data[key])
    for df in ["solde_date", "date_ouverture"]:
        if df in data and data[df]:
            setattr(account, df, date.fromisoformat(data[df]))
    db.session.commit()
    return jsonify(account.to_dict())


@api.route("/cash/<int:id>", methods=["DELETE"])
def delete_cash(id):
    account = CashAccount.query.get_or_404(id)
    db.session.delete(account)
    db.session.commit()
    return jsonify({"status": "ok"})


# ─── CONNEXION BANCAIRE API ───────────────────────────────

@api.route("/banking/status")
def banking_status():
    """Vérifie si l'API bancaire est configurée."""
    from banking_api import is_configured
    return jsonify({"configured": is_configured()})


@api.route("/banking/institutions")
def banking_institutions():
    """Liste les banques disponibles pour connexion."""
    from banking_api import list_institutions
    country = request.args.get("country", "FR")
    return jsonify(list_institutions(country))


@api.route("/banking/connect", methods=["POST"])
def banking_connect():
    """Crée un lien de connexion vers une banque."""
    from banking_api import create_bank_link
    data = request.get_json()
    institution_id = data.get("institution_id")
    redirect_url = data.get("redirect_url", "https://dashboard.5ginvest.fr/banking/callback")
    if not institution_id:
        return jsonify({"error": "institution_id requis"}), 400
    result = create_bank_link(institution_id, redirect_url)
    return jsonify(result)


@api.route("/banking/requisition/<requisition_id>/status")
def banking_requisition_status(requisition_id):
    """Vérifie le statut d'une connexion."""
    from banking_api import get_requisition_status
    return jsonify(get_requisition_status(requisition_id))


@api.route("/banking/requisition/<requisition_id>/sync", methods=["POST"])
def banking_sync(requisition_id):
    """
    Synchronise les comptes et transactions d'une connexion.
    Crée/met à jour les CashAccount et importe les BankTransactions.
    """
    from banking_api import sync_all_accounts
    from cash_engine import categorize_transaction

    accounts = sync_all_accounts(requisition_id)
    synced = []

    for acc in accounts:
        if "error" in acc:
            synced.append(acc)
            continue

        # Trouver ou créer le compte
        from models import TYPES_COMPTE
        existing = CashAccount.query.filter_by(numero_compte=acc.get("iban")).first()
        if not existing:
            type_info = TYPES_COMPTE.get(acc.get("type", "ccp"), {})
            existing = CashAccount(
                nom=acc.get("name", "Compte"),
                type_compte=acc.get("type", "ccp"),
                banque=acc.get("owner_name", ""),
                numero_compte=acc.get("iban", "")[-8:] if acc.get("iban") else "",
                solde=acc.get("solde", 0),
                solde_date=date.today(),
                taux_interet=type_info.get("taux_defaut", 0),
                plafond=type_info.get("plafond"),
            )
            db.session.add(existing)
            db.session.flush()
        else:
            existing.solde = acc.get("solde", existing.solde)
            existing.solde_date = date.today()

        # Importer les transactions (éviter les doublons via reference)
        imported = 0
        for tx_data in acc.get("transactions", []):
            ref = tx_data.get("reference", "")
            if ref and BankTransaction.query.filter_by(account_id=existing.id, reference=ref).first():
                continue

            cat = categorize_transaction(tx_data.get("libelle", ""))
            tx = BankTransaction(
                account_id=existing.id,
                date=date.fromisoformat(tx_data["date"]) if tx_data.get("date") else date.today(),
                libelle=tx_data.get("libelle", ""),
                montant=tx_data.get("montant", 0),
                categorie=cat["categorie"],
                sous_categorie=cat["sous_categorie"],
                source="api_bancaire",
                reference=ref,
            )
            db.session.add(tx)
            imported += 1

        synced.append({
            "account_id": existing.id,
            "nom": existing.nom,
            "solde": existing.solde,
            "transactions_imported": imported,
        })

    db.session.commit()
    return jsonify({"status": "ok", "accounts": synced})


# ─── TRANSACTIONS BANCAIRES ──────────────────────────────

@api.route("/cash/<int:account_id>/transactions", methods=["GET"])
def list_bank_transactions(account_id):
    CashAccount.query.get_or_404(account_id)
    txs = BankTransaction.query.filter_by(account_id=account_id).order_by(BankTransaction.date.desc()).limit(200).all()
    return jsonify([t.to_dict() for t in txs])


@api.route("/cash/<int:account_id>/transactions", methods=["POST"])
def create_bank_transaction(account_id):
    """Ajouter une transaction (auto-catégorisée)."""
    CashAccount.query.get_or_404(account_id)
    data = request.get_json()
    from cash_engine import categorize_transaction
    cat = categorize_transaction(data.get("libelle", ""))

    tx = BankTransaction(
        account_id=account_id,
        date=date.fromisoformat(data["date"]) if data.get("date") else date.today(),
        libelle=data.get("libelle"),
        montant=data.get("montant", 0),
        categorie=data.get("categorie") or cat["categorie"],
        sous_categorie=data.get("sous_categorie") or cat["sous_categorie"],
        est_recurrent=data.get("est_recurrent", False),
        frequence=data.get("frequence"),
        source=data.get("source", "manuel"),
        reference=data.get("reference"),
    )
    db.session.add(tx)
    db.session.commit()
    return jsonify(tx.to_dict()), 201


@api.route("/cash/<int:account_id>/transactions/import", methods=["POST"])
def import_bank_transactions(account_id):
    """Import en lot de transactions (depuis CSV ou API bancaire)."""
    CashAccount.query.get_or_404(account_id)
    data = request.get_json()
    transactions = data.get("transactions", [])
    from cash_engine import categorize_batch
    categorize_batch(transactions)

    created = 0
    for tx_data in transactions:
        tx = BankTransaction(
            account_id=account_id,
            date=date.fromisoformat(tx_data["date"]) if tx_data.get("date") else date.today(),
            libelle=tx_data.get("libelle"),
            montant=tx_data.get("montant", 0),
            categorie=tx_data.get("categorie", "autre"),
            sous_categorie=tx_data.get("sous_categorie", "autre"),
            est_recurrent=tx_data.get("est_recurrent", False),
            source=tx_data.get("source", "import"),
            reference=tx_data.get("reference"),
        )
        db.session.add(tx)
        created += 1

    db.session.commit()
    return jsonify({"status": "ok", "imported": created})


# ─── ANALYSE CASH / PRÉVISIONNEL ─────────────────────────

@api.route("/cash/<int:account_id>/analysis")
def cash_analysis(account_id):
    """Analyse complète d'un compte: récurrences, budget, prévisionnel."""
    account = CashAccount.query.get_or_404(account_id)
    txs = BankTransaction.query.filter_by(account_id=account_id).order_by(BankTransaction.date.desc()).all()
    tx_dicts = [t.to_dict() for t in txs]

    from cash_engine import detect_recurring, build_forecast, build_budget_summary

    recurring = detect_recurring(tx_dicts)
    budget = build_budget_summary(tx_dicts, mois=3)

    # Prévisionnel 3, 6, 12 mois
    forecast_3 = build_forecast(account.solde, recurring, horizon_mois=3)
    forecast_6 = build_forecast(account.solde, recurring, horizon_mois=6)
    forecast_12 = build_forecast(account.solde, recurring, horizon_mois=12)

    return jsonify({
        "account": account.to_dict(),
        "recurring": recurring,
        "budget": budget,
        "forecast": {
            "3_mois": forecast_3,
            "6_mois": forecast_6,
            "12_mois": forecast_12,
        },
    })


@api.route("/cash/summary")
def cash_summary():
    """Résumé global de tous les comptes cash."""
    accounts = CashAccount.query.all()
    total_solde = sum(a.solde for a in accounts)
    total_interet = sum(a.interet_annuel_estime for a in accounts)

    # Propositions d'optimisation
    propositions = []
    for a in accounts:
        if a.type_compte == "ccp" and a.solde > 5000:
            propositions.append({
                "type": "optimisation",
                "compte": a.nom,
                "message": f"{a.nom}: {a.solde:.0f}€ sur compte courant (0%). "
                           f"Transférez {a.solde - 2000:.0f}€ vers un livret rémunéré.",
            })
        if a.plafond and a.remplissage_pct and a.remplissage_pct < 50 and a.taux_interet >= 2:
            propositions.append({
                "type": "remplissage",
                "compte": a.nom,
                "message": f"{a.nom}: rempli à {a.remplissage_pct:.0f}% seulement. "
                           f"Espace disponible: {a.plafond - a.solde:.0f}€ à {a.taux_interet}%.",
            })

    return jsonify({
        "nb_comptes": len(accounts),
        "total_solde": round(total_solde, 2),
        "total_interet_annuel": round(total_interet, 2),
        "comptes": [a.to_dict() for a in accounts],
        "propositions": propositions,
    })


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
