"""
Risk scoring engine (Modules 9 + 10).

A transparent, weighted anomaly-scoring model. Each check contributes points
to a 0-100 risk score when it finds an inconsistency; every point added is
tied to a human-readable finding so the score is fully explainable (an
explicit requirement of the project: AI assists, a human decides).

The engine also emits a numeric feature vector (result["features"]). That
vector is the input a trained classifier (e.g. scikit-learn IsolationForest
or RandomForest) would consume once labelled fraud data exists, so the
scoring layer can be swapped for a learned model without touching the rest
of the application.

This module is pure Python (no Flask/DB imports) so it can be unit tested.
"""
from datetime import date
from hashlib import sha1

from .matcher import name_similarity, normalize_survey, percent_diff

REQUIRED_DOC_TYPES = ["Title Deed", "Tax Receipt"]

LEVELS = [(55, "High"), (25, "Medium"), (0, "Low")]


def level_for(score):
    for threshold, label in LEVELS:
        if score >= threshold:
            return label
    return "Low"


def _finding(severity, title, detail, points=0):
    return {"severity": severity, "title": title, "detail": detail, "points": points}


def _explain(finding):
    """
    A plain-language description of the check's logic/threshold behind a
    finding, matched by keyword rather than threaded through every call
    site -- used for the hover tooltips on the property page and the
    Model Evaluation page, so the "why" behind a flag is always one hover
    away instead of hidden in source code.
    """
    title = finding["title"].lower()
    if "missing" in title:
        return "Required-document check: Title Deed and Tax Receipt must both be present to cross-check ownership and tax records."
    if "unreadable" in title:
        return "OCR readability check: a document with under ~15 characters of extracted text, or a failed OCR run, can't be analyzed and is flagged."
    if title.startswith("owner name"):
        return "Fuzzy name matching: similarity \u2265 85% passes, 60\u201385% is flagged as a possible spelling variation, below 60% is flagged as likely different people."
    if "survey number" in title:
        return "Survey/plot number is normalized (lowercased, punctuation stripped) and compared across the property record and every document; any disagreement is flagged."
    if title.startswith("area"):
        return "Area is compared pairwise as a percentage difference: \u2264 5% passes, 5\u201315% is a minor flag, over 15% is a major flag."
    if "pin code" in title:
        return "The property's declared PIN code is checked for appearing somewhere in the uploaded documents' OCR text."
    if "future date" in title:
        return "Dates extracted from documents are checked against today's date; any date in the future is flagged."
    if "predates" in title or "logical order" in title:
        return "Document dates are checked against each other -- e.g. a sale agreement should not be dated earlier than the title deed."
    if "identical content" in title:
        return "Each document's OCR text is hashed; two different document types sharing an identical hash suggests the same file was uploaded twice under different labels."
    if "same survey number" in title:
        return "Checks whether another account has already submitted a property with the same survey number in the same city -- a common sign of a duplicate or fraudulent claim."
    return None


def compute_risk(prop, docs, duplicate_property=False, today=None):
    """
    prop: dict(survey_number, area_sq_ft, pincode)
    docs: list of dict(doc_type, filename, ocr_status, text, fields)
    Returns dict(score, level, findings, features, checks_run, checks_passed).
    """
    today = today or date.today()
    findings = []
    checks_run = 0
    checks_passed = 0
    features = {
        "n_docs": len(docs), "n_unreadable": 0, "missing_required": 0,
        "name_min_similarity": 1.0, "survey_mismatch": 0, "area_diff_pct": 0.0,
        "future_dates": 0, "duplicate_content": 0, "duplicate_property": 0,
        "date_order_violation": 0, "pincode_mismatch": 0,
    }

    def passed(title, detail):
        nonlocal checks_run, checks_passed
        checks_run += 1
        checks_passed += 1
        findings.append(_finding("pass", title, detail, 0))

    def failed(severity, title, detail, points):
        nonlocal checks_run
        checks_run += 1
        findings.append(_finding(severity, title, detail, points))

    # 1. Required documents ------------------------------------------------
    present_types = {d["doc_type"] for d in docs}
    for req in REQUIRED_DOC_TYPES:
        if req in present_types:
            passed(f"{req} present", f"A {req} has been uploaded.")
        else:
            features["missing_required"] += 1
            failed("high", f"{req} missing", f"No {req} was uploaded, so ownership/tax details cannot be cross-checked.", 15)

    # 2. Readability of documents -----------------------------------------
    readable = []
    for d in docs:
        if d["ocr_status"] != "Completed" or len((d["text"] or "").strip()) < 15:
            features["n_unreadable"] += 1
            failed("medium", f"{d['doc_type']} unreadable",
                   f"No usable text could be extracted from '{d['filename']}'. Check the scan quality or edit the extracted text.", 8)
        else:
            readable.append(d)

    # 3. Owner name consistency -------------------------------------------
    named = [(d, d["fields"]["owner_names"][0]) for d in readable if d["fields"]["owner_names"]]
    if len(named) >= 2:
        worst, pair = 1.0, None
        for i in range(len(named)):
            for j in range(i + 1, len(named)):
                sim = name_similarity(named[i][1], named[j][1])
                if sim < worst:
                    worst, pair = sim, (named[i], named[j])
        features["name_min_similarity"] = worst
        desc = ""
        if pair:
            desc = f"'{pair[0][1]}' ({pair[0][0]['doc_type']}) vs '{pair[1][1]}' ({pair[1][0]['doc_type']}), similarity {worst:.0%}."
        if worst >= 0.85:
            passed("Owner names consistent", f"Owner name matches across {len(named)} documents.")
        elif worst >= 0.6:
            failed("medium", "Owner name partially differs", desc + " Possible spelling variation.", 10)
        else:
            failed("high", "Owner name mismatch", desc + " Documents name different owners.", 25)
    else:
        findings.append(_finding("info", "Owner name not compared", "Fewer than two documents contained a readable owner name.", 0))

    # 4. Survey number consistency ----------------------------------------
    survey_values = []
    if prop.get("survey_number"):
        survey_values.append(("Property record", normalize_survey(prop["survey_number"]), prop["survey_number"]))
    for d in readable:
        if d["fields"]["survey_numbers"]:
            raw = d["fields"]["survey_numbers"][0]
            survey_values.append((d["doc_type"], normalize_survey(raw), raw))
    if len(survey_values) >= 2:
        if len({v[1] for v in survey_values}) == 1:
            passed("Survey number consistent", f"Survey number '{survey_values[0][2]}' matches everywhere it appears.")
        else:
            features["survey_mismatch"] = 1
            shown = "; ".join(f"{v[0]}: {v[2]}" for v in survey_values)
            failed("high", "Survey number mismatch", shown, 20)
    else:
        findings.append(_finding("info", "Survey number not compared", "Survey number found in fewer than two places.", 0))

    # 5. Area consistency --------------------------------------------------
    area_values = []
    if prop.get("area_sq_ft"):
        area_values.append(("Property record", float(prop["area_sq_ft"])))
    for d in readable:
        if d["fields"]["areas_sq_ft"]:
            area_values.append((d["doc_type"], d["fields"]["areas_sq_ft"][0]))
    if len(area_values) >= 2:
        biggest = max(percent_diff(area_values[i][1], area_values[j][1]) or 0
                      for i in range(len(area_values)) for j in range(i + 1, len(area_values)))
        features["area_diff_pct"] = round(biggest, 1)
        shown = "; ".join(f"{a[0]}: {a[1]:g} sq ft" for a in area_values)
        if biggest <= 5:
            passed("Area consistent", shown)
        elif biggest <= 15:
            failed("medium", "Area differs slightly", f"{shown} (max gap {biggest:.0f}%).", 10)
        else:
            failed("high", "Area mismatch", f"{shown} (max gap {biggest:.0f}%).", 20)
    else:
        findings.append(_finding("info", "Area not compared", "Area found in fewer than two places.", 0))

    # 6. PIN code ----------------------------------------------------------
    if prop.get("pincode"):
        doc_pins = {p for d in readable for p in d["fields"]["pincodes"]}
        if doc_pins:
            if prop["pincode"] in doc_pins:
                passed("PIN code matches", f"PIN {prop['pincode']} appears in the documents.")
            else:
                features["pincode_mismatch"] = 1
                failed("medium", "PIN code mismatch", f"Property PIN {prop['pincode']} not found; documents mention {', '.join(sorted(doc_pins))}.", 8)

    # 7. Date sanity -------------------------------------------------------
    future = 0
    for d in readable:
        for iso in d["fields"]["dates"]:
            if date.fromisoformat(iso) > today:
                future += 1
                failed("high", f"Future date in {d['doc_type']}", f"Document contains the date {iso}, which is in the future.", 15)
                break
    features["future_dates"] = future

    def earliest(doc_type):
        found = [date.fromisoformat(x) for d in readable if d["doc_type"] == doc_type for x in d["fields"]["dates"]]
        return min(found) if found else None

    deed, agreement = earliest("Title Deed"), earliest("Sale Agreement")
    if deed and agreement:
        if agreement < deed:
            features["date_order_violation"] = 1
            failed("medium", "Sale agreement predates title deed", f"Sale agreement {agreement} is earlier than title deed {deed}.", 10)
        else:
            passed("Document dates in logical order", f"Title deed {deed} precedes sale agreement {agreement}.")

    # 8. Duplicate content -------------------------------------------------
    seen = {}
    for d in readable:
        digest = sha1(" ".join(d["text"].lower().split()).encode()).hexdigest()
        if digest in seen and seen[digest] != d["doc_type"]:
            features["duplicate_content"] += 1
            failed("medium", "Identical content in different documents",
                   f"{seen[digest]} and {d['doc_type']} contain the same text, which suggests one file was uploaded twice.", 10)
        seen[digest] = d["doc_type"]

    # 9. Duplicate property claim -----------------------------------------
    if duplicate_property:
        features["duplicate_property"] = 1
        failed("high", "Same survey number registered by another owner",
               "Another account has already submitted a property with this survey number in the same city.", 30)

    score = min(100, sum(f["points"] for f in findings))
    for f in findings:
        f["explain"] = _explain(f)
    order = {"high": 0, "medium": 1, "info": 2, "pass": 3}
    findings.sort(key=lambda f: order[f["severity"]])
    return {
        "score": score, "level": level_for(score), "findings": findings,
        "features": features, "checks_run": checks_run, "checks_passed": checks_passed,
    }
