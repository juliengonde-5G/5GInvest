"""
Modèles SQLAlchemy - Portfolio multi-actifs.
Tables: immobilier, crypto, commodities, cash, transactions.
"""

from datetime import datetime, date
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


# ─── IMMOBILIER ───────────────────────────────────────────

class RealEstate(db.Model):
    __tablename__ = "real_estate"

    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(200), nullable=False)
    adresse = db.Column(db.String(500))
    ville = db.Column(db.String(100))
    code_postal = db.Column(db.String(10))
    type_bien = db.Column(db.String(50))  # appartement, maison, immeuble, parking
    surface_m2 = db.Column(db.Float, default=0)
    prix_achat = db.Column(db.Float, default=0)
    date_achat = db.Column(db.Date)
    prix_m2_estime = db.Column(db.Float, default=0)  # prix/m2 INSEE local
    valeur_estimee = db.Column(db.Float, default=0)
    travaux_realises = db.Column(db.Float, default=0)
    loyer_mensuel = db.Column(db.Float, default=0)
    charges_mensuelles = db.Column(db.Float, default=0)  # copro, taxe foncière/12, assurance
    credit_mensuel = db.Column(db.Float, default=0)
    capital_restant_du = db.Column(db.Float, default=0)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def rendement_brut(self):
        if self.valeur_estimee and self.valeur_estimee > 0:
            return round((self.loyer_mensuel * 12) / self.valeur_estimee * 100, 2)
        return 0

    @property
    def rendement_net(self):
        if self.valeur_estimee and self.valeur_estimee > 0:
            revenu_net = (self.loyer_mensuel - self.charges_mensuelles) * 12
            return round(revenu_net / self.valeur_estimee * 100, 2)
        return 0

    @property
    def cashflow_mensuel(self):
        return round(self.loyer_mensuel - self.charges_mensuelles - self.credit_mensuel, 2)

    @property
    def valeur_nette(self):
        return round(self.valeur_estimee - self.capital_restant_du, 2)

    def to_dict(self):
        return {
            "id": self.id,
            "nom": self.nom,
            "adresse": self.adresse,
            "ville": self.ville,
            "code_postal": self.code_postal,
            "type_bien": self.type_bien,
            "surface_m2": self.surface_m2,
            "prix_achat": self.prix_achat,
            "date_achat": self.date_achat.isoformat() if self.date_achat else None,
            "prix_m2_estime": self.prix_m2_estime,
            "valeur_estimee": self.valeur_estimee,
            "travaux_realises": self.travaux_realises,
            "loyer_mensuel": self.loyer_mensuel,
            "charges_mensuelles": self.charges_mensuelles,
            "credit_mensuel": self.credit_mensuel,
            "capital_restant_du": self.capital_restant_du,
            "rendement_brut": self.rendement_brut,
            "rendement_net": self.rendement_net,
            "cashflow_mensuel": self.cashflow_mensuel,
            "valeur_nette": self.valeur_nette,
            "notes": self.notes,
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
