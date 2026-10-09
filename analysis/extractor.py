"""
NLP field extraction (Module 8, part 1).

Turns the raw OCR text of a document into structured fields using
pattern-based information extraction (regular expressions + light
normalisation). The fields are then compared across documents by matcher.py.

Extracted per document:
  owner_names    - names that appear after Owner/Seller/Vendor/Holder labels
  other_parties  - buyers / purchasers (kept separate so a sale agreement's
                   buyer is never compared against the owner on a title deed)
  survey_numbers - survey / plot / gat / khasra numbers
  areas_sq_ft    - built-up / plot areas, converted to sq. ft.
  dates          - ISO dates (dd/mm/yyyy, dd-mm-yyyy, "12 March 2019")
  pincodes       - 6 digit Indian PIN codes
  amounts        - rupee amounts
"""
import re
from datetime import datetime

MONTHS = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}

SQM_TO_SQFT = 10.7639

_TITLE = r"(?i:(?:mr|mrs|ms|shri|smt|sri|dr)\.?\s*)?"
_NAME = r"([A-Z][A-Za-z\.]+(?:[ \t]+[A-Z][A-Za-z\.]+){0,3})"

OWNER_RE = re.compile(
    r"(?i:owner|seller|vendor|transferor|holder|assessee|registered\s+owner)"
    r"(?i:\s*name)?[ \t]*[:\-][ \t]*" + _TITLE + _NAME
)
PARTY_RE = re.compile(
    r"(?i:buyer|purchaser|transferee|vendee)(?i:\s*name)?[ \t]*[:\-][ \t]*" + _TITLE + _NAME
)
SURVEY_RE = re.compile(
    r"(?i:survey|plot|gat|khasra)[ \t]*(?i:no\.?|number|#)?[ \t]*[:\-]?[ \t]*(\d+[A-Za-z0-9/\-]*)"
)
AREA_RE = re.compile(
    r"(\d[\d,]*\.?\d*)[ \t]*(?i:(sq\.?[ \t]*ft|sqft|square[ \t]*feet|sq\.?[ \t]*m(?:tr|eters?)?|sqm|square[ \t]*met(?:er|re)s?))"
)
DATE_NUM_RE = re.compile(r"\b(\d{1,2})[/\-.](\d{1,2})[/\-.](\d{4})\b")
DATE_TXT_RE = re.compile(
    r"\b(\d{1,2})(?:st|nd|rd|th)?[ \t]+(?:of[ \t]+)?"
    r"(Jan[a-z]*|Feb[a-z]*|Mar[a-z]*|Apr[a-z]*|May|Jun[a-z]*|Jul[a-z]*|Aug[a-z]*|Sep[a-z]*|Oct[a-z]*|Nov[a-z]*|Dec[a-z]*)"
    r"[ \t,]+(\d{4})\b", re.IGNORECASE
)
PIN_RE = re.compile(r"\b([1-9]\d{5})\b")
AMOUNT_RE = re.compile(r"(?i:rs\.?|inr|₹)[ \t]*([\d,]+(?:\.\d+)?)")

# Words that signal the name has ended when two labelled fields share a line.
_STOP_WORDS = {
    "survey", "plot", "gat", "khasra", "address", "date", "dated", "area", "no",
    "son", "daughter", "wife", "resident", "aged", "age", "pin", "pincode",
    "village", "city", "district", "registration", "amount", "buyer", "seller",
}


def _clean_name(raw):
    tokens = []
    for tok in raw.split():
        if tok.lower().strip(".") in _STOP_WORDS:
            break
        tokens.append(tok)
    return " ".join(tokens).strip(" .")


def _safe_date(day, month, year):
    try:
        return datetime(int(year), int(month), int(day)).date().isoformat()
    except ValueError:
        return None


def extract_fields(text):
    text = text or ""
    fields = {
        "owner_names": [], "other_parties": [], "survey_numbers": [],
        "areas_sq_ft": [], "dates": [], "pincodes": [], "amounts": [],
    }

    for m in OWNER_RE.finditer(text):
        name = _clean_name(m.group(1))
        if len(name) > 2:
            fields["owner_names"].append(name)
    for m in PARTY_RE.finditer(text):
        name = _clean_name(m.group(1))
        if len(name) > 2:
            fields["other_parties"].append(name)

    fields["survey_numbers"] = [m.group(1) for m in SURVEY_RE.finditer(text)]

    for m in AREA_RE.finditer(text):
        try:
            value = float(m.group(1).replace(",", ""))
        except ValueError:
            continue
        unit = m.group(2).lower().replace(" ", "").replace(".", "")
        if unit.startswith("sqm") or unit.startswith("squaremet") or unit.startswith("sqmtr") or unit.startswith("sqmeter"):
            value *= SQM_TO_SQFT
        fields["areas_sq_ft"].append(round(value, 2))

    for m in DATE_NUM_RE.finditer(text):
        iso = _safe_date(m.group(1), m.group(2), m.group(3))
        if iso:
            fields["dates"].append(iso)
    for m in DATE_TXT_RE.finditer(text):
        iso = _safe_date(m.group(1), MONTHS[m.group(2)[:3].lower()], m.group(3))
        if iso:
            fields["dates"].append(iso)

    fields["pincodes"] = sorted(set(PIN_RE.findall(text)))
    fields["amounts"] = [m.group(1).replace(",", "") for m in AMOUNT_RE.finditer(text)]
    return fields
