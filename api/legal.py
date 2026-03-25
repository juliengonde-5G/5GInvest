"""
Pages légales obligatoires : mentions légales, CGU, politique de confidentialité.
Servies comme contenu JSON pour le frontend PWA.
"""

DISCLAIMER_AMF = (
    "5GInvest est un outil d'aide à la décision et ne constitue en aucun cas "
    "un conseil en investissement au sens de l'article L.321-1 du Code monétaire "
    "et financier. Les informations, analyses et signaux fournis sont à titre "
    "informatif et éducatif uniquement. Les performances passées ne préjugent pas "
    "des performances futures. Tout investissement comporte un risque de perte en "
    "capital, y compris totale. Vous êtes seul responsable de vos décisions "
    "d'investissement. Consultez un conseiller en investissements financiers (CIF) "
    "agréé par l'AMF pour un conseil personnalisé."
)

RISK_WARNING_CRYPTO = (
    "Risque élevé : les crypto-actifs sont des produits hautement spéculatifs "
    "présentant un risque de perte totale du capital investi. Leur valeur peut "
    "varier de ±50% en quelques semaines. Ces produits ne conviennent pas à tous "
    "les profils d'investisseurs. Assurez-vous de comprendre les risques avant d'investir."
)

RISK_WARNING_LEVERAGE = (
    "Risque très élevé : les ETF à effet de levier amplifient les mouvements "
    "de marché (x2 = pertes amplifiées x2). L'effet de beta slippage les rend "
    "inadaptés à un horizon supérieur à quelques jours. Ces produits complexes "
    "sont réservés aux investisseurs expérimentés."
)

DISCLAIMER_FISCAL = (
    "Les simulations fiscales sont fournies à titre indicatif sur la base de "
    "la législation en vigueur. Elles ne constituent pas un conseil fiscal et "
    "ne sauraient engager la responsabilité de l'éditeur. La fiscalité peut "
    "évoluer. Consultez un conseiller fiscal pour votre situation personnelle."
)

MENTIONS_LEGALES = {
    "titre": "Mentions légales",
    "editeur": {
        "label": "Éditeur",
        "text": (
            "5GInvest - Outil personnel d'aide à la décision d'investissement. "
            "Application à usage privé, non commerciale. "
            "Ce service n'est pas enregistré comme CIF (Conseiller en Investissements "
            "Financiers) auprès de l'ORIAS et ne fournit aucun conseil en investissement."
        ),
    },
    "hebergeur": {
        "label": "Hébergeur",
        "text": "OVH SAS - 2 rue Kellermann, 59100 Roubaix, France. RCS Lille Métropole 424 761 419.",
    },
    "responsable": {
        "label": "Directeur de la publication",
        "text": "L'utilisateur du service.",
    },
    "propriete_intellectuelle": {
        "label": "Propriété intellectuelle",
        "text": "Le code source est hébergé sur GitHub. Les données de marché proviennent de Yahoo Finance et CoinGecko.",
    },
    "disclaimer_amf": {
        "label": "Avertissement AMF",
        "text": DISCLAIMER_AMF,
    },
    "mediateur": {
        "label": "Médiation",
        "text": (
            "Conformément à l'article L.612-1 du Code de la consommation, "
            "en cas de litige, le consommateur peut recourir à un médiateur de la consommation."
        ),
    },
}

CGU = {
    "titre": "Conditions Générales d'Utilisation",
    "sections": [
        {
            "titre": "1. Objet du service",
            "contenu": (
                "5GInvest est un outil d'aide à la décision pour l'investissement "
                "personnel. Il fournit des analyses techniques, des simulations "
                "fiscales et un suivi de portefeuille. Il NE constitue PAS un "
                "service de conseil en investissement, de gestion de portefeuille "
                "ou d'exécution d'ordres."
            ),
        },
        {
            "titre": "2. Limitation de responsabilité",
            "contenu": (
                "L'éditeur ne garantit ni l'exactitude, ni la complétude, ni "
                "l'actualité des informations fournies. Les signaux d'achat/vente "
                "sont générés par des algorithmes et ne constituent pas des "
                "recommandations personnalisées. L'utilisateur est seul "
                "responsable de ses décisions d'investissement et des pertes "
                "éventuelles qui en résultent."
            ),
        },
        {
            "titre": "3. Produits à risque",
            "contenu": (
                "L'application peut afficher des informations sur des crypto-actifs "
                "et des ETF à effet de levier. Ces produits présentent un risque "
                "de perte totale du capital. L'utilisateur reconnaît avoir pris "
                "connaissance des risques avant toute utilisation."
            ),
        },
        {
            "titre": "4. Données personnelles",
            "contenu": (
                "Le traitement des données personnelles est décrit dans la "
                "Politique de confidentialité. L'utilisation du service vaut "
                "acceptation de cette politique."
            ),
        },
        {
            "titre": "5. Conflits d'intérêts",
            "contenu": (
                "L'éditeur n'a aucun accord commercial, de parrainage ou "
                "d'affiliation avec les banques ou courtiers mentionnés. "
                "Les comparaisons sont fournies à titre informatif."
            ),
        },
        {
            "titre": "6. Droit applicable",
            "contenu": (
                "Les présentes CGU sont régies par le droit français. "
                "En cas de litige, les tribunaux français sont seuls compétents."
            ),
        },
    ],
}

POLITIQUE_CONFIDENTIALITE = {
    "titre": "Politique de confidentialité (RGPD)",
    "sections": [
        {
            "titre": "1. Responsable du traitement",
            "contenu": "L'utilisateur du service, en qualité d'hébergeur de l'application sur son propre serveur.",
        },
        {
            "titre": "2. Données collectées",
            "contenu": (
                "- Prénom, âge, situation familiale\n"
                "- Revenu annuel net, TMI (tranche marginale d'imposition)\n"
                "- Patrimoine financier (PEA, assurance-vie, PER)\n"
                "- Banques utilisées, profil de risque, expérience boursière\n"
                "- Positions et historique des transactions (portefeuille)\n"
                "- Endpoint de notification push"
            ),
        },
        {
            "titre": "3. Finalité du traitement",
            "contenu": (
                "Les données sont utilisées exclusivement pour :\n"
                "- Générer des recommandations d'investissement personnalisées\n"
                "- Calculer l'impact fiscal des opérations\n"
                "- Envoyer des alertes de trading via notifications push\n"
                "- Suivre la performance du portefeuille"
            ),
        },
        {
            "titre": "4. Base légale",
            "contenu": "Consentement explicite de l'utilisateur (article 6(1)(a) du RGPD), recueilli lors de la création du profil.",
        },
        {
            "titre": "5. Stockage et sécurité",
            "contenu": (
                "Les données sont stockées localement sur le serveur de "
                "l'utilisateur (fichiers JSON dans /data/). Elles ne sont "
                "transmises à aucun tiers. L'accès est protégé par HTTPS "
                "et les restrictions CORS."
            ),
        },
        {
            "titre": "6. Durée de conservation",
            "contenu": "Les données sont conservées tant que le profil existe. L'utilisateur peut supprimer son profil à tout moment.",
        },
        {
            "titre": "7. Droits de la personne",
            "contenu": (
                "Conformément au RGPD, vous disposez des droits suivants :\n"
                "- Droit d'accès (article 15) : GET /api/profile/export\n"
                "- Droit de rectification (article 16) : POST /api/profile\n"
                "- Droit à l'effacement (article 17) : DELETE /api/profile\n"
                "- Droit à la portabilité (article 20) : GET /api/profile/export\n"
                "- Droit de réclamation auprès de la CNIL (www.cnil.fr)"
            ),
        },
        {
            "titre": "8. Transferts de données",
            "contenu": (
                "Les données de marché sont récupérées via Yahoo Finance (US) et "
                "CoinGecko (EU). Ces services reçoivent uniquement les requêtes "
                "de prix, jamais vos données personnelles."
            ),
        },
    ],
}


def get_all_legal() -> dict:
    """Retourne toutes les pages légales."""
    return {
        "disclaimer_amf": DISCLAIMER_AMF,
        "risk_crypto": RISK_WARNING_CRYPTO,
        "risk_leverage": RISK_WARNING_LEVERAGE,
        "disclaimer_fiscal": DISCLAIMER_FISCAL,
        "mentions_legales": MENTIONS_LEGALES,
        "cgu": CGU,
        "politique_confidentialite": POLITIQUE_CONFIDENTIALITE,
    }
