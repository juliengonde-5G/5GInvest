"""
Catalogue des banques françaises et de leurs produits d'investissement.
Inclut: frais, enveloppes disponibles, produits distribués, avantages/limites.
"""

BANKS = {
    "revolut": {
        "nom": "Revolut",
        "type": "neobanque",
        "pays": "Lituanie (licence EU)",
        "enveloppes": ["cto"],
        "frais": {
            "cto_ordre": 0.0,  # 0€ (1 gratuit/mois Standard, illimité Metal)
            "cto_ordre_apres_gratuit": 1.0,  # 1€ par ordre supplémentaire (Standard)
            "garde": 0.0,
            "crypto_spread": 1.49,  # % Standard plan
            "change_eur_usd": 0.0,  # Gratuit en semaine
            "inactivite": 0.0,
        },
        "produits": {
            "actions_us": True, "actions_eu": True, "etf": True,
            "crypto": True, "obligations": False, "opcvm": False,
            "matieres_premieres_etf": True, "fractional": True,
            "options": False, "cfd": False,
        },
        "avantages": [
            "0 commission (1 trade/mois Standard)",
            "Actions fractionnées dès 1€",
            "Crypto intégrée",
            "Interface simple",
            "Multi-devises",
        ],
        "limites": [
            "Pas de PEA ni AV",
            "Fiscalité CTO uniquement (PFU 30%)",
            "Pas d'OPCVM/fonds",
            "Spread crypto élevé (1.49%)",
            "Déclaration fiscale à faire soi-même",
        ],
        "ideal_pour": ["trading court terme", "crypto", "petits montants", "débutants"],
    },
    "boursorama": {
        "nom": "Boursorama (BoursoBank)",
        "type": "banque en ligne",
        "pays": "France",
        "enveloppes": ["pea", "cto", "assurance_vie", "per"],
        "frais": {
            "pea_ordre_0_500": 1.99,  # €
            "pea_ordre_500_2000": 0.0,  # % (Bourso Découverte gratuit)
            "cto_ordre": 1.99,  # min par ordre
            "av_gestion_uc": 0.75,  # % annuel
            "av_gestion_fonds_euro": 0.75,
            "av_entree": 0.0,
            "av_arbitrage": 0.0,
            "garde": 0.0,
        },
        "produits": {
            "actions_us": True, "actions_eu": True, "etf": True,
            "crypto": False, "obligations": True, "opcvm": True,
            "fonds_euro": True, "scpi": True, "warrants": True,
            "turbos": True, "fractional": False,
        },
        "avantages": [
            "PEA avec large choix d'ETF",
            "Assurance-vie Bourso Vie (bon fonds euro)",
            "PER disponible",
            "Tarifs compétitifs (offre Découverte)",
            "IFU fourni (déclaration simplifiée)",
        ],
        "limites": [
            "Pas de crypto",
            "Pas de fractions d'actions",
            "Frais PEA sur petits ordres",
        ],
        "ideal_pour": ["PEA long terme", "assurance-vie", "investisseur patrimonial"],
    },
    "fortuneo": {
        "nom": "Fortuneo",
        "type": "banque en ligne",
        "pays": "France",
        "enveloppes": ["pea", "cto", "assurance_vie", "per"],
        "frais": {
            "pea_ordre_starter": 1.95,  # 1 ordre gratuit/mois (Starter)
            "pea_ordre_progress": 3.90,  # 2 ordres gratuits/mois
            "cto_ordre": 1.95,
            "av_gestion_uc": 0.60,  # Fortuneo Vie = 0.60%
            "av_gestion_fonds_euro": 0.60,
            "av_entree": 0.0,
            "av_arbitrage": 0.0,
            "garde": 0.0,
        },
        "produits": {
            "actions_us": True, "actions_eu": True, "etf": True,
            "crypto": False, "obligations": True, "opcvm": True,
            "fonds_euro": True, "scpi": False, "warrants": True,
            "fractional": False,
        },
        "avantages": [
            "1 ordre gratuit/mois (Starter)",
            "PEA très compétitif",
            "AV Fortuneo Vie (frais bas 0.60%)",
            "Large choix ETF Amundi/Lyxor",
            "IFU fourni",
        ],
        "limites": [
            "Pas de crypto",
            "Pas de fractions d'actions",
            "Choix SCPI limité",
        ],
        "ideal_pour": ["PEA ETF", "assurance-vie", "gestion passive"],
    },
    "trade_republic": {
        "nom": "Trade Republic",
        "type": "neocourtier",
        "pays": "Allemagne (licence EU)",
        "enveloppes": ["cto"],
        "frais": {
            "cto_ordre": 1.0,  # 1€ fixe par ordre
            "plans_epargne": 0.0,  # Plans d'épargne gratuits
            "crypto": 1.0,  # 1€ + spread
            "crypto_spread": 1.0,  # % environ
            "garde": 0.0,
            "interet_cash": 2.75,  # % sur le cash non investi (2025)
        },
        "produits": {
            "actions_us": True, "actions_eu": True, "etf": True,
            "crypto": True, "obligations": True, "opcvm": False,
            "fractional": True, "plans_epargne": True,
            "derivatifs": True,
        },
        "avantages": [
            "1€ fixe par ordre",
            "Plans d'épargne gratuits (DCA automatique)",
            "Actions fractionnées",
            "Crypto intégrée",
            "2.75% d'intérêt sur le cash",
            "Large choix ETF iShares",
        ],
        "limites": [
            "Pas de PEA",
            "Fiscalité CTO (PFU 30%)",
            "Pas d'OPCVM classiques",
            "Déclaration fiscale manuelle",
        ],
        "ideal_pour": ["DCA ETF", "plans d'épargne", "crypto", "petits budgets"],
    },
    "degiro": {
        "nom": "DEGIRO",
        "type": "courtier en ligne",
        "pays": "Pays-Bas (licence EU)",
        "enveloppes": ["cto"],
        "frais": {
            "cto_ordre_etf_selection": 0.0,  # ETF core selection gratuit
            "cto_ordre_actions_eu": 2.0,
            "cto_ordre_actions_us": 0.50,  # + 0.004$/action
            "cto_connexion_bourse_us": 2.50,  # /an
            "garde": 0.0,
        },
        "produits": {
            "actions_us": True, "actions_eu": True, "etf": True,
            "crypto": False, "obligations": True, "opcvm": True,
            "options": True, "futures": True, "fractional": False,
        },
        "avantages": [
            "ETF core selection gratuit (1/mois)",
            "Actions US très peu chères",
            "Accès marchés mondiaux",
            "Options et futures disponibles",
        ],
        "limites": [
            "Pas de PEA",
            "Pas de crypto",
            "Pas de fractions d'actions",
            "Interface perfectible",
            "Déclaration fiscale manuelle",
        ],
        "ideal_pour": ["ETF passif", "actions US", "options", "investisseurs expérimentés"],
    },
    "bourse_direct": {
        "nom": "Bourse Direct",
        "type": "courtier en ligne",
        "pays": "France",
        "enveloppes": ["pea", "pea_pme", "cto", "per"],
        "frais": {
            "pea_ordre_0_500": 0.99,
            "pea_ordre_500_1000": 1.90,
            "pea_ordre_1000_4400": 3.80,
            "cto_ordre": 0.99,  # min
            "garde": 0.0,
        },
        "produits": {
            "actions_us": True, "actions_eu": True, "etf": True,
            "crypto": False, "obligations": True, "opcvm": True,
            "warrants": True, "turbos": True, "fractional": False,
        },
        "avantages": [
            "PEA le moins cher de France (0.99€)",
            "PEA-PME disponible",
            "Large choix de titres",
            "IFU fourni",
        ],
        "limites": [
            "Interface datée",
            "Pas de crypto",
            "Pas de fractions",
        ],
        "ideal_pour": ["PEA pas cher", "PEA-PME", "investisseur autonome"],
    },
    "societe_generale": {
        "nom": "Société Générale",
        "type": "banque traditionnelle",
        "pays": "France",
        "enveloppes": ["pea", "cto", "assurance_vie", "per"],
        "frais": {
            "pea_ordre": 5.50,  # min environ
            "cto_ordre": 8.90,  # min
            "av_gestion": 0.96,
            "av_entree": 2.0,  # % max
            "garde_cto": 0.036,  # % trimestriel
        },
        "produits": {
            "actions_us": True, "actions_eu": True, "etf": True,
            "crypto": False, "obligations": True, "opcvm": True,
            "fonds_euro": True, "scpi": True, "assurance_vie": True,
            "fractional": False,
        },
        "avantages": [
            "Conseil en agence",
            "Gamme complète (PEA, AV, PER)",
            "SCPI en assurance-vie",
        ],
        "limites": [
            "Frais très élevés",
            "Droits de garde",
            "Frais d'entrée AV",
        ],
        "ideal_pour": ["clients existants SG", "besoin de conseil", "SCPI"],
    },
    "bnp_paribas": {
        "nom": "BNP Paribas",
        "type": "banque traditionnelle",
        "pays": "France",
        "enveloppes": ["pea", "cto", "assurance_vie", "per"],
        "frais": {
            "pea_ordre": 5.50,
            "cto_ordre": 7.50,
            "av_gestion": 0.85,
            "av_entree": 2.5,
            "garde_cto": 0.05,  # % trimestriel
        },
        "produits": {
            "actions_us": True, "actions_eu": True, "etf": True,
            "crypto": False, "obligations": True, "opcvm": True,
            "fonds_euro": True, "scpi": True, "pe_private_equity": True,
            "fractional": False,
        },
        "avantages": [
            "Gamme très large (OPCVM, SCPI, PE)",
            "Conseil patrimonial",
            "Solidité institutionnelle",
        ],
        "limites": [
            "Frais parmi les plus élevés",
            "Droits de garde",
        ],
        "ideal_pour": ["patrimoine important", "conseil personnalisé"],
    },
    "credit_agricole": {
        "nom": "Crédit Agricole",
        "type": "banque traditionnelle",
        "pays": "France",
        "enveloppes": ["pea", "cto", "assurance_vie", "per", "livrets"],
        "frais": {
            "pea_ordre": 6.00,
            "cto_ordre": 9.00,
            "av_gestion": 0.85,
            "av_entree": 2.0,
        },
        "produits": {
            "actions_us": True, "actions_eu": True, "etf": True,
            "crypto": False, "obligations": True, "opcvm": True,
            "fonds_euro": True, "scpi": True, "fractional": False,
        },
        "avantages": [
            "Réseau d'agences dense",
            "Amundi (filiale = large gamme OPCVM)",
            "AV Predica",
        ],
        "limites": [
            "Frais élevés",
            "Offre bourse limitée en ligne",
        ],
        "ideal_pour": ["clients ruraux", "fonds Amundi", "AV Predica"],
    },
    "lcl": {
        "nom": "LCL",
        "type": "banque traditionnelle",
        "pays": "France",
        "enveloppes": ["pea", "cto", "assurance_vie", "per"],
        "frais": {
            "pea_ordre": 6.50,
            "cto_ordre": 8.00,
            "av_gestion": 0.90,
            "av_entree": 2.5,
        },
        "produits": {
            "actions_us": True, "actions_eu": True, "etf": True,
            "crypto": False, "obligations": True, "opcvm": True,
            "fonds_euro": True, "fractional": False,
        },
        "avantages": ["Réseau agences", "Gamme Amundi"],
        "limites": ["Frais élevés", "Offre limitée"],
        "ideal_pour": ["clients existants LCL"],
    },
    "n26": {
        "nom": "N26",
        "type": "neobanque",
        "pays": "Allemagne (licence EU)",
        "enveloppes": ["cto"],
        "frais": {
            "cto_actions": 0.0,  # via partenaire (limité)
            "crypto_spread": 2.5,
        },
        "produits": {
            "actions_us": True, "actions_eu": True, "etf": True,
            "crypto": True, "fractional": True,
        },
        "avantages": ["Interface mobile simple", "Crypto intégrée"],
        "limites": [
            "Offre investissement très limitée",
            "Spread crypto élevé",
            "Pas de PEA",
        ],
        "ideal_pour": ["débutants", "très petits montants"],
    },
}


def get_bank(bank_id: str) -> dict:
    """Récupère les infos d'une banque."""
    normalized = bank_id.lower().replace(" ", "_").replace("-", "_")
    # Mappings d'alias
    aliases = {
        "boursobank": "boursorama",
        "sg": "societe_generale",
        "ca": "credit_agricole",
        "bnp": "bnp_paribas",
        "tr": "trade_republic",
    }
    normalized = aliases.get(normalized, normalized)
    return BANKS.get(normalized, {})


def list_banks() -> list:
    """Liste toutes les banques disponibles."""
    return [{"id": k, **v} for k, v in BANKS.items()]


def get_user_banks(bank_names: list) -> list:
    """Récupère les infos des banques de l'utilisateur."""
    result = []
    for name in bank_names:
        bank = get_bank(name)
        if bank:
            result.append({"id": name.lower().replace(" ", "_"), **bank})
    return result


def compare_banks_for_product(banks: list, product_type: str) -> list:
    """
    Compare les banques pour un type de produit donné.
    Retourne la liste triée par coût.
    """
    results = []
    for bank in banks:
        bank_info = get_bank(bank) if isinstance(bank, str) else bank
        if not bank_info:
            continue

        products = bank_info.get("produits", {})
        if not products.get(product_type.lower(), False):
            continue

        # Estimer le coût annuel pour ce produit
        frais = bank_info.get("frais", {})
        cost_score = _estimate_cost_score(frais, product_type)

        results.append({
            "banque": bank_info.get("nom", bank),
            "disponible": True,
            "enveloppes": bank_info.get("enveloppes", []),
            "cout_estime": cost_score,
            "avantages": bank_info.get("avantages", []),
        })

    results.sort(key=lambda x: x["cout_estime"])
    return results


def _estimate_cost_score(frais: dict, product_type: str) -> float:
    """Score de coût (plus bas = moins cher). Basé sur 12 ordres/an."""
    if product_type in ("etf", "actions_us", "actions_eu"):
        ordre = frais.get("cto_ordre", frais.get("pea_ordre", 5.0))
        garde = frais.get("garde", frais.get("garde_cto", 0)) * 4  # annualisé
        return ordre * 12 + garde * 100  # 12 ordres, garde sur 100€

    if product_type == "assurance_vie":
        gestion = frais.get("av_gestion_uc", frais.get("av_gestion", 1.0))
        entree = frais.get("av_entree", 0)
        return gestion + entree

    if product_type == "crypto":
        return frais.get("crypto_spread", frais.get("crypto", 5.0))

    return 5.0  # default


def select_best_bank(user_banks: list, product_type: str, enveloppe: str = None) -> dict:
    """
    Sélectionne la meilleure banque de l'utilisateur pour un produit/enveloppe.
    """
    comparison = compare_banks_for_product(user_banks, product_type)
    if not comparison:
        return {"error": f"Aucune de vos banques ne propose {product_type}"}

    if enveloppe:
        filtered = [c for c in comparison if enveloppe in c.get("enveloppes", [])]
        if filtered:
            return filtered[0]

    return comparison[0]


def display_bank_selector(user_banks: list):
    """Affiche le sélecteur de banques avec les produits disponibles."""
    print(f"\n{'='*70}")
    print("  VOS BANQUES ET PRODUITS DISPONIBLES")
    print(f"{'='*70}")

    for bank_name in user_banks:
        bank = get_bank(bank_name)
        if not bank:
            print(f"\n  {bank_name}: Banque non reconnue")
            continue

        print(f"\n  {bank.get('nom', bank_name)} ({bank.get('type', '?')})")
        print(f"  {'─'*50}")

        # Enveloppes
        env_labels = {
            "pea": "PEA", "pea_pme": "PEA-PME", "cto": "CTO",
            "assurance_vie": "Assurance-vie", "per": "PER", "livrets": "Livrets",
        }
        envs = [env_labels.get(e, e) for e in bank.get("enveloppes", [])]
        print(f"  Enveloppes: {', '.join(envs)}")

        # Produits
        produits = bank.get("produits", {})
        dispos = [k.replace("_", " ").title() for k, v in produits.items() if v is True]
        print(f"  Produits:   {', '.join(dispos[:6])}")
        if len(dispos) > 6:
            print(f"              {', '.join(dispos[6:])}")

        # Frais clés
        frais = bank.get("frais", {})
        if "cto_ordre" in frais:
            print(f"  Frais ordre: {frais['cto_ordre']}€")
        if "crypto_spread" in frais:
            print(f"  Spread crypto: {frais['crypto_spread']}%")

        # Points forts
        avantages = bank.get("avantages", [])[:3]
        if avantages:
            print(f"  + {' | '.join(avantages)}")
