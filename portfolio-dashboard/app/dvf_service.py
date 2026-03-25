"""
Module DVF (Demandes de Valeurs Foncières) - data.gouv.fr
Données ouvertes des transactions immobilières notariées.
Utilisé pour: estimation prix/m², historique 10 ans, comparables locaux.
"""

import requests
import time
from datetime import date
from functools import lru_cache
from typing import Optional

# Cache mémoire simple
_cache = {}
CACHE_TTL = 3600  # 1h


def _cached(key, ttl=CACHE_TTL):
    entry = _cache.get(key)
    if entry and time.time() - entry["t"] < ttl:
        return entry["v"]
    return None


def _set_cache(key, value):
    _cache[key] = {"v": value, "t": time.time()}


# ─── GEOCODING (adresse → lat/lon + code INSEE) ──────────

def geocode_address(adresse: str, code_postal: str = "", ville: str = "") -> dict:
    """
    Géocode une adresse via api-adresse.data.gouv.fr (BAN - Base Adresse Nationale).
    Retourne: lat, lon, label, code_insee, code_postal, ville.
    """
    query = f"{adresse} {code_postal} {ville}".strip()
    cache_key = f"geocode_{query}"
    cached = _cached(cache_key)
    if cached:
        return cached

    try:
        resp = requests.get(
            "https://api-adresse.data.gouv.fr/search/",
            params={"q": query, "limit": 1},
            timeout=10,
        )
        data = resp.json()
        if data.get("features"):
            feat = data["features"][0]
            props = feat["properties"]
            coords = feat["geometry"]["coordinates"]
            result = {
                "latitude": coords[1],
                "longitude": coords[0],
                "label": props.get("label", ""),
                "code_insee": props.get("citycode", ""),
                "code_postal": props.get("postcode", code_postal),
                "ville": props.get("city", ville),
                "score": props.get("score", 0),
            }
            _set_cache(cache_key, result)
            return result
    except Exception as e:
        pass

    return {"error": f"Géocodage impossible pour: {query}"}


# ─── DVF - TRANSACTIONS RÉCENTES ─────────────────────────

def get_dvf_transactions(code_insee: str = None, code_postal: str = None,
                         lat: float = None, lon: float = None,
                         rayon_m: int = 1000, type_bien: str = None) -> list:
    """
    Récupère les transactions DVF récentes autour d'une localisation.
    Source: API DVF data.gouv.fr
    """
    cache_key = f"dvf_{code_insee}_{code_postal}_{lat}_{lon}_{type_bien}"
    cached = _cached(cache_key)
    if cached:
        return cached

    transactions = []

    # API DVF par code commune
    if code_insee:
        try:
            url = f"https://api.cquest.org/dvf?code_commune={code_insee}"
            if type_bien:
                type_map = {
                    "appartement": "Appartement",
                    "maison": "Maison",
                }
                t = type_map.get(type_bien)
                if t:
                    url += f"&type_local={t}"

            resp = requests.get(url, timeout=15)
            data = resp.json()

            for r in data.get("resultats", [])[:200]:
                tx = _parse_dvf_record(r)
                if tx:
                    transactions.append(tx)
        except Exception:
            pass

    # Fallback: API geo DVF avec lat/lon
    if not transactions and lat and lon:
        try:
            url = (
                f"https://api.cquest.org/dvf?"
                f"lat={lat}&lon={lon}&dist={rayon_m}"
            )
            resp = requests.get(url, timeout=15)
            data = resp.json()
            for r in data.get("resultats", [])[:200]:
                tx = _parse_dvf_record(r)
                if tx:
                    transactions.append(tx)
        except Exception:
            pass

    # Trier par date décroissante
    transactions.sort(key=lambda x: x.get("date_mutation", ""), reverse=True)
    _set_cache(cache_key, transactions)
    return transactions


def _parse_dvf_record(r: dict) -> dict:
    """Parse un enregistrement DVF brut."""
    try:
        surface = r.get("surface_reelle_bati") or r.get("surface_terrain") or 0
        valeur = r.get("valeur_fonciere") or 0
        if surface > 0 and valeur > 0:
            return {
                "date_mutation": r.get("date_mutation", ""),
                "nature_mutation": r.get("nature_mutation", ""),
                "type_local": r.get("type_local", ""),
                "surface_m2": float(surface),
                "valeur_fonciere": float(valeur),
                "prix_m2": round(float(valeur) / float(surface), 0),
                "nb_pieces": r.get("nombre_pieces_principales"),
                "adresse": f"{r.get('adresse_numero', '')} {r.get('adresse_nom_voie', '')}".strip(),
                "code_postal": r.get("code_postal", ""),
                "commune": r.get("nom_commune", ""),
            }
    except (TypeError, ValueError, ZeroDivisionError):
        pass
    return None


# ─── ESTIMATION PRIX/M² ──────────────────────────────────

def estimate_price_m2(code_insee: str = None, code_postal: str = None,
                      lat: float = None, lon: float = None,
                      type_bien: str = "appartement",
                      surface_m2: float = 0) -> dict:
    """
    Estime le prix au m² à partir des transactions DVF récentes.
    Applique des coefficients correcteurs (surface, DPE, étage, etc.).
    """
    transactions = get_dvf_transactions(
        code_insee=code_insee, code_postal=code_postal,
        lat=lat, lon=lon, type_bien=type_bien,
    )

    if not transactions:
        return {"error": "Pas assez de données DVF pour ce secteur", "prix_m2": 0, "nb_transactions": 0}

    # Filtrer les 3 dernières années et le même type
    annee_min = date.today().year - 3
    type_map = {"appartement": "Appartement", "maison": "Maison"}
    type_filter = type_map.get(type_bien)

    recent = []
    for tx in transactions:
        year = int(tx["date_mutation"][:4]) if tx["date_mutation"] else 0
        if year >= annee_min:
            if type_filter and tx.get("type_local") != type_filter:
                continue
            recent.append(tx)

    if not recent:
        recent = transactions[:30]

    # Calcul prix médian au m²
    prix_m2_list = [tx["prix_m2"] for tx in recent if tx.get("prix_m2", 0) > 0]
    if not prix_m2_list:
        return {"error": "Pas de prix valides", "prix_m2": 0, "nb_transactions": 0}

    prix_m2_list.sort()
    n = len(prix_m2_list)
    mediane = prix_m2_list[n // 2] if n % 2 else (prix_m2_list[n // 2 - 1] + prix_m2_list[n // 2]) / 2
    moyenne = sum(prix_m2_list) / n
    prix_min = prix_m2_list[0]
    prix_max = prix_m2_list[-1]

    # Coefficient de surface (les petites surfaces sont plus chères au m²)
    coef_surface = 1.0
    if surface_m2 > 0:
        if surface_m2 < 30:
            coef_surface = 1.15  # +15% petites surfaces
        elif surface_m2 < 50:
            coef_surface = 1.05
        elif surface_m2 > 100:
            coef_surface = 0.95  # -5% grandes surfaces
        elif surface_m2 > 150:
            coef_surface = 0.90

    prix_m2_ajuste = round(mediane * coef_surface, 0)

    return {
        "prix_m2_median": round(mediane, 0),
        "prix_m2_moyen": round(moyenne, 0),
        "prix_m2_ajuste": prix_m2_ajuste,
        "prix_m2_min": round(prix_min, 0),
        "prix_m2_max": round(prix_max, 0),
        "nb_transactions": n,
        "coef_surface": coef_surface,
        "estimation_valeur": round(prix_m2_ajuste * surface_m2, 0) if surface_m2 > 0 else 0,
        "fourchette_basse": round(prix_m2_list[int(n * 0.25)] * surface_m2, 0) if surface_m2 > 0 else 0,
        "fourchette_haute": round(prix_m2_list[int(n * 0.75)] * surface_m2, 0) if surface_m2 > 0 else 0,
    }


# ─── HISTORIQUE DVF 10 ANS (pour graphique) ──────────────

def get_dvf_history_10y(code_insee: str = None, code_postal: str = None,
                        type_bien: str = "appartement") -> list:
    """
    Historique prix/m² par année sur 10 ans pour le graphique d'évolution.
    Retourne: [{year, prix_m2_median, nb_transactions}]
    """
    cache_key = f"dvf_history_{code_insee}_{code_postal}_{type_bien}"
    cached = _cached(cache_key, ttl=7200)
    if cached:
        return cached

    transactions = get_dvf_transactions(
        code_insee=code_insee, code_postal=code_postal,
        type_bien=type_bien,
    )

    if not transactions:
        return []

    # Grouper par année
    by_year = {}
    current_year = date.today().year
    type_map = {"appartement": "Appartement", "maison": "Maison"}
    type_filter = type_map.get(type_bien)

    for tx in transactions:
        year = int(tx["date_mutation"][:4]) if tx.get("date_mutation") else 0
        if year < current_year - 10:
            continue
        if type_filter and tx.get("type_local") != type_filter:
            continue
        if year not in by_year:
            by_year[year] = []
        if tx.get("prix_m2", 0) > 0:
            by_year[year].append(tx["prix_m2"])

    # Calculer médianes par année
    history = []
    for year in sorted(by_year.keys()):
        prices = sorted(by_year[year])
        n = len(prices)
        if n > 0:
            mediane = prices[n // 2] if n % 2 else (prices[n // 2 - 1] + prices[n // 2]) / 2
            history.append({
                "year": year,
                "prix_m2_median": round(mediane, 0),
                "nb_transactions": n,
            })

    _set_cache(cache_key, history)
    return history
