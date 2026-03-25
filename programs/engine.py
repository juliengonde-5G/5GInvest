"""
Moteur de programmes d'investissement autonomes.
Chaque programme a: budget, durée, risque, banque, instruments, objectif.
Persistance JSON. Un utilisateur peut avoir N programmes simultanés.
"""

import json
import os
import uuid
import datetime
from typing import List, Dict, Optional

from banks.catalog import get_bank, select_best_bank, get_user_banks
from fiscal.engine import FiscalEngine


PROGRAMS_FILE = "programs.json"

# Modèles d'allocation selon le profil de risque et la durée
ALLOCATION_MODELS = {
    # (risque, horizon) -> allocation cible
    ("prudent", "court"): {
        "fonds_euro": 50, "obligations_etf": 20, "etf_monde": 15,
        "monetaire": 15,
    },
    ("prudent", "moyen"): {
        "fonds_euro": 40, "obligations_etf": 20, "etf_monde": 25,
        "or_etf": 10, "monetaire": 5,
    },
    ("prudent", "long"): {
        "fonds_euro": 30, "etf_monde": 35, "obligations_etf": 20,
        "or_etf": 10, "scpi": 5,
    },
    ("equilibre", "court"): {
        "etf_monde": 35, "etf_sp500": 20, "obligations_etf": 20,
        "or_etf": 10, "crypto_btc": 5, "monetaire": 10,
    },
    ("equilibre", "moyen"): {
        "etf_monde": 40, "etf_sp500": 20, "etf_emergents": 10,
        "obligations_etf": 15, "or_etf": 10, "crypto_btc": 5,
    },
    ("equilibre", "long"): {
        "etf_monde": 45, "etf_sp500": 20, "etf_emergents": 10,
        "or_etf": 10, "fonds_euro": 10, "crypto_btc": 5,
    },
    ("dynamique", "court"): {
        "etf_sp500": 25, "etf_nasdaq": 20, "actions_growth": 20,
        "crypto_btc": 10, "crypto_alt": 5, "etf_monde": 15,
        "or_etf": 5,
    },
    ("dynamique", "moyen"): {
        "etf_sp500": 25, "etf_nasdaq": 20, "actions_growth": 15,
        "etf_emergents": 10, "crypto_btc": 10, "crypto_alt": 5,
        "etf_monde": 15,
    },
    ("dynamique", "long"): {
        "etf_sp500": 30, "etf_nasdaq": 20, "actions_growth": 15,
        "etf_emergents": 10, "crypto_btc": 10, "crypto_alt": 5,
        "etf_monde": 10,
    },
    ("agressif", "court"): {
        "actions_momentum": 25, "crypto_btc": 15, "crypto_alt": 15,
        "etf_levier": 15, "actions_growth": 20, "etf_nasdaq": 10,
    },
    ("agressif", "moyen"): {
        "actions_growth": 25, "crypto_btc": 15, "crypto_alt": 10,
        "etf_nasdaq": 20, "actions_small_cap": 15, "etf_emergents": 15,
    },
    ("agressif", "long"): {
        "actions_growth": 25, "etf_nasdaq": 20, "crypto_btc": 15,
        "crypto_alt": 10, "etf_emergents": 15, "actions_small_cap": 15,
    },
}

# Mapping catégories -> instruments concrets (symboles)
INSTRUMENTS_MAP = {
    "etf_monde": {"symbol": "IWDA.AS", "nom": "iShares MSCI World", "type": "etf", "enveloppe": ["pea", "cto"]},
    "etf_sp500": {"symbol": "CSPX.AS", "nom": "iShares S&P 500", "type": "etf", "enveloppe": ["pea", "cto"]},
    "etf_nasdaq": {"symbol": "EQQQ.DE", "nom": "Invesco Nasdaq 100", "type": "etf", "enveloppe": ["pea", "cto"]},
    "etf_emergents": {"symbol": "IS3N.DE", "nom": "iShares MSCI EM", "type": "etf", "enveloppe": ["cto"]},
    "etf_levier": {"symbol": "CL2.PA", "nom": "Amundi Lev MSCI USA Daily 2x", "type": "etf", "enveloppe": ["cto"]},
    "obligations_etf": {"symbol": "AGGH.AS", "nom": "iShares Global Agg Bond", "type": "etf", "enveloppe": ["cto"]},
    "or_etf": {"symbol": "IGLN.AS", "nom": "iShares Physical Gold", "type": "etf", "enveloppe": ["cto"]},
    "crypto_btc": {"symbol": "BTC", "nom": "Bitcoin", "type": "crypto", "enveloppe": ["cto"]},
    "crypto_alt": {"symbol": "ETH", "nom": "Ethereum", "type": "crypto", "enveloppe": ["cto"]},
    "actions_growth": {"symbol": "NVDA", "nom": "NVIDIA (exemple growth)", "type": "action", "enveloppe": ["cto"]},
    "actions_momentum": {"symbol": "TSLA", "nom": "Tesla (exemple momentum)", "type": "action", "enveloppe": ["cto"]},
    "actions_small_cap": {"symbol": "PLTR", "nom": "Palantir (exemple small cap)", "type": "action", "enveloppe": ["cto"]},
    "fonds_euro": {"symbol": "FONDS_EURO", "nom": "Fonds Euro (assurance-vie)", "type": "fonds_euro", "enveloppe": ["assurance_vie"]},
    "monetaire": {"symbol": "XEON.DE", "nom": "Xtrackers EUR Overnight Rate", "type": "etf", "enveloppe": ["cto"]},
    "scpi": {"symbol": "SCPI", "nom": "SCPI (assurance-vie)", "type": "scpi", "enveloppe": ["assurance_vie"]},
}


class ProgramManager:
    """Gestionnaire de programmes d'investissement."""

    def __init__(self, filepath: str = None):
        self.filepath = filepath or PROGRAMS_FILE
        self.data = self._load()

    def create_program(self, profile: dict) -> dict:
        """Crée un nouveau programme via questionnaire interactif."""
        print(f"\n{'='*60}")
        print("  CRÉATION D'UN NOUVEAU PROGRAMME D'INVESTISSEMENT")
        print(f"{'='*60}")

        program = {
            "id": str(uuid.uuid4())[:8],
            "created_at": datetime.datetime.now().isoformat(),
            "status": "active",
        }

        # Nom du programme
        program["nom"] = _ask("Nom du programme", f"Programme {len(self.data.get('programs', [])) + 1}")

        # Budget
        program["budget_initial"] = _ask_float("Budget initial (€)", 100.0)
        program["budget_restant"] = program["budget_initial"]

        # Durée / horizon
        print("\n  Horizon d'investissement:")
        print("  1. Court terme (< 1 an)")
        print("  2. Moyen terme (1-5 ans)")
        print("  3. Long terme (> 5 ans)")
        program["horizon"] = _ask_choice("Horizon", ["court", "moyen", "long"], 1)

        duree_map = {"court": 6, "moyen": 36, "long": 120}
        program["duree_mois"] = _ask_int(
            "Durée cible en mois",
            duree_map[program["horizon"]]
        )

        # Risque
        print("\n  Niveau de risque:")
        print("  1. Prudent     (2-4% visé)")
        print("  2. Équilibré   (4-7% visé)")
        print("  3. Dynamique   (7-12% visé)")
        print("  4. Agressif    (>12% visé)")
        program["risque"] = _ask_choice(
            "Risque",
            ["prudent", "equilibre", "dynamique", "agressif"],
            2
        )

        # Objectif de rendement
        rendement_map = {
            "prudent": 3, "equilibre": 6, "dynamique": 10, "agressif": 15,
        }
        program["objectif_rendement_pct"] = _ask_float(
            "Objectif de rendement annuel (%)",
            rendement_map[program["risque"]]
        )

        # Banque(s) pour ce programme
        user_banks = profile.get("banques", ["Revolut"])
        print(f"\n  Vos banques: {', '.join(user_banks)}")
        bank_input = _ask("Banque(s) pour ce programme", ", ".join(user_banks))
        program["banques"] = [b.strip() for b in bank_input.split(",")]

        # Enveloppe préférée
        all_envs = set()
        for bank_name in program["banques"]:
            bank = get_bank(bank_name)
            if bank:
                all_envs.update(bank.get("enveloppes", []))

        env_list = sorted(all_envs)
        if env_list:
            print(f"\n  Enveloppes disponibles: {', '.join(env_list)}")
            program["enveloppe_preferee"] = _ask("Enveloppe préférée", env_list[0])
        else:
            program["enveloppe_preferee"] = "cto"

        # DCA (investissement régulier)
        program["dca_enabled"] = _ask_bool("Activer le DCA (investissement régulier) ?", False)
        if program["dca_enabled"]:
            program["dca_montant"] = _ask_float("Montant DCA mensuel (€)", 50.0)
            program["dca_frequence"] = _ask_choice(
                "Fréquence (hebdo, mensuel, trimestriel)",
                ["hebdo", "mensuel", "trimestriel"], 2
            )

        # Générer l'allocation
        program["allocation"] = self._generer_allocation(program, profile)
        program["positions"] = {}
        program["historique"] = []

        # Sauvegarder
        if "programs" not in self.data:
            self.data["programs"] = []
        self.data["programs"].append(program)
        self._save()

        return program

    def _generer_allocation(self, program: dict, profile: dict) -> list:
        """Génère l'allocation cible basée sur le risque et l'horizon."""
        key = (program["risque"], program["horizon"])
        model = ALLOCATION_MODELS.get(key, ALLOCATION_MODELS[("equilibre", "court")])

        budget = program["budget_initial"]
        fiscal = FiscalEngine(profile)
        allocation = []

        for categorie, pct in model.items():
            instrument = INSTRUMENTS_MAP.get(categorie, {})
            montant = round(budget * pct / 100, 2)

            if montant < 1:  # Sous le minimum Revolut
                continue

            # Vérifier la disponibilité dans les banques du programme
            available_banks = []
            for bank_name in program.get("banques", []):
                bank = get_bank(bank_name)
                if bank:
                    produits = bank.get("produits", {})
                    if instrument.get("type") in ("etf", "action"):
                        if produits.get("etf") or produits.get(f"actions_{instrument.get('type', '')}", True):
                            available_banks.append(bank.get("nom", bank_name))
                    elif instrument.get("type") == "crypto":
                        if produits.get("crypto"):
                            available_banks.append(bank.get("nom", bank_name))
                    elif instrument.get("type") == "fonds_euro":
                        if produits.get("fonds_euro"):
                            available_banks.append(bank.get("nom", bank_name))
                    else:
                        available_banks.append(bank.get("nom", bank_name))

            # Impact fiscal estimé
            gain_estime = montant * program["objectif_rendement_pct"] / 100
            enveloppe = program.get("enveloppe_preferee", "cto")
            fiscal_impact = fiscal.calculer_impot_plus_value(gain_estime, enveloppe)

            allocation.append({
                "categorie": categorie,
                "pct": pct,
                "montant_eur": montant,
                "instrument": instrument,
                "banques_disponibles": available_banks,
                "fiscal_taux_effectif": fiscal_impact.get("taux_effectif", 30),
            })

        return allocation

    def list_programs(self) -> list:
        """Liste tous les programmes."""
        return self.data.get("programs", [])

    def get_program(self, program_id: str) -> Optional[dict]:
        """Récupère un programme par ID ou nom."""
        for p in self.data.get("programs", []):
            if p["id"] == program_id or p.get("nom", "").lower() == program_id.lower():
                return p
        return None

    def delete_program(self, program_id: str) -> bool:
        """Supprime un programme."""
        programs = self.data.get("programs", [])
        self.data["programs"] = [p for p in programs if p["id"] != program_id]
        self._save()
        return len(self.data["programs"]) < len(programs)

    def display_program(self, program: dict):
        """Affiche le détail d'un programme."""
        print(f"\n{'='*65}")
        print(f"  PROGRAMME: {program['nom']} [{program['id']}]")
        print(f"{'='*65}")
        print(f"  Status:     {program['status']}")
        print(f"  Budget:     {program['budget_initial']:.2f}€")
        print(f"  Horizon:    {program['horizon']} ({program['duree_mois']} mois)")
        print(f"  Risque:     {program['risque']}")
        print(f"  Rendement:  {program['objectif_rendement_pct']}% visé / an")
        print(f"  Banques:    {', '.join(program.get('banques', []))}")
        print(f"  Enveloppe:  {program.get('enveloppe_preferee', 'CTO')}")

        if program.get("dca_enabled"):
            print(f"  DCA:        {program['dca_montant']}€ / {program['dca_frequence']}")

        print(f"\n  ALLOCATION CIBLE")
        print(f"  {'─'*60}")
        print(f"  {'Catégorie':<22} {'%':>5} {'Montant':>8}  {'Instrument':<20} {'Banque'}")
        print(f"  {'─'*60}")

        for a in program.get("allocation", []):
            instr = a.get("instrument", {})
            banks = ", ".join(a.get("banques_disponibles", [])[:2])
            fiscal_note = f" (fiscal: {a['fiscal_taux_effectif']:.0f}%)" if a.get("fiscal_taux_effectif") else ""
            print(f"  {a['categorie']:<22} {a['pct']:>4}% {a['montant_eur']:>7.2f}€  "
                  f"{instr.get('nom', '?')[:20]:<20} {banks}")

        total = sum(a["montant_eur"] for a in program.get("allocation", []))
        print(f"  {'─'*60}")
        print(f"  {'TOTAL':<22} {'100':>4}% {total:>7.2f}€")

    def display_all_programs(self):
        """Résumé de tous les programmes."""
        programs = self.list_programs()
        if not programs:
            print("\n  Aucun programme créé. Utilisez: python main.py program create")
            return

        print(f"\n{'='*70}")
        print(f"  VOS PROGRAMMES D'INVESTISSEMENT ({len(programs)})")
        print(f"{'='*70}")
        print(f"  {'ID':<10} {'Nom':<20} {'Budget':>8} {'Risque':<12} {'Horizon':<8} {'Status'}")
        print(f"  {'─'*68}")

        for p in programs:
            print(f"  {p['id']:<10} {p['nom']:<20} {p['budget_initial']:>7.0f}€ "
                  f"{p['risque']:<12} {p['horizon']:<8} {p['status']}")

    def _load(self) -> dict:
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        return {"programs": []}

    def _save(self):
        with open(self.filepath, "w") as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)


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
