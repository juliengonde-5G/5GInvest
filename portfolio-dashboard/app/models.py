"""
Modèles SQLAlchemy - Portfolio multi-actifs.
Tables: immobilier, crypto, commodities, cash, transactions.
"""

from datetime import datetime, date
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


# ─── IMMOBILIER ───────────────────────────────────────────

class RealEstate(db.Model):
    """Bien immobilier avec toutes les données d'expertise."""
    __tablename__ = "real_estate"

    id = db.Column(db.Integer, primary_key=True)

    # Identification
    nom = db.Column(db.String(200), nullable=False)
    adresse = db.Column(db.String(500))
    complement_adresse = db.Column(db.String(200))
    code_postal = db.Column(db.String(10))
    ville = db.Column(db.String(100))
    pays = db.Column(db.String(50), default="France")
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)

    # Type et usage
    type_bien = db.Column(db.String(50))
    # résidence_principale, résidence_secondaire, locatif_nu, locatif_meuble,
    # lmnp, lmp, parking, terrain, scpi, immeuble_rapport, local_commercial
    usage = db.Column(db.String(50))  # habitation, commercial, mixte, terrain
    etage = db.Column(db.Integer)
    nb_pieces = db.Column(db.Integer)
    nb_chambres = db.Column(db.Integer)
    nb_sdb = db.Column(db.Integer)
    annee_construction = db.Column(db.Integer)
    dpe = db.Column(db.String(1))  # A à G

    # Surfaces
    surface_habitable_m2 = db.Column(db.Float, default=0)
    surface_carrez_m2 = db.Column(db.Float, default=0)
    surface_terrain_m2 = db.Column(db.Float, default=0)
    surface_annexes_m2 = db.Column(db.Float, default=0)  # cave, grenier, balcon pondéré
    nb_parking = db.Column(db.Integer, default=0)

    # Détention
    mode_detention = db.Column(db.String(50), default="pleine_propriete")
    # pleine_propriete, sci_ir, sci_is, indivision, usufruit, nue_propriete, demembrement
    quote_part_pct = db.Column(db.Float, default=100)  # % de détention (indivision, SCI)
    date_acquisition = db.Column(db.Date)
    date_mise_en_location = db.Column(db.Date)  # si locatif

    # Acquisition
    prix_achat_net = db.Column(db.Float, default=0)  # prix net vendeur
    frais_notaire = db.Column(db.Float, default=0)
    frais_agence = db.Column(db.Float, default=0)
    prix_achat_total = db.Column(db.Float, default=0)  # net + notaire + agence

    # Estimation actuelle
    prix_m2_dvf = db.Column(db.Float, default=0)  # dernière DVF du secteur
    prix_m2_estime = db.Column(db.Float, default=0)  # estimation ajustée
    valeur_estimee = db.Column(db.Float, default=0)
    date_derniere_estimation = db.Column(db.Date)

    # Travaux (montant total, le détail est dans RealEstateWork)
    montant_travaux_total = db.Column(db.Float, default=0)
    travaux_deductibles = db.Column(db.Boolean, default=False)

    # Charges (mensuelles)
    taxe_fonciere_annuelle = db.Column(db.Float, default=0)
    charges_copro_mensuelles = db.Column(db.Float, default=0)
    assurance_pno_mensuelle = db.Column(db.Float, default=0)  # propriétaire non occupant
    gestion_locative_pct = db.Column(db.Float, default=0)  # % des loyers si gestion déléguée
    autres_charges_mensuelles = db.Column(db.Float, default=0)

    # Revenus (si locatif)
    loyer_mensuel_hc = db.Column(db.Float, default=0)
    charges_locataire_mensuel = db.Column(db.Float, default=0)
    regime_fiscal = db.Column(db.String(50))
    # micro_foncier, reel, lmnp_micro_bic, lmnp_reel, lmp, sci_ir, sci_is

    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    loans = db.relationship("RealEstateLoan", backref="property", cascade="all,delete-orphan", lazy=True)
    works = db.relationship("RealEstateWork", backref="property", cascade="all,delete-orphan", lazy=True)

    @property
    def charges_mensuelles_totales(self):
        return round(
            self.charges_copro_mensuelles
            + self.assurance_pno_mensuelle
            + self.autres_charges_mensuelles
            + self.taxe_fonciere_annuelle / 12
            + (self.loyer_mensuel_hc * self.gestion_locative_pct / 100 if self.gestion_locative_pct else 0),
            2
        )

    @property
    def credit_mensuel_total(self):
        return round(sum(l.mensualite_totale for l in self.loans if l.en_cours), 2)

    @property
    def capital_restant_du_total(self):
        return round(sum(l.capital_restant_du for l in self.loans if l.en_cours), 2)

    @property
    def rendement_brut(self):
        if self.valeur_estimee and self.valeur_estimee > 0 and self.loyer_mensuel_hc > 0:
            return round((self.loyer_mensuel_hc * 12) / self.valeur_estimee * 100, 2)
        return 0

    @property
    def rendement_net(self):
        if self.valeur_estimee and self.valeur_estimee > 0 and self.loyer_mensuel_hc > 0:
            revenu_net = (self.loyer_mensuel_hc - self.charges_mensuelles_totales) * 12
            return round(revenu_net / self.valeur_estimee * 100, 2)
        return 0

    @property
    def cashflow_mensuel(self):
        return round(
            self.loyer_mensuel_hc
            - self.charges_mensuelles_totales
            - self.credit_mensuel_total,
            2
        )

    @property
    def valeur_nette(self):
        """Valeur estimée * quote-part - capital restant dû."""
        v = self.valeur_estimee * self.quote_part_pct / 100
        return round(v - self.capital_restant_du_total, 2)

    @property
    def plus_value_brute(self):
        """Plus-value brute = valeur estimée - prix d'achat total - travaux."""
        return round(self.valeur_estimee - self.prix_achat_total - self.montant_travaux_total, 2)

    @property
    def duree_detention_ans(self):
        if self.date_acquisition:
            delta = date.today() - self.date_acquisition
            return round(delta.days / 365.25, 1)
        return 0

    @property
    def abattement_pv_ir_pct(self):
        """Abattement IR sur PV immobilière selon durée détention."""
        ans = int(self.duree_detention_ans)
        if ans <= 5:
            return 0
        elif ans <= 21:
            return min((ans - 5) * 6, 100)  # 6% par an de la 6e à la 21e année
        elif ans == 22:
            return 100  # Exonération IR totale
        return 100

    @property
    def abattement_pv_ps_pct(self):
        """Abattement PS sur PV immobilière selon durée détention."""
        ans = int(self.duree_detention_ans)
        if ans <= 5:
            return 0
        elif ans <= 21:
            return min((ans - 5) * 1.65, 100)
        elif ans <= 22:
            return 28.5  # 1.65*16 + 1.6*1
        elif ans <= 30:
            return min(28.5 + (ans - 22) * 9, 100)
        return 100  # Exonération totale après 30 ans

    @property
    def plus_value_imposable(self):
        """PV imposable après abattements."""
        pv_brute = max(0, self.plus_value_brute)
        # Forfait travaux 15% après 5 ans si pas de travaux déclarés
        if not self.travaux_deductibles and self.duree_detention_ans >= 5:
            pv_brute = max(0, pv_brute - self.prix_achat_total * 0.15)
        pv_ir = pv_brute * (1 - self.abattement_pv_ir_pct / 100)
        pv_ps = pv_brute * (1 - self.abattement_pv_ps_pct / 100)
        return {"ir": round(pv_ir, 2), "ps": round(pv_ps, 2)}

    @property
    def impot_pv_estime(self):
        """Estimation de l'impôt sur la plus-value à la revente."""
        pv = self.plus_value_imposable
        # Résidence principale = exonérée
        if self.type_bien == "residence_principale":
            return {"ir": 0, "ps": 0, "total": 0, "exonere": True, "raison": "Résidence principale"}
        impot_ir = pv["ir"] * 0.19  # 19% IR
        impot_ps = pv["ps"] * 0.172  # 17.2% PS
        # Surtaxe si PV > 50k
        surtaxe = 0
        pv_brute = max(0, self.plus_value_brute)
        if pv_brute > 50000:
            surtaxe = pv_brute * 0.06  # Simplifié, barème réel est progressif
        total = impot_ir + impot_ps + surtaxe
        return {
            "ir": round(impot_ir, 2), "ps": round(impot_ps, 2),
            "surtaxe": round(surtaxe, 2), "total": round(total, 2),
            "exonere": total == 0,
            "raison": f"Détention {self.duree_detention_ans:.0f} ans, abattement IR {self.abattement_pv_ir_pct}%",
        }

    @property
    def prix_vente_net_vendeur(self):
        """Prix de vente conseillé (valeur estimée - impôt PV)."""
        return round(self.valeur_estimee - self.impot_pv_estime["total"], 2)

    def to_dict(self):
        return {
            "id": self.id,
            "nom": self.nom,
            "adresse": self.adresse,
            "complement_adresse": self.complement_adresse,
            "code_postal": self.code_postal,
            "ville": self.ville,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "type_bien": self.type_bien,
            "usage": self.usage,
            "etage": self.etage,
            "nb_pieces": self.nb_pieces,
            "nb_chambres": self.nb_chambres,
            "annee_construction": self.annee_construction,
            "dpe": self.dpe,
            "surface_habitable_m2": self.surface_habitable_m2,
            "surface_carrez_m2": self.surface_carrez_m2,
            "surface_terrain_m2": self.surface_terrain_m2,
            "nb_parking": self.nb_parking,
            "mode_detention": self.mode_detention,
            "quote_part_pct": self.quote_part_pct,
            "date_acquisition": self.date_acquisition.isoformat() if self.date_acquisition else None,
            "duree_detention_ans": self.duree_detention_ans,
            "prix_achat_net": self.prix_achat_net,
            "frais_notaire": self.frais_notaire,
            "frais_agence": self.frais_agence,
            "prix_achat_total": self.prix_achat_total,
            "prix_m2_dvf": self.prix_m2_dvf,
            "prix_m2_estime": self.prix_m2_estime,
            "valeur_estimee": self.valeur_estimee,
            "montant_travaux_total": self.montant_travaux_total,
            "taxe_fonciere_annuelle": self.taxe_fonciere_annuelle,
            "charges_copro_mensuelles": self.charges_copro_mensuelles,
            "charges_mensuelles_totales": self.charges_mensuelles_totales,
            "loyer_mensuel_hc": self.loyer_mensuel_hc,
            "regime_fiscal": self.regime_fiscal,
            "rendement_brut": self.rendement_brut,
            "rendement_net": self.rendement_net,
            "credit_mensuel_total": self.credit_mensuel_total,
            "capital_restant_du_total": self.capital_restant_du_total,
            "cashflow_mensuel": self.cashflow_mensuel,
            "valeur_nette": self.valeur_nette,
            "plus_value_brute": self.plus_value_brute,
            "impot_pv_estime": self.impot_pv_estime,
            "prix_vente_net_vendeur": self.prix_vente_net_vendeur,
            "loans": [l.to_dict() for l in self.loans],
            "works": [w.to_dict() for w in self.works],
            "notes": self.notes,
        }


class RealEstateLoan(db.Model):
    """Prêt immobilier (multi-financement par bien)."""
    __tablename__ = "real_estate_loans"

    id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer, db.ForeignKey("real_estate.id"), nullable=False)

    nom = db.Column(db.String(100))  # "Prêt principal", "PTZ", "Prêt relais"
    type_pret = db.Column(db.String(50))
    # classique, ptz, pret_relais, in_fine, taux_variable, pret_employeur
    banque = db.Column(db.String(100))
    montant_emprunte = db.Column(db.Float, default=0)
    taux_nominal = db.Column(db.Float, default=0)  # % annuel
    taux_assurance = db.Column(db.Float, default=0)  # % annuel
    duree_mois = db.Column(db.Integer, default=240)
    date_debut = db.Column(db.Date)
    mensualite_hors_assurance = db.Column(db.Float, default=0)
    mensualite_assurance = db.Column(db.Float, default=0)
    capital_restant_du = db.Column(db.Float, default=0)
    en_cours = db.Column(db.Boolean, default=True)
    notes = db.Column(db.Text)

    @property
    def mensualite_totale(self):
        return round(self.mensualite_hors_assurance + self.mensualite_assurance, 2)

    @property
    def cout_total_credit(self):
        return round(self.mensualite_totale * self.duree_mois, 2)

    @property
    def mois_restants(self):
        if self.date_debut and self.duree_mois:
            from dateutil.relativedelta import relativedelta
            fin = self.date_debut + relativedelta(months=self.duree_mois)
            delta = fin - date.today()
            return max(0, delta.days // 30)
        return 0

    def to_dict(self):
        return {
            "id": self.id,
            "nom": self.nom,
            "type_pret": self.type_pret,
            "banque": self.banque,
            "montant_emprunte": self.montant_emprunte,
            "taux_nominal": self.taux_nominal,
            "taux_assurance": self.taux_assurance,
            "duree_mois": self.duree_mois,
            "date_debut": self.date_debut.isoformat() if self.date_debut else None,
            "mensualite_hors_assurance": self.mensualite_hors_assurance,
            "mensualite_assurance": self.mensualite_assurance,
            "mensualite_totale": self.mensualite_totale,
            "capital_restant_du": self.capital_restant_du,
            "en_cours": self.en_cours,
            "mois_restants": self.mois_restants,
        }


class RealEstateWork(db.Model):
    """Travaux réalisés sur un bien (historique)."""
    __tablename__ = "real_estate_works"

    id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer, db.ForeignKey("real_estate.id"), nullable=False)

    description = db.Column(db.String(300))
    type_travaux = db.Column(db.String(50))
    # renovation_energetique, gros_oeuvre, second_oeuvre, amenagement,
    # mise_aux_normes, extension, decoration
    montant = db.Column(db.Float, default=0)
    date_travaux = db.Column(db.Date)
    deductible_fiscalement = db.Column(db.Boolean, default=False)
    notes = db.Column(db.Text)

    def to_dict(self):
        return {
            "id": self.id,
            "description": self.description,
            "type_travaux": self.type_travaux,
            "montant": self.montant,
            "date_travaux": self.date_travaux.isoformat() if self.date_travaux else None,
            "deductible_fiscalement": self.deductible_fiscalement,
        }


# ─── CRYPTO ───────────────────────────────────────────────

class CryptoPosition(db.Model):
    __tablename__ = "crypto_positions"

    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(20), nullable=False)  # BTC, ETH, SOL...
    nom = db.Column(db.String(100))
    quantite = db.Column(db.Float, default=0)
    prix_achat_moyen = db.Column(db.Float, default=0)  # coût moyen en EUR
    plateforme = db.Column(db.String(50))  # Revolut, Binance, Ledger...
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self, current_price=None):
        invested = self.quantite * self.prix_achat_moyen
        current_value = self.quantite * current_price if current_price else invested
        pnl = current_value - invested
        pnl_pct = (pnl / invested * 100) if invested > 0 else 0
        return {
            "id": self.id,
            "symbol": self.symbol,
            "nom": self.nom,
            "quantite": self.quantite,
            "prix_achat_moyen": self.prix_achat_moyen,
            "invested_eur": round(invested, 2),
            "current_price": current_price,
            "current_value": round(current_value, 2),
            "pnl_eur": round(pnl, 2),
            "pnl_pct": round(pnl_pct, 2),
            "plateforme": self.plateforme,
        }


# ─── MATIÈRES PREMIÈRES ──────────────────────────────────

class CommodityPosition(db.Model):
    __tablename__ = "commodity_positions"

    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(20), nullable=False)  # GOLD, SILVER, OIL
    nom = db.Column(db.String(100))
    type_produit = db.Column(db.String(50))  # physique, etf, cfd
    quantite = db.Column(db.Float, default=0)  # onces, barils, parts ETF
    prix_achat_moyen = db.Column(db.Float, default=0)
    devise = db.Column(db.String(5), default="EUR")
    plateforme = db.Column(db.String(50))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self, current_price=None):
        invested = self.quantite * self.prix_achat_moyen
        current_value = self.quantite * current_price if current_price else invested
        pnl = current_value - invested
        pnl_pct = (pnl / invested * 100) if invested > 0 else 0
        return {
            "id": self.id,
            "symbol": self.symbol,
            "nom": self.nom,
            "type_produit": self.type_produit,
            "quantite": self.quantite,
            "prix_achat_moyen": self.prix_achat_moyen,
            "invested_eur": round(invested, 2),
            "current_price": current_price,
            "current_value": round(current_value, 2),
            "pnl_eur": round(pnl, 2),
            "pnl_pct": round(pnl_pct, 2),
            "devise": self.devise,
            "plateforme": self.plateforme,
        }


# ─── CASH / COMPTES BANCAIRES ────────────────────────────

class CashAccount(db.Model):
    __tablename__ = "cash_accounts"

    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(200), nullable=False)  # "Livret A BoursoBank"
    type_compte = db.Column(db.String(50))  # ccp, livret_a, ldds, lep, pel, csl, autre
    banque = db.Column(db.String(100))
    solde = db.Column(db.Float, default=0)
    taux_interet = db.Column(db.Float, default=0)  # % annuel
    plafond = db.Column(db.Float)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def interet_annuel_estime(self):
        return round(self.solde * self.taux_interet / 100, 2)

    def to_dict(self):
        return {
            "id": self.id,
            "nom": self.nom,
            "type_compte": self.type_compte,
            "banque": self.banque,
            "solde": self.solde,
            "taux_interet": self.taux_interet,
            "plafond": self.plafond,
            "interet_annuel_estime": self.interet_annuel_estime,
        }


# ─── TRANSACTIONS (historique global) ────────────────────

class Transaction(db.Model):
    __tablename__ = "transactions"

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, default=date.today)
    type_actif = db.Column(db.String(20))  # immo, crypto, commodity, cash
    actif_id = db.Column(db.Integer)
    action = db.Column(db.String(20))  # buy, sell, deposit, withdraw, dividend, rent
    montant = db.Column(db.Float, default=0)
    quantite = db.Column(db.Float)
    prix_unitaire = db.Column(db.Float)
    frais = db.Column(db.Float, default=0)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "date": self.date.isoformat() if self.date else None,
            "type_actif": self.type_actif,
            "actif_id": self.actif_id,
            "action": self.action,
            "montant": self.montant,
            "quantite": self.quantite,
            "prix_unitaire": self.prix_unitaire,
            "frais": self.frais,
            "notes": self.notes,
        }


# ─── SNAPSHOTS (pour graphique évolution) ────────────────

class PortfolioSnapshot(db.Model):
    __tablename__ = "portfolio_snapshots"

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, default=date.today, index=True)
    net_worth = db.Column(db.Float, default=0)
    immo_value = db.Column(db.Float, default=0)
    crypto_value = db.Column(db.Float, default=0)
    commodity_value = db.Column(db.Float, default=0)
    cash_value = db.Column(db.Float, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "date": self.date.isoformat(),
            "net_worth": self.net_worth,
            "immo": self.immo_value,
            "crypto": self.crypto_value,
            "commodity": self.commodity_value,
            "cash": self.cash_value,
        }
