"""
Moteur de prévisionnel et catégorisation des flux bancaires.
Analyse les transactions, détecte les récurrences, projette les soldes.
"""

from datetime import date, timedelta
from collections import defaultdict
from typing import List, Dict

# ─── CATÉGORISATION AUTOMATIQUE ───────────────────────────

CATEGORY_RULES = [
    # (patterns dans le libellé, catégorie, sous_catégorie)
    (["salaire", "paie", "virement employeur", "remuneration"], "revenus", "salaire"),
    (["loyer", "quittance", "bail", "sas immo", "foncia", "nexity"], "logement", "loyer"),
    (["edf", "engie", "energie", "electricite", "gaz", "veolia", "eau"], "logement", "energie"),
    (["free", "orange", "sfr", "bouygues", "sosh", "red by"], "abonnements", "telecom"),
    (["netflix", "spotify", "disney", "canal+", "prime video", "deezer"], "abonnements", "streaming"),
    (["amazon", "cdiscount", "fnac", "darty", "boulanger"], "shopping", "en_ligne"),
    (["carrefour", "leclerc", "auchan", "lidl", "aldi", "intermarche", "monoprix", "picard", "franprix"], "courses", "alimentaire"),
    (["uber eat", "deliveroo", "just eat", "mcdo", "burger", "restaurant", "brasserie"], "restaurant", "restaurant"),
    (["sncf", "ratp", "navigo", "essence", "total", "shell", "bp", "parking", "autoroute", "peage"], "transport", "transport"),
    (["mutuelle", "cpam", "ameli", "pharmacie", "docteur", "medecin", "hopital", "sante"], "sante", "sante"),
    (["impot", "tresor public", "dgfip", "taxe", "urssaf", "csg"], "impots", "impots"),
    (["assurance", "maif", "macif", "axa", "allianz", "matmut", "groupama"], "assurance", "assurance"),
    (["virement", "epargne", "livret", "pea", "placement"], "epargne", "epargne"),
    (["cb ", "carte ", "paiement"], "divers", "carte"),
]


def categorize_transaction(libelle: str) -> dict:
    """Catégorise une transaction à partir de son libellé."""
    if not libelle:
        return {"categorie": "autre", "sous_categorie": "autre"}

    libelle_lower = libelle.lower()
    for patterns, cat, sous_cat in CATEGORY_RULES:
        for pattern in patterns:
            if pattern in libelle_lower:
                return {"categorie": cat, "sous_categorie": sous_cat}

    return {"categorie": "autre", "sous_categorie": "autre"}


def categorize_batch(transactions: List[dict]) -> List[dict]:
    """Catégorise un lot de transactions."""
    for tx in transactions:
        if not tx.get("categorie") or tx["categorie"] == "autre":
            cat = categorize_transaction(tx.get("libelle", ""))
            tx["categorie"] = cat["categorie"]
            tx["sous_categorie"] = cat["sous_categorie"]
    return transactions


# ─── DÉTECTION DES RÉCURRENCES ────────────────────────────

def detect_recurring(transactions: List[dict]) -> List[dict]:
    """
    Détecte les transactions récurrentes (même montant ± 5%, même fréquence).
    Retourne la liste des flux récurrents avec leur fréquence.
    """
    # Grouper par libellé normalisé et montant arrondi
    groups = defaultdict(list)
    for tx in transactions:
        key = _normalize_label(tx.get("libelle", ""))
        if key:
            groups[key].append(tx)

    recurring = []
    for label, txs in groups.items():
        if len(txs) < 2:
            continue

        # Trier par date
        txs.sort(key=lambda t: t.get("date", ""))
        montants = [t["montant"] for t in txs]
        avg_montant = sum(montants) / len(montants)

        # Vérifier que les montants sont similaires (±10%)
        if all(abs(m - avg_montant) / abs(avg_montant) < 0.10 for m in montants if avg_montant != 0):
            # Calculer la fréquence
            freq = _detect_frequency(txs)
            if freq:
                recurring.append({
                    "libelle": txs[0].get("libelle", label),
                    "montant_moyen": round(avg_montant, 2),
                    "frequence": freq,
                    "categorie": txs[0].get("categorie", "autre"),
                    "nb_occurrences": len(txs),
                    "derniere_date": txs[-1].get("date"),
                })

    return recurring


def _normalize_label(label: str) -> str:
    """Normalise un libellé pour le grouper."""
    import re
    label = label.lower().strip()
    label = re.sub(r'\d{2}/\d{2}(/\d{2,4})?', '', label)  # Retirer les dates
    label = re.sub(r'\d{4,}', '', label)  # Retirer les longs numéros
    label = re.sub(r'\s+', ' ', label).strip()
    return label[:40] if len(label) > 3 else ""


def _detect_frequency(txs: List[dict]) -> str:
    """Détecte la fréquence d'une série de transactions."""
    if len(txs) < 2:
        return None

    dates = []
    for tx in txs:
        d = tx.get("date")
        if isinstance(d, str):
            dates.append(date.fromisoformat(d))
        elif isinstance(d, date):
            dates.append(d)

    if len(dates) < 2:
        return None

    dates.sort()
    deltas = [(dates[i+1] - dates[i]).days for i in range(len(dates)-1)]
    avg_delta = sum(deltas) / len(deltas)

    if 5 <= avg_delta <= 10:
        return "hebdo"
    elif 25 <= avg_delta <= 35:
        return "mensuel"
    elif 85 <= avg_delta <= 100:
        return "trimestriel"
    elif 350 <= avg_delta <= 380:
        return "annuel"
    return None


# ─── PRÉVISIONNEL ─────────────────────────────────────────

FREQ_TO_DAYS = {"hebdo": 7, "mensuel": 30, "trimestriel": 91, "annuel": 365}


def build_forecast(solde_actuel: float, recurring: List[dict],
                   horizon_mois: int = 3) -> List[dict]:
    """
    Construit un prévisionnel de solde sur N mois à partir des flux récurrents.
    Retourne: [{date, solde_prevu, flux_prevu}]
    """
    today = date.today()
    end_date = today + timedelta(days=horizon_mois * 30)

    # Construire les flux futurs
    future_flows = []
    for rec in recurring:
        freq_days = FREQ_TO_DAYS.get(rec["frequence"], 30)
        last = rec.get("derniere_date")
        if isinstance(last, str):
            last = date.fromisoformat(last)
        if not last:
            last = today

        next_date = last + timedelta(days=freq_days)
        while next_date <= end_date:
            future_flows.append({
                "date": next_date,
                "montant": rec["montant_moyen"],
                "libelle": rec["libelle"],
                "categorie": rec["categorie"],
            })
            next_date += timedelta(days=freq_days)

    future_flows.sort(key=lambda f: f["date"])

    # Construire le prévisionnel jour par jour (agrégé par semaine)
    forecast = []
    solde = solde_actuel
    current_week = today

    while current_week <= end_date:
        week_end = current_week + timedelta(days=7)
        week_flows = [f for f in future_flows if current_week <= f["date"] < week_end]
        flux_total = sum(f["montant"] for f in week_flows)
        solde += flux_total

        forecast.append({
            "date": current_week.isoformat(),
            "solde_prevu": round(solde, 2),
            "flux_semaine": round(flux_total, 2),
            "nb_operations": len(week_flows),
        })
        current_week = week_end

    return forecast


def build_budget_summary(transactions: List[dict], mois: int = 1) -> dict:
    """
    Résumé budgétaire: revenus vs dépenses par catégorie sur N mois.
    """
    revenus = defaultdict(float)
    depenses = defaultdict(float)

    for tx in transactions:
        montant = tx.get("montant", 0)
        cat = tx.get("categorie", "autre")
        if montant >= 0:
            revenus[cat] += montant
        else:
            depenses[cat] += abs(montant)

    total_revenus = sum(revenus.values())
    total_depenses = sum(depenses.values())

    return {
        "periode_mois": mois,
        "total_revenus": round(total_revenus, 2),
        "total_depenses": round(total_depenses, 2),
        "solde_mensuel": round((total_revenus - total_depenses) / max(mois, 1), 2),
        "taux_epargne_pct": round((total_revenus - total_depenses) / total_revenus * 100, 1) if total_revenus > 0 else 0,
        "revenus_par_categorie": dict(revenus),
        "depenses_par_categorie": dict(depenses),
        "top_depenses": sorted(depenses.items(), key=lambda x: x[1], reverse=True)[:5],
    }
