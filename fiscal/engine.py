"""
Moteur de calcul fiscal français pour les investissements.
PFU, barème, PEA, AV, plus-values, abattements.
"""

from typing import Dict, Optional


# --- Constantes fiscales 2025 ---

PFU_TAUX = 0.30              # Flat Tax = 12.8% IR + 17.2% PS
PS_TAUX = 0.172              # Prélèvements sociaux
IR_PFU = 0.128               # Part IR du PFU

# PEA
PEA_PLAFOND_VERSEMENT = 150_000    # €
PEA_PME_PLAFOND = 225_000         # € (cumul PEA + PEA-PME)
PEA_DUREE_AVANTAGE = 5            # ans pour exonération IR

# Assurance-vie
AV_ABATTEMENT_ANNUEL_SOLO = 4_600    # € après 8 ans
AV_ABATTEMENT_ANNUEL_COUPLE = 9_200  # € après 8 ans
AV_TAUX_AVANT_8ANS = 0.128          # IR (hors PS)
AV_TAUX_APRES_8ANS_SOUS_150K = 0.075  # 7.5% IR (hors PS)
AV_TAUX_APRES_8ANS_PLUS_150K = 0.128  # 12.8% IR (hors PS)
AV_SEUIL_VERSEMENTS = 150_000        # €

# Crypto
CRYPTO_SEUIL_EXONERATION = 305  # € de cessions annuelles (2025)


class FiscalEngine:
    """Calcul de l'impact fiscal selon le profil utilisateur."""

    def __init__(self, profile: dict):
        self.profile = profile
        self.option = profile.get("option_fiscale", "pfu")
        self.tmi = profile.get("tmi", 0.30)
        self.situation = profile.get("situation_familiale", "celibataire")

    def calculer_impot_plus_value(self, gain_brut: float, enveloppe: str,
                                  anciennete_ans: int = 0,
                                  versements_av: float = 0) -> dict:
        """
        Calcule l'impôt sur une plus-value selon l'enveloppe.
        Retourne: impot, gain_net, taux_effectif, détail.
        """
        if gain_brut <= 0:
            return {
                "gain_brut": gain_brut,
                "impot": 0,
                "gain_net": gain_brut,
                "taux_effectif": 0,
                "detail": "Pas de plus-value, pas d'impôt",
            }

        if enveloppe == "pea":
            return self._impot_pea(gain_brut, anciennete_ans)
        elif enveloppe == "assurance_vie":
            return self._impot_av(gain_brut, anciennete_ans, versements_av)
        elif enveloppe == "per":
            return self._impot_per(gain_brut)
        elif enveloppe == "crypto":
            return self._impot_crypto(gain_brut)
        else:  # CTO
            return self._impot_cto(gain_brut)

    def _impot_cto(self, gain: float) -> dict:
        """CTO: PFU 30% ou barème progressif + PS."""
        if self.option == "pfu":
            impot = gain * PFU_TAUX
            detail = f"PFU: {IR_PFU*100}% IR + {PS_TAUX*100}% PS = {PFU_TAUX*100}%"
        else:
            impot_ir = gain * self.tmi
            impot_ps = gain * PS_TAUX
            impot = impot_ir + impot_ps
            detail = f"Barème: {self.tmi*100:.0f}% IR + {PS_TAUX*100}% PS = {(self.tmi+PS_TAUX)*100:.1f}%"

        return {
            "gain_brut": round(gain, 2),
            "impot": round(impot, 2),
            "gain_net": round(gain - impot, 2),
            "taux_effectif": round(impot / gain * 100, 1),
            "enveloppe": "CTO",
            "detail": detail,
        }

    def _impot_pea(self, gain: float, anciennete: int) -> dict:
        """PEA: exonéré d'IR après 5 ans, PS toujours dus."""
        if anciennete >= PEA_DUREE_AVANTAGE:
            impot = gain * PS_TAUX
            detail = f"PEA > 5 ans: IR exonéré, PS {PS_TAUX*100}% uniquement"
        else:
            impot = gain * PFU_TAUX
            detail = f"PEA < 5 ans: PFU {PFU_TAUX*100}% (clôture entraîne cette fiscalité)"

        return {
            "gain_brut": round(gain, 2),
            "impot": round(impot, 2),
            "gain_net": round(gain - impot, 2),
            "taux_effectif": round(impot / gain * 100, 1),
            "enveloppe": "PEA",
            "anciennete_ans": anciennete,
            "detail": detail,
        }

    def _impot_av(self, gain: float, anciennete: int, versements: float) -> dict:
        """Assurance-vie: abattement après 8 ans, taux réduit."""
        couple = self.situation == "marie_pacse"
        abattement = AV_ABATTEMENT_ANNUEL_COUPLE if couple else AV_ABATTEMENT_ANNUEL_SOLO

        if anciennete >= 8:
            gain_imposable = max(0, gain - abattement)
            if versements <= AV_SEUIL_VERSEMENTS:
                taux_ir = AV_TAUX_APRES_8ANS_SOUS_150K
            else:
                taux_ir = AV_TAUX_APRES_8ANS_PLUS_150K

            impot_ir = gain_imposable * taux_ir
            impot_ps = gain * PS_TAUX
            impot = impot_ir + impot_ps
            detail = (f"AV > 8 ans: abattement {abattement}€, "
                      f"taux IR {taux_ir*100}% sur {gain_imposable:.0f}€, "
                      f"+ PS {PS_TAUX*100}%")
        else:
            if self.option == "pfu":
                impot = gain * PFU_TAUX
                detail = f"AV < 8 ans: PFU {PFU_TAUX*100}%"
            else:
                impot = gain * (self.tmi + PS_TAUX)
                detail = f"AV < 8 ans: barème {self.tmi*100:.0f}% + PS {PS_TAUX*100}%"

        return {
            "gain_brut": round(gain, 2),
            "impot": round(impot, 2),
            "gain_net": round(gain - impot, 2),
            "taux_effectif": round(impot / gain * 100, 1) if gain > 0 else 0,
            "enveloppe": "Assurance-vie",
            "anciennete_ans": anciennete,
            "abattement_utilise": abattement if anciennete >= 8 else 0,
            "detail": detail,
        }

    def _impot_per(self, gain: float) -> dict:
        """PER: fiscalité à la sortie (barème IR sur capital, PFU sur gains)."""
        impot = gain * PFU_TAUX  # Sur les gains uniquement
        return {
            "gain_brut": round(gain, 2),
            "impot": round(impot, 2),
            "gain_net": round(gain - impot, 2),
            "taux_effectif": round(PFU_TAUX * 100, 1),
            "enveloppe": "PER",
            "detail": f"PER (sortie capital): PFU {PFU_TAUX*100}% sur les gains. "
                      f"Le capital versé est imposé au barème IR ({self.tmi*100:.0f}%)",
        }

    def _impot_crypto(self, gain: float, total_cessions_annuelles: float = 0) -> dict:
        """
        Crypto: PFU 30%, exonéré si total des cessions annuelles < 305€/an.
        NB: Le seuil de 305€ porte sur le montant TOTAL des cessions (ventes),
        PAS sur la plus-value. Si total_cessions_annuelles < 305€, exonération totale.
        """
        # Si l'utilisateur a vendu moins de 305€ de crypto dans l'année -> exonéré
        if total_cessions_annuelles > 0 and total_cessions_annuelles < CRYPTO_SEUIL_EXONERATION:
            return {
                "gain_brut": round(gain, 2),
                "impot": 0,
                "gain_net": round(gain, 2),
                "taux_effectif": 0,
                "enveloppe": "Crypto (CTO)",
                "detail": (
                    f"Exonéré: total cessions annuelles ({total_cessions_annuelles:.0f}€) "
                    f"< seuil {CRYPTO_SEUIL_EXONERATION}€. Aucun impôt dû."
                ),
            }

        impot = gain * PFU_TAUX
        detail = f"Crypto: PFU {PFU_TAUX*100}% (flat tax)"
        if total_cessions_annuelles == 0:
            detail += (
                f". NB: si le total de vos cessions annuelles (montant vendu, "
                f"pas la plus-value) est < {CRYPTO_SEUIL_EXONERATION}€, "
                f"vous êtes exonéré. Vérifiez ce montant."
            )

        return {
            "gain_brut": round(gain, 2),
            "impot": round(impot, 2),
            "gain_net": round(gain - impot, 2),
            "taux_effectif": round(PFU_TAUX * 100, 1),
            "enveloppe": "Crypto (CTO)",
            "detail": detail,
        }

    def comparer_enveloppes(self, gain: float, duree_ans: int = 0) -> list:
        """
        Compare la fiscalité entre différentes enveloppes pour un même gain.
        Aide à choisir la meilleure enveloppe.
        """
        results = []
        pea_anc = self.profile.get("pea_age_ans", 0) + duree_ans
        av_anc = self.profile.get("av_age_ans", 0) + duree_ans
        av_vers = self.profile.get("av_encours", 0)

        comparaisons = [
            ("CTO", "cto", {}),
            ("PEA", "pea", {"anciennete_ans": pea_anc}) if self.profile.get("has_pea") else None,
            ("Assurance-vie", "assurance_vie", {"anciennete_ans": av_anc, "versements_av": av_vers}) if self.profile.get("has_assurance_vie") else None,
            ("PER", "per", {}) if self.profile.get("has_per") else None,
        ]

        for entry in comparaisons:
            if entry is None:
                continue
            label, enveloppe, kwargs = entry
            result = self.calculer_impot_plus_value(gain, enveloppe, **kwargs)
            result["label"] = label
            results.append(result)

        results.sort(key=lambda x: x["impot"])
        return results

    def calculer_frais_totaux(self, montant: float, nb_ordres: int,
                               bank_frais: dict, duree_mois: int) -> dict:
        """
        Calcule le coût total (frais bancaires + fiscalité estimée) sur la durée.
        """
        # Frais d'ordre
        cout_ordre = bank_frais.get("cto_ordre", bank_frais.get("pea_ordre_0_500", 2.0))
        frais_ordres = cout_ordre * nb_ordres

        # Frais de garde annualisés
        garde_trim = bank_frais.get("garde_cto", bank_frais.get("garde", 0))
        frais_garde = garde_trim * 4 * montant / 100 * (duree_mois / 12)

        # Frais AV si applicable
        gestion_av = bank_frais.get("av_gestion_uc", 0)
        frais_av = gestion_av * montant / 100 * (duree_mois / 12) if gestion_av else 0

        # Frais d'entrée AV
        entree_av = bank_frais.get("av_entree", 0) * montant / 100

        total_frais = frais_ordres + frais_garde + frais_av + entree_av

        return {
            "frais_ordres": round(frais_ordres, 2),
            "frais_garde": round(frais_garde, 2),
            "frais_gestion_av": round(frais_av, 2),
            "frais_entree_av": round(entree_av, 2),
            "total_frais": round(total_frais, 2),
            "impact_rendement_pct": round(total_frais / montant * 100, 2) if montant > 0 else 0,
        }


def display_fiscal_comparison(gain: float, profile: dict, duree_ans: int = 0):
    """Affiche la comparaison fiscale entre enveloppes."""
    engine = FiscalEngine(profile)
    results = engine.comparer_enveloppes(gain, duree_ans)

    print(f"\n{'='*60}")
    print(f"  COMPARAISON FISCALE - Plus-value de {gain:.2f}€")
    if duree_ans:
        print(f"  Horizon: {duree_ans} an(s)")
    print(f"{'='*60}")

    print(f"\n  {'Enveloppe':<18} {'Impôt':>8} {'Net':>8} {'Taux':>6}  Détail")
    print(f"  {'─'*58}")

    for i, r in enumerate(results):
        marker = " *" if i == 0 else "  "
        print(f" {marker}{r.get('label', r['enveloppe']):<17} {r['impot']:>7.2f}€ "
              f"{r['gain_net']:>7.2f}€ {r['taux_effectif']:>5.1f}%  {r['detail'][:40]}")

    if results:
        best = results[0]
        worst = results[-1]
        economie = worst["impot"] - best["impot"]
        if economie > 0:
            print(f"\n  → Meilleur choix: {best.get('label', best['enveloppe'])} "
                  f"(économie: {economie:.2f}€ vs {worst.get('label', worst['enveloppe'])})")
