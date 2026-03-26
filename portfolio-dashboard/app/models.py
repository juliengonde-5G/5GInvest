"""
Modèles SQLAlchemy - Portfolio multi-actifs.
Tables: immobilier, crypto, commodities, cash, transactions.
"""

from datetime import datetime, date
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


# ─── PROFIL UTILISATEUR (PATRIMOINE) ─────────────────────

class UserProfile(db.Model):
    """Profil patrimonial de l'utilisateur - base du conseil."""
    __tablename__ = "user_profiles"

    id = db.Column(db.Integer, primary_key=True)

    # Identité
    prenom = db.Column(db.String(100))
    nom = db.Column(db.String(100))
    email = db.Column(db.String(200), unique=True)
    date_naissance = db.Column(db.Date)
    age = db.Column(db.Integer)

    # Situation
    situation_familiale = db.Column(db.String(30))  # celibataire, marie, pacse, divorce, veuf
    nb_enfants = db.Column(db.Integer, default=0)
    nb_parts_fiscales = db.Column(db.Float, default=1.0)
    regime_matrimonial = db.Column(db.String(50))  # communaute, separation, universel

    # Revenus
    revenu_net_annuel = db.Column(db.Float, default=0)
    revenu_foncier_annuel = db.Column(db.Float, default=0)
    autres_revenus_annuel = db.Column(db.Float, default=0)
    charges_fixes_mensuelles = db.Column(db.Float, default=0)

    # Fiscal
    tmi = db.Column(db.Float, default=0.30)
    option_fiscale = db.Column(db.String(10), default="pfu")  # pfu, bareme

    # Objectifs patrimoniaux
    objectif_principal = db.Column(db.String(50))
    # constitution, retraite, revenus_complementaires, transmission, liberte_financiere, projet
    objectif_description = db.Column(db.Text)
    age_objectif = db.Column(db.Integer)  # âge cible (ex: retraite à 60 ans)
    montant_objectif = db.Column(db.Float)  # montant cible (ex: 500k€)

    # Profil risque global
    profil_risque = db.Column(db.String(20), default="equilibre")
    experience_investissement = db.Column(db.String(20), default="debutant")
    horizon_global = db.Column(db.String(20), default="moyen")  # court, moyen, long

    # Épargne
    capacite_epargne_mensuelle = db.Column(db.Float, default=0)
    epargne_precaution_mois = db.Column(db.Integer, default=3)  # objectif mois de réserve

    # Banques
    banques = db.Column(db.Text)  # JSON array: ["Revolut", "Boursorama"]

    # Enveloppes
    has_pea = db.Column(db.Boolean, default=False)
    pea_date_ouverture = db.Column(db.Date)
    has_assurance_vie = db.Column(db.Boolean, default=False)
    av_date_ouverture = db.Column(db.Date)
    has_per = db.Column(db.Boolean, default=False)
    has_cto = db.Column(db.Boolean, default=True)

    # RGPD
    rgpd_consent = db.Column(db.Boolean, default=False)
    rgpd_consent_date = db.Column(db.DateTime)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def annees_avant_objectif(self):
        if self.age_objectif and self.age:
            return max(0, self.age_objectif - self.age)
        return None

    @property
    def revenu_total_annuel(self):
        return (self.revenu_net_annuel or 0) + (self.revenu_foncier_annuel or 0) + (self.autres_revenus_annuel or 0)

    @property
    def taux_effort_pct(self):
        """Ratio charges/revenus mensuels."""
        revenu_mensuel = self.revenu_total_annuel / 12
        if revenu_mensuel > 0:
            return round(self.charges_fixes_mensuelles / revenu_mensuel * 100, 1)
        return 0

    def get_banques_list(self):
        import json
        try:
            return json.loads(self.banques) if self.banques else []
        except Exception:
            return []

    def to_dict(self):
        return {
            "id": self.id,
            "prenom": self.prenom,
            "email": self.email,
            "age": self.age,
            "situation_familiale": self.situation_familiale,
            "nb_enfants": self.nb_enfants,
            "nb_parts_fiscales": self.nb_parts_fiscales,
            "revenu_net_annuel": self.revenu_net_annuel,
            "charges_fixes_mensuelles": self.charges_fixes_mensuelles,
            "capacite_epargne_mensuelle": self.capacite_epargne_mensuelle,
            "taux_effort_pct": self.taux_effort_pct,
            "tmi": self.tmi,
            "option_fiscale": self.option_fiscale,
            "objectif_principal": self.objectif_principal,
            "objectif_description": self.objectif_description,
            "age_objectif": self.age_objectif,
            "montant_objectif": self.montant_objectif,
            "annees_avant_objectif": self.annees_avant_objectif,
            "profil_risque": self.profil_risque,
            "experience_investissement": self.experience_investissement,
            "horizon_global": self.horizon_global,
            "banques": self.get_banques_list(),
            "has_pea": self.has_pea,
            "pea_date_ouverture": self.pea_date_ouverture.isoformat() if self.pea_date_ouverture else None,
            "has_assurance_vie": self.has_assurance_vie,
            "av_date_ouverture": self.av_date_ouverture.isoformat() if self.av_date_ouverture else None,
            "has_per": self.has_per,
        }


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


# ─── PARCOURS D'INVESTISSEMENT ────────────────────────────

class InvestmentPath(db.Model):
    """Parcours d'investissement autonome avec objectif et profil."""
    __tablename__ = "investment_paths"

    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)

    # Profil
    profil_risque = db.Column(db.String(30))  # prudent, equilibre, dynamique, agressif, sur_mesure
    reactivite = db.Column(db.String(30))  # passive, moderee, active, tres_active
    maturite_mois = db.Column(db.Integer, default=12)  # horizon en mois

    # Budget
    mise_depart = db.Column(db.Float, default=0)
    objectif_sortie = db.Column(db.Float, default=0)  # montant cible à atteindre
    objectif_rendement_pct = db.Column(db.Float, default=0)  # rendement annuel visé

    # Banque / enveloppe
    banque = db.Column(db.String(100))
    enveloppe = db.Column(db.String(50))  # cto, pea, assurance_vie, per
    date_ouverture_enveloppe = db.Column(db.Date)  # impact fiscal

    # État
    statut = db.Column(db.String(20), default="actif")  # actif, pause, cloture
    valeur_actuelle = db.Column(db.Float, default=0)
    pnl_eur = db.Column(db.Float, default=0)
    pnl_pct = db.Column(db.Float, default=0)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    positions = db.relationship("InvestmentPosition", backref="path", cascade="all,delete-orphan", lazy=True)
    arbitrages = db.relationship("Arbitrage", backref="path", cascade="all,delete-orphan", lazy=True)

    @property
    def rendement_actuel_pct(self):
        if self.mise_depart > 0:
            return round((self.valeur_actuelle - self.mise_depart) / self.mise_depart * 100, 2)
        return 0

    @property
    def progression_objectif_pct(self):
        if self.objectif_sortie > 0 and self.mise_depart > 0:
            gain_cible = self.objectif_sortie - self.mise_depart
            gain_actuel = self.valeur_actuelle - self.mise_depart
            return round(gain_actuel / gain_cible * 100, 1) if gain_cible > 0 else 0
        return 0

    def to_dict(self):
        return {
            "id": self.id,
            "nom": self.nom,
            "description": self.description,
            "profil_risque": self.profil_risque,
            "reactivite": self.reactivite,
            "maturite_mois": self.maturite_mois,
            "mise_depart": self.mise_depart,
            "objectif_sortie": self.objectif_sortie,
            "objectif_rendement_pct": self.objectif_rendement_pct,
            "banque": self.banque,
            "enveloppe": self.enveloppe,
            "date_ouverture_enveloppe": self.date_ouverture_enveloppe.isoformat() if self.date_ouverture_enveloppe else None,
            "statut": self.statut,
            "valeur_actuelle": self.valeur_actuelle,
            "pnl_eur": self.pnl_eur,
            "pnl_pct": self.pnl_pct,
            "rendement_actuel_pct": self.rendement_actuel_pct,
            "progression_objectif_pct": self.progression_objectif_pct,
            "positions": [p.to_dict() for p in self.positions],
            "arbitrages": [a.to_dict() for a in sorted(self.arbitrages, key=lambda x: x.date_proposition or date.min, reverse=True)[:10]],
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class InvestmentPosition(db.Model):
    """Position dans un parcours d'investissement."""
    __tablename__ = "investment_positions"

    id = db.Column(db.Integer, primary_key=True)
    path_id = db.Column(db.Integer, db.ForeignKey("investment_paths.id"), nullable=False)

    symbol = db.Column(db.String(30), nullable=False)  # IWDA.AS, BTC, NVDA...
    nom = db.Column(db.String(200))
    type_produit = db.Column(db.String(30))  # etf, action, crypto, obligation, fonds_euro, opcvm
    quantite = db.Column(db.Float, default=0)
    prix_entree = db.Column(db.Float, default=0)  # prix moyen d'achat
    prix_actuel = db.Column(db.Float, default=0)
    date_entree = db.Column(db.Date)
    date_sortie = db.Column(db.Date)  # null si toujours en portefeuille
    prix_sortie = db.Column(db.Float)  # renseigné par l'utilisateur à la vente

    # Objectifs
    objectif_cours_haut = db.Column(db.Float)  # take profit
    objectif_cours_bas = db.Column(db.Float)  # stop loss
    alerte_envoyee = db.Column(db.Boolean, default=False)

    # Staking / rewards (crypto)
    staking_actif = db.Column(db.Boolean, default=False)
    rewards_cumules = db.Column(db.Float, default=0)

    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def investi(self):
        return round(self.quantite * self.prix_entree, 2)

    @property
    def valeur_actuelle(self):
        if self.date_sortie and self.prix_sortie:
            return round(self.quantite * self.prix_sortie, 2)
        return round(self.quantite * self.prix_actuel, 2)

    @property
    def pnl_eur(self):
        return round(self.valeur_actuelle - self.investi + self.rewards_cumules, 2)

    @property
    def pnl_pct(self):
        if self.investi > 0:
            return round(self.pnl_eur / self.investi * 100, 2)
        return 0

    @property
    def objectif_atteint(self):
        if self.objectif_cours_haut and self.prix_actuel >= self.objectif_cours_haut:
            return "take_profit"
        if self.objectif_cours_bas and self.prix_actuel <= self.objectif_cours_bas:
            return "stop_loss"
        return None

    def to_dict(self):
        return {
            "id": self.id,
            "symbol": self.symbol,
            "nom": self.nom,
            "type_produit": self.type_produit,
            "quantite": self.quantite,
            "prix_entree": self.prix_entree,
            "prix_actuel": self.prix_actuel,
            "date_entree": self.date_entree.isoformat() if self.date_entree else None,
            "date_sortie": self.date_sortie.isoformat() if self.date_sortie else None,
            "prix_sortie": self.prix_sortie,
            "investi": self.investi,
            "valeur_actuelle": self.valeur_actuelle,
            "pnl_eur": self.pnl_eur,
            "pnl_pct": self.pnl_pct,
            "objectif_cours_haut": self.objectif_cours_haut,
            "objectif_cours_bas": self.objectif_cours_bas,
            "objectif_atteint": self.objectif_atteint,
            "staking_actif": self.staking_actif,
            "rewards_cumules": self.rewards_cumules,
            "en_portefeuille": self.date_sortie is None,
        }


class Arbitrage(db.Model):
    """Proposition d'arbitrage (achat/vente) par le système."""
    __tablename__ = "arbitrages"

    id = db.Column(db.Integer, primary_key=True)
    path_id = db.Column(db.Integer, db.ForeignKey("investment_paths.id"), nullable=False)

    type_action = db.Column(db.String(20))  # buy, sell, switch, rebalance
    symbol = db.Column(db.String(30))
    nom_produit = db.Column(db.String(200))
    montant_suggere = db.Column(db.Float, default=0)
    prix_cible = db.Column(db.Float)
    raison = db.Column(db.Text)  # justification de l'arbitrage

    # Remplacement (si switch)
    symbol_remplacement = db.Column(db.String(30))
    nom_remplacement = db.Column(db.String(200))

    # Statut
    statut = db.Column(db.String(20), default="propose")  # propose, accepte, refuse, execute
    date_proposition = db.Column(db.DateTime, default=datetime.utcnow)
    date_execution = db.Column(db.DateTime)
    prix_execution = db.Column(db.Float)  # renseigné par l'utilisateur après exécution

    notes = db.Column(db.Text)

    def to_dict(self):
        return {
            "id": self.id,
            "type_action": self.type_action,
            "symbol": self.symbol,
            "nom_produit": self.nom_produit,
            "montant_suggere": self.montant_suggere,
            "prix_cible": self.prix_cible,
            "raison": self.raison,
            "symbol_remplacement": self.symbol_remplacement,
            "nom_remplacement": self.nom_remplacement,
            "statut": self.statut,
            "date_proposition": self.date_proposition.isoformat() if self.date_proposition else None,
            "date_execution": self.date_execution.isoformat() if self.date_execution else None,
            "prix_execution": self.prix_execution,
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

TYPES_COMPTE = {
    "ccp": {"label": "Compte courant", "taux_defaut": 0, "plafond": None},
    "livret_a": {"label": "Livret A", "taux_defaut": 2.4, "plafond": 22950},
    "ldds": {"label": "LDDS", "taux_defaut": 2.4, "plafond": 12000},
    "lep": {"label": "LEP", "taux_defaut": 3.5, "plafond": 10000},
    "pel": {"label": "PEL", "taux_defaut": 2.25, "plafond": 61200},
    "cel": {"label": "CEL", "taux_defaut": 2.0, "plafond": 15300},
    "csl": {"label": "Compte sur livret", "taux_defaut": 0.5, "plafond": None},
    "compte_terme": {"label": "Compte à terme", "taux_defaut": 3.0, "plafond": None},
    "autre": {"label": "Autre", "taux_defaut": 0, "plafond": None},
}


class CashAccount(db.Model):
    __tablename__ = "cash_accounts"

    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(200), nullable=False)
    type_compte = db.Column(db.String(50))
    banque = db.Column(db.String(100))
    numero_compte = db.Column(db.String(50))  # IBAN masqué
    solde = db.Column(db.Float, default=0)
    solde_date = db.Column(db.Date, default=date.today)
    taux_interet = db.Column(db.Float, default=0)
    plafond = db.Column(db.Float)
    date_ouverture = db.Column(db.Date)
    est_compte_joint = db.Column(db.Boolean, default=False)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    bank_transactions = db.relationship("BankTransaction", backref="account", cascade="all,delete-orphan", lazy=True)

    @property
    def interet_annuel_estime(self):
        return round(self.solde * self.taux_interet / 100, 2)

    @property
    def remplissage_pct(self):
        if self.plafond and self.plafond > 0:
            return round(self.solde / self.plafond * 100, 1)
        return None

    def to_dict(self):
        return {
            "id": self.id,
            "nom": self.nom,
            "type_compte": self.type_compte,
            "type_label": TYPES_COMPTE.get(self.type_compte, {}).get("label", self.type_compte),
            "banque": self.banque,
            "solde": self.solde,
            "solde_date": self.solde_date.isoformat() if self.solde_date else None,
            "taux_interet": self.taux_interet,
            "plafond": self.plafond,
            "remplissage_pct": self.remplissage_pct,
            "interet_annuel_estime": self.interet_annuel_estime,
            "date_ouverture": self.date_ouverture.isoformat() if self.date_ouverture else None,
            "est_compte_joint": self.est_compte_joint,
        }


class BankTransaction(db.Model):
    """Transaction bancaire (pour analyse flux et prévisionnel)."""
    __tablename__ = "bank_transactions"

    id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(db.Integer, db.ForeignKey("cash_accounts.id"), nullable=False)

    date = db.Column(db.Date, nullable=False)
    libelle = db.Column(db.String(500))
    montant = db.Column(db.Float, default=0)  # positif = crédit, négatif = débit

    # Catégorisation
    categorie = db.Column(db.String(50))
    # loyer, salaire, courses, restaurant, transport, abonnement, sante,
    # energie, telecom, impots, epargne, loisirs, shopping, autre
    sous_categorie = db.Column(db.String(50))
    est_recurrent = db.Column(db.Boolean, default=False)
    frequence = db.Column(db.String(20))  # mensuel, hebdo, trimestriel, annuel

    # Source
    source = db.Column(db.String(20), default="manuel")  # manuel, import, api_bancaire
    reference = db.Column(db.String(100))  # ID transaction banque

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "account_id": self.account_id,
            "date": self.date.isoformat(),
            "libelle": self.libelle,
            "montant": self.montant,
            "categorie": self.categorie,
            "sous_categorie": self.sous_categorie,
            "est_recurrent": self.est_recurrent,
            "frequence": self.frequence,
            "source": self.source,
        }


# ─── TRANSACTIONS PATRIMOINE (historique global) ─────────

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
