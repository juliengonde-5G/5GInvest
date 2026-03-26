"""
Génération de rapport fiscal annuel PDF (récap pour déclaration).
Utilise ReportLab.
"""

import io
import os
from datetime import date
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable


def generate_fiscal_report(profile: dict, dashboard: dict, year: int = None) -> bytes:
    """
    Génère un PDF de récapitulatif fiscal annuel.
    Retourne les bytes du PDF.
    """
    if not year:
        year = date.today().year - 1  # Année précédente par défaut

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            leftMargin=2*cm, rightMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("Title2", parent=styles["Title"], fontSize=18, textColor=HexColor("#1a1a2e"))
    h2_style = ParagraphStyle("H2", parent=styles["Heading2"], fontSize=14, spaceAfter=10, textColor=HexColor("#3b3b5c"))
    normal = styles["Normal"]
    small = ParagraphStyle("Small", parent=normal, fontSize=8, textColor=HexColor("#666666"))

    story = []

    # ─── EN-TÊTE ──────────────────────────────────────────
    story.append(Paragraph(f"Récapitulatif fiscal {year}", title_style))
    story.append(Paragraph(f"Généré le {date.today().strftime('%d/%m/%Y')} - {profile.get('prenom', '')} {profile.get('nom', '')}", small))
    story.append(Spacer(1, 0.5*cm))
    story.append(HRFlowable(width="100%", color=HexColor("#e0e0e0")))
    story.append(Spacer(1, 0.5*cm))

    # ─── PROFIL FISCAL ────────────────────────────────────
    story.append(Paragraph("1. Profil fiscal", h2_style))
    profil_data = [
        ["TMI", f"{profile.get('tmi', 0)*100:.0f}%"],
        ["Option fiscale", profile.get("option_fiscale", "PFU").upper()],
        ["Parts fiscales", str(profile.get("nb_parts_fiscales", 1))],
        ["Revenu net annuel", fmt(profile.get("revenu_net_annuel", 0))],
    ]
    story.append(_make_table(profil_data))
    story.append(Spacer(1, 0.5*cm))

    # ─── PATRIMOINE ───────────────────────────────────────
    story.append(Paragraph("2. Patrimoine au 31/12", h2_style))
    alloc = dashboard.get("allocation", {})
    patrimoine_data = [
        ["Classe d'actif", "Valeur", "% du total"],
        ["Immobilier (valeur nette)", fmt(alloc.get("immo", 0)), f"{alloc.get('immo_pct', 0):.1f}%"],
        ["Crypto-actifs", fmt(alloc.get("crypto", 0)), f"{alloc.get('crypto_pct', 0):.1f}%"],
        ["Matières premières", fmt(alloc.get("commodity", 0)), f"{alloc.get('commodity_pct', 0):.1f}%"],
        ["Cash et épargne", fmt(alloc.get("cash", 0)), f"{alloc.get('cash_pct', 0):.1f}%"],
        ["TOTAL", fmt(dashboard.get("net_worth", 0)), "100%"],
    ]
    story.append(_make_table(patrimoine_data, header=True))
    story.append(Spacer(1, 0.5*cm))

    # ─── IMMOBILIER ───────────────────────────────────────
    immo_list = dashboard.get("real_estate", [])
    if immo_list:
        story.append(Paragraph("3. Immobilier - Plus-values latentes", h2_style))
        immo_data = [["Bien", "Détention", "PV brute", "Abattement IR", "Impôt PV estimé"]]
        for p in immo_list:
            pv = p.get("impot_pv_estime", {})
            immo_data.append([
                p.get("nom", "?"),
                f"{p.get('duree_detention_ans', 0):.0f} ans",
                fmt(p.get("plus_value_brute", 0)),
                f"{p.get('abattement_pv_ir_pct', 0) if hasattr(p, 'abattement_pv_ir_pct') else '?'}%",
                "Exonéré" if pv.get("exonere") else fmt(pv.get("total", 0)),
            ])
        story.append(_make_table(immo_data, header=True))
        story.append(Spacer(1, 0.5*cm))

    # ─── CRYPTO ───────────────────────────────────────────
    crypto_list = dashboard.get("crypto", [])
    if crypto_list:
        story.append(Paragraph("4. Crypto-actifs - P&L", h2_style))
        story.append(Paragraph(
            f"Rappel: si le total de vos cessions annuelles est inférieur à 305€, "
            f"vous êtes exonéré d'impôt. Sinon, flat tax 30%.", small
        ))
        crypto_data = [["Symbole", "Quantité", "P. achat moy.", "Valeur actuelle", "P&L", "P&L %"]]
        for c in crypto_list:
            crypto_data.append([
                c.get("symbol", "?"),
                f"{c.get('quantite', 0):.4f}",
                fmt(c.get("prix_achat_moyen", 0)),
                fmt(c.get("current_value", 0)),
                fmt(c.get("pnl_eur", 0)),
                f"{c.get('pnl_pct', 0):+.1f}%",
            ])
        story.append(_make_table(crypto_data, header=True))
        story.append(Spacer(1, 0.5*cm))

    # ─── CASH ─────────────────────────────────────────────
    cash_list = dashboard.get("cash", [])
    if cash_list:
        story.append(Paragraph("5. Épargne et comptes bancaires", h2_style))
        cash_data = [["Compte", "Type", "Solde", "Taux", "Intérêts estimés/an"]]
        for c in cash_list:
            cash_data.append([
                c.get("nom", "?"),
                c.get("type_label", c.get("type_compte", "")),
                fmt(c.get("solde", 0)),
                f"{c.get('taux_interet', 0)}%",
                fmt(c.get("interet_annuel_estime", 0)),
            ])
        story.append(_make_table(cash_data, header=True))
        story.append(Spacer(1, 0.5*cm))

    # ─── DISCLAIMER ───────────────────────────────────────
    story.append(Spacer(1, 1*cm))
    story.append(HRFlowable(width="100%", color=HexColor("#e0e0e0")))
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph(
        "Ce document est un récapitulatif automatique à usage personnel. "
        "Il ne se substitue pas à l'IFU fourni par vos établissements financiers. "
        "Ne constitue pas un conseil fiscal. Consultez un professionnel pour votre déclaration.",
        small
    ))

    doc.build(story)
    return buffer.getvalue()


def _make_table(data, header=False):
    """Crée un tableau ReportLab formaté."""
    style_cmds = [
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#e0e0e0")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]
    if header:
        style_cmds.extend([
            ("BACKGROUND", (0, 0), (-1, 0), HexColor("#f5f5f7")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 8),
            ("TEXTCOLOR", (0, 0), (-1, 0), HexColor("#3b3b5c")),
        ])
    t = Table(data, repeatRows=1 if header else 0)
    t.setStyle(TableStyle(style_cmds))
    return t


def fmt(n):
    if n is None:
        return "—"
    try:
        return f"{float(n):,.0f} €".replace(",", " ")
    except (ValueError, TypeError):
        return str(n)
