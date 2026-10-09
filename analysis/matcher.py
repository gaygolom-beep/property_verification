"""
Cross-document matching (Module 8, part 2).

Compares extracted fields across a property's documents and against the
property record itself. Uses fuzzy string similarity (difflib) for names so
"Om Gaygol" and "Gaygol Om" or "Priya D. Deshmukh" and "Priya Deshmukh" are
treated as near-matches instead of hard mismatches.
"""
import re
from difflib import SequenceMatcher

_HONORIFICS = {"mr", "mrs", "ms", "shri", "smt", "sri", "dr"}


def normalize_name(name):
    tokens = re.findall(r"[a-z]+", (name or "").lower())
    tokens = [t for t in tokens if t not in _HONORIFICS and len(t) > 1]  # drop initials
    return " ".join(sorted(tokens))


def name_similarity(a, b):
    na, nb = normalize_name(a), normalize_name(b)
    if not na or not nb:
        return 0.0
    ratio = SequenceMatcher(None, na, nb).ratio()
    # "Priya Deshmukh" vs "Priya D. Deshmukh": subset of tokens is a soft match
    ta, tb = set(na.split()), set(nb.split())
    if ta and tb and (ta <= tb or tb <= ta):
        ratio = max(ratio, 0.9)
    return round(ratio, 3)


def normalize_survey(value):
    return re.sub(r"[^a-z0-9]", "", (value or "").lower())


def percent_diff(a, b):
    if not a or not b:
        return None
    return abs(a - b) / max(a, b) * 100.0
