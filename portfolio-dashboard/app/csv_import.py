"""
Import CSV/OFX de relevés bancaires.
Supporte les formats d'export de toutes les banques françaises.
Auto-détection du format (séparateur, colonnes, encodage).
"""

import csv
import io
import re
from datetime import date, datetime
from typing import List, Dict, Optional


# Formats connus par banque (colonnes attendues)
BANK_FORMATS = {
    "boursorama": {
        "date_cols": ["dateOp", "Date opération", "date"],
        "label_cols": ["label", "Libellé", "libelle"],
        "amount_cols": ["amount", "Montant", "montant"],
        "separator": ";",
        "encoding": "utf-8",
        "date_format": "%d/%m/%Y",
    },
    "societe_generale": {
        "date_cols": ["Date", "Date de l'opération", "date"],
        "label_cols": ["Libellé", "Détail de l'écriture", "libelle"],
        "amount_cols": ["Montant", "Débit", "montant"],
        "credit_col": "Crédit",
        "separator": ";",
        "encoding": "iso-8859-1",
        "date_format": "%d/%m/%Y",
    },
    "credit_agricole": {
        "date_cols": ["Date", "date"],
        "label_cols": ["Libellé", "libelle"],
        "amount_cols": ["Montant", "Débit euros"],
        "credit_col": "Crédit euros",
        "separator": ";",
        "encoding": "iso-8859-1",
        "date_format": "%d/%m/%Y",
    },
    "bnp": {
        "date_cols": ["Date", "Date opération"],
        "label_cols": ["Libellé", "Objet"],
        "amount_cols": ["Montant", "Valeur"],
        "separator": ";",
        "encoding": "iso-8859-1",
        "date_format": "%d/%m/%Y",
    },
    "fortuneo": {
        "date_cols": ["Date opération", "Date"],
        "label_cols": ["Libellé", "libelle"],
        "amount_cols": ["Montant", "Débit"],
        "credit_col": "Crédit",
        "separator": ";",
        "encoding": "utf-8",
        "date_format": "%d/%m/%Y",
    },
    "revolut": {
        "date_cols": ["Started Date", "Completed Date", "Date started"],
        "label_cols": ["Description", "Reference"],
        "amount_cols": ["Amount", "Money out"],
        "credit_col": "Money in",
        "separator": ",",
        "encoding": "utf-8",
        "date_format": "%Y-%m-%d",
    },
    "lcl": {
        "date_cols": ["Date"],
        "label_cols": ["Libellé"],
        "amount_cols": ["Débit", "Montant"],
        "credit_col": "Crédit",
        "separator": ";",
        "encoding": "iso-8859-1",
        "date_format": "%d/%m/%Y",
    },
    "la_banque_postale": {
        "date_cols": ["Date"],
        "label_cols": ["Libellé"],
        "amount_cols": ["Montant"],
        "separator": ";",
        "encoding": "iso-8859-1",
        "date_format": "%d/%m/%Y",
    },
    "n26": {
        "date_cols": ["Date"],
        "label_cols": ["Payee", "Payment reference"],
        "amount_cols": ["Amount (EUR)"],
        "separator": ",",
        "encoding": "utf-8",
        "date_format": "%Y-%m-%d",
    },
    "trade_republic": {
        "date_cols": ["Date"],
        "label_cols": ["Note", "Type"],
        "amount_cols": ["Amount"],
        "separator": ",",
        "encoding": "utf-8",
        "date_format": "%Y-%m-%d",
    },
}


def parse_csv(file_content: bytes, bank_hint: str = None) -> dict:
    """
    Parse un CSV bancaire. Auto-détecte le format.
    Retourne: {transactions: [], bank_detected: str, nb_parsed: int, errors: []}
    """
    # Essayer plusieurs encodages
    text = None
    for encoding in ["utf-8", "iso-8859-1", "windows-1252", "utf-8-sig"]:
        try:
            text = file_content.decode(encoding)
            break
        except (UnicodeDecodeError, AttributeError):
            continue

    if not text:
        return {"error": "Impossible de décoder le fichier. Encodage non supporté.", "transactions": []}

    # Détecter le séparateur
    separator = _detect_separator(text)

    # Parser le CSV
    reader = csv.DictReader(io.StringIO(text), delimiter=separator)
    headers = reader.fieldnames or []

    if not headers:
        return {"error": "Fichier vide ou format non reconnu.", "transactions": []}

    # Détecter la banque
    bank = bank_hint or _detect_bank(headers)
    fmt = BANK_FORMATS.get(bank, {})
    date_format = fmt.get("date_format", "%d/%m/%Y")

    # Mapper les colonnes
    date_col = _find_column(headers, fmt.get("date_cols", ["Date", "date", "DATE"]))
    label_col = _find_column(headers, fmt.get("label_cols", ["Libellé", "libelle", "Description", "Label"]))
    amount_col = _find_column(headers, fmt.get("amount_cols", ["Montant", "montant", "Amount", "Débit"]))
    credit_col = _find_column(headers, [fmt.get("credit_col", "Crédit"), "Crédit", "Credit", "Money in"])

    if not date_col or not label_col:
        return {
            "error": f"Colonnes non détectées. Headers trouvés: {headers}",
            "transactions": [],
            "headers": headers,
        }

    # Parser les lignes
    transactions = []
    errors = []
    for i, row in enumerate(reader):
        try:
            # Date
            date_str = (row.get(date_col) or "").strip()
            if not date_str:
                continue
            tx_date = _parse_date(date_str, date_format)
            if not tx_date:
                errors.append(f"Ligne {i+2}: date invalide '{date_str}'")
                continue

            # Libellé
            label = (row.get(label_col) or "").strip()
            if not label:
                continue

            # Montant
            amount = _parse_amount(row.get(amount_col, ""))
            if credit_col and credit_col in row:
                credit = _parse_amount(row.get(credit_col, ""))
                if credit and credit > 0:
                    if amount is None or amount == 0:
                        amount = credit
                    elif amount < 0:
                        amount = credit  # Le crédit override le débit

            if amount is None:
                errors.append(f"Ligne {i+2}: montant invalide")
                continue

            transactions.append({
                "date": tx_date.isoformat(),
                "libelle": label,
                "montant": round(amount, 2),
                "source": "import_csv",
            })
        except Exception as e:
            errors.append(f"Ligne {i+2}: {str(e)}")

    return {
        "transactions": transactions,
        "nb_parsed": len(transactions),
        "bank_detected": bank,
        "headers": headers,
        "errors": errors[:10],
    }


def _detect_separator(text: str) -> str:
    """Détecte le séparateur CSV."""
    first_lines = text[:2000]
    semicolons = first_lines.count(";")
    commas = first_lines.count(",")
    tabs = first_lines.count("\t")
    if tabs > semicolons and tabs > commas:
        return "\t"
    if semicolons > commas:
        return ";"
    return ","


def _detect_bank(headers: list) -> str:
    """Détecte la banque à partir des headers."""
    headers_lower = [h.lower() for h in headers]
    headers_str = " ".join(headers_lower)

    for bank, fmt in BANK_FORMATS.items():
        for col_list in [fmt.get("date_cols", []), fmt.get("label_cols", []), fmt.get("amount_cols", [])]:
            for col in col_list:
                if col.lower() in headers_lower or col.lower() in headers_str:
                    return bank

    # Heuristiques
    if "started date" in headers_str or "money out" in headers_str:
        return "revolut"
    if "amount (eur)" in headers_str:
        return "n26"
    if "dateop" in headers_str:
        return "boursorama"

    return "generic"


def _find_column(headers: list, candidates: list) -> Optional[str]:
    """Trouve la colonne correspondante parmi les candidats."""
    headers_lower = {h.lower().strip(): h for h in headers}
    for candidate in candidates:
        if candidate in headers:
            return candidate
        if candidate.lower() in headers_lower:
            return headers_lower[candidate.lower()]
    return None


def _parse_date(s: str, fmt: str = "%d/%m/%Y") -> Optional[date]:
    """Parse une date avec plusieurs formats."""
    for f in [fmt, "%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%d.%m.%Y", "%Y/%m/%d"]:
        try:
            return datetime.strptime(s.strip(), f).date()
        except ValueError:
            continue
    # Essai ISO
    try:
        return date.fromisoformat(s.strip()[:10])
    except ValueError:
        return None


def _parse_amount(s: str) -> Optional[float]:
    """Parse un montant (gère les formats FR et EN)."""
    if not s or not s.strip():
        return None
    s = s.strip().replace(" ", "").replace("\xa0", "")
    # Format FR: 1.234,56 ou -1234,56
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".")
    elif "," in s:
        s = s.replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None
