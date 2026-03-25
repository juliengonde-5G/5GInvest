"""
Profil utilisateur: questionnaire fiscal, situation personnelle,
préférences d'investissement. Persistance JSON.
"""

import json
import os
import datetime
from typing import Optional


from config.paths import PROFILE_FILE

# Tranches d'imposition IR 2025 (revenus 2024)
TRANCHES_IR_2025 = [
    (11_294, 0.00),
    (28_797, 0.11),
    (82_341, 0.30),
    (177_106, 0.41),
    (float("inf"), 0.45),
]


def questionnaire_interactif() -> dict:
    """Questionnaire complet pour configurer le profil utilisateur."""
    print("\n" + "=" * 60)
    print("  CONFIGURATION DE VOTRE PROFIL INVESTISSEUR")
    print("=" * 60)

    profile = {}

    # --- Identité ---
    print("\n--- Identité ---")
    profile["prenom"] = _ask("Prénom", "Investisseur")
    profile["age"] = _ask_int("Âge", 30)

    # --- Situation fiscale ---
    print("\n--- Situation fiscale ---")
    print("  1. Célibataire")
    print("  2. Marié / Pacsé")
    print("  3. Divorcé")
    print("  4. Veuf")
    profile["situation_familiale"] = _ask_choice(
        "Situation familiale", ["celibataire", "marie_pacse", "divorce", "veuf"], 1
    )
    profile["nb_parts_fiscales"] = _ask_float("Nombre de parts fiscales", 1.0)
    profile["revenu_annuel_net"] = _ask_int("Revenu annuel net imposable (€)", 30000)

    # Calcul TMI
    profile["tmi"] = _calculer_tmi(profile["revenu_annuel_net"], profile["nb_parts_fiscales"])
    print(f"  → Votre tranche marginale d'imposition (TMI): {profile['tmi']*100:.0f}%")

    # --- PFU ou barème ---
    print("\n--- Option fiscale pour les revenus de capitaux ---")
    print("  1. PFU (Flat Tax 30%) - Par défaut, simple et souvent optimal")
    print("  2. Barème progressif IR (+ 17.2% PS) - Intéressant si TMI ≤ 11%")
    choice = _ask_choice("Option fiscale", ["pfu", "bareme"], 1)
    profile["option_fiscale"] = choice
    if choice == "pfu":
        profile["taux_imposition_gains"] = 0.30  # 12.8% IR + 17.2% PS
    else:
        profile["taux_imposition_gains"] = profile["tmi"] + 0.172

    print(f"  → Taux effectif sur vos plus-values: {profile['taux_imposition_gains']*100:.1f}%")

    # --- Enveloppes fiscales existantes ---
    print("\n--- Enveloppes fiscales détenues ---")
    profile["has_pea"] = _ask_bool("Avez-vous un PEA ?", False)
    if profile["has_pea"]:
        profile["pea_age_ans"] = _ask_int("Depuis combien d'années (ancienneté PEA)?", 0)
        profile["pea_montant_verse"] = _ask_float("Montant total versé sur le PEA (€)", 0)
    profile["has_pea_pme"] = _ask_bool("Avez-vous un PEA-PME ?", False)
    profile["has_assurance_vie"] = _ask_bool("Avez-vous une assurance-vie ?", False)
    if profile["has_assurance_vie"]:
        profile["av_age_ans"] = _ask_int("Ancienneté de l'AV (années)?", 0)
        profile["av_encours"] = _ask_float("Encours total AV (€)", 0)
    profile["has_per"] = _ask_bool("Avez-vous un PER ?", False)
    profile["has_cto"] = _ask_bool("Avez-vous un CTO (compte-titres ordinaire) ?", True)

    # --- Banques ---
    print("\n--- Banques et courtiers ---")
    print("  Banques disponibles: Revolut, Boursorama, Fortuneo, BoursoBank,")
    print("  Trade Republic, Degiro, Bourse Direct, SG, BNP, CA, LCL, N26")
    banks_input = _ask(
        "Vos banques (séparées par des virgules)",
        "Revolut"
    )
    profile["banques"] = [b.strip() for b in banks_input.split(",")]

    # --- Profil de risque ---
    print("\n--- Profil de risque ---")
    print("  1. Prudent     - Capital garanti, rendement faible (2-4%)")
    print("  2. Équilibré   - Mix sécurité/rendement (4-7%)")
    print("  3. Dynamique   - Accepte la volatilité (7-12%)")
    print("  4. Agressif    - Rendement max, risque élevé (>12%)")
    profile["profil_risque"] = _ask_choice(
        "Profil de risque",
        ["prudent", "equilibre", "dynamique", "agressif"],
        2
    )

    # --- Objectifs ---
    print("\n--- Objectifs ---")
    profile["objectif_principal"] = _ask(
        "Objectif principal (épargne, retraite, projet, trading)",
        "trading"
    )
    profile["horizon_global"] = _ask_choice(
        "Horizon global (court <1an, moyen 1-5ans, long >5ans)",
        ["court", "moyen", "long"],
        1
    )

    # --- Expérience ---
    print("\n--- Expérience ---")
    profile["experience_bourse"] = _ask_choice(
        "Expérience en bourse (debutant, intermediaire, avance)",
        ["debutant", "intermediaire", "avance"],
        1
    )

    # --- Métadonnées ---
    profile["created_at"] = datetime.datetime.now().isoformat()
    profile["updated_at"] = datetime.datetime.now().isoformat()

    # Sauvegarder
    save_profile(profile)
    print(f"\n  Profil sauvegardé dans {PROFILE_FILE}")

    return profile


def _calculer_tmi(revenu_net: float, parts: float) -> float:
    """Calcule la tranche marginale d'imposition."""
    quotient = revenu_net / parts
    tmi = 0.0
    for plafond, taux in TRANCHES_IR_2025:
        if quotient <= plafond:
            tmi = taux
            break
        tmi = taux
    return tmi


def save_profile(profile: dict, filepath: str = None):
    """Sauvegarde le profil."""
    filepath = filepath or PROFILE_FILE
    profile["updated_at"] = datetime.datetime.now().isoformat()
    with open(filepath, "w") as f:
        json.dump(profile, f, indent=2, ensure_ascii=False)


def load_profile(filepath: str = None) -> Optional[dict]:
    """Charge le profil existant."""
    filepath = filepath or PROFILE_FILE
    if os.path.exists(filepath):
        try:
            with open(filepath, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return None


def get_or_create_profile() -> dict:
    """Charge le profil ou lance le questionnaire."""
    profile = load_profile()
    if profile:
        print(f"\n  Profil chargé: {profile.get('prenom', 'Utilisateur')} "
              f"(TMI: {profile.get('tmi', 0)*100:.0f}%, "
              f"Risque: {profile.get('profil_risque', '?')})")
        update = _ask_bool("Mettre à jour le profil ?", False)
        if update:
            return questionnaire_interactif()
        return profile
    return questionnaire_interactif()


# --- Helpers input ---

def _ask(question: str, default: str = "") -> str:
    try:
        val = input(f"  {question} [{default}]: ").strip()
        return val if val else default
    except (EOFError, KeyboardInterrupt):
        return default


def _ask_int(question: str, default: int = 0) -> int:
    try:
        val = input(f"  {question} [{default}]: ").strip()
        return int(val) if val else default
    except (ValueError, EOFError, KeyboardInterrupt):
        return default


def _ask_float(question: str, default: float = 0.0) -> float:
    try:
        val = input(f"  {question} [{default}]: ").strip()
        return float(val) if val else default
    except (ValueError, EOFError, KeyboardInterrupt):
        return default


def _ask_bool(question: str, default: bool = False) -> bool:
    d = "o" if default else "n"
    try:
        val = input(f"  {question} (o/n) [{d}]: ").strip().lower()
        if not val:
            return default
        return val in ("o", "oui", "y", "yes")
    except (EOFError, KeyboardInterrupt):
        return default


def _ask_choice(question: str, choices: list, default_idx: int = 1) -> str:
    try:
        val = input(f"  {question} [{default_idx}]: ").strip()
        if not val:
            return choices[default_idx - 1]
        idx = int(val)
        if 1 <= idx <= len(choices):
            return choices[idx - 1]
        return choices[default_idx - 1]
    except (ValueError, EOFError, KeyboardInterrupt):
        return choices[default_idx - 1]
