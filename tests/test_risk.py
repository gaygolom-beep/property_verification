"""
Tests for analysis/risk.py -- the rule-based risk scoring engine.

The parametrized test at the bottom runs every scenario in
scripts/demo_data.py (the same ones used by scripts/seed_demo.py) through
the real engine and checks it lands on the intended risk level. This is the
project's "model evaluation" in the absence of real labeled fraud data --
a known-answer test set with a documented expected outcome for each case.
"""
from datetime import date

import pytest

from analysis.extractor import extract_fields
from analysis.risk import compute_risk, level_for
from scripts.demo_data import SCENARIOS

TODAY = date(2026, 9, 28)


def _run_scenario(sc):
    docs = []
    for doc_type, text in sc["docs"]:
        docs.append({
            "doc_type": doc_type, "filename": f"{doc_type}.png",
            "ocr_status": "Completed", "text": text, "fields": extract_fields(text),
        })
    prop = {
        "survey_number": sc["survey_number"],
        "area_sq_ft": sc["area_sq_ft"],
        "pincode": sc["pincode"],
    }
    return compute_risk(prop, docs, today=TODAY)


# ---------------------------------------------------------------------- #
# Known-answer suite: every seeded demo scenario must score at its
# documented expected risk level. If this fails, either the engine's
# weighting changed or a scenario's document text was edited without
# re-validating it -- both are worth catching before a demo.
# ---------------------------------------------------------------------- #

@pytest.mark.parametrize("sc", SCENARIOS, ids=[sc["title"] for sc in SCENARIOS])
def test_scenario_matches_expected_risk_level(sc):
    result = _run_scenario(sc)
    assert result["level"] == sc["expect"], (
        f"{sc['title']}: expected {sc['expect']}, got {result['level']} "
        f"(score {result['score']}). Findings: "
        f"{[f['title'] for f in result['findings'] if f['points'] > 0]}"
    )


def test_all_scenarios_cover_all_three_risk_levels():
    # Sanity check on the test data itself: the demo set should actually
    # exercise Low, Medium, and High, not just one band.
    levels = {sc["expect"] for sc in SCENARIOS}
    assert levels == {"Low", "Medium", "High"}


# ---------------------------------------------------------------------- #
# Targeted unit tests for individual checks, independent of the demo data
# ---------------------------------------------------------------------- #

def test_level_for_boundaries():
    assert level_for(0) == "Low"
    assert level_for(24) == "Low"
    assert level_for(25) == "Medium"
    assert level_for(54) == "Medium"
    assert level_for(55) == "High"
    assert level_for(100) == "High"


def test_clean_property_scores_zero_with_all_checks_passing():
    docs = [
        {"doc_type": "Title Deed", "filename": "a.png", "ocr_status": "Completed",
         "text": "Owner: Test Owner\nSurvey No: 1\nArea: 1000 sq ft\nDate: 01/01/2020",
         "fields": extract_fields("Owner: Test Owner\nSurvey No: 1\nArea: 1000 sq ft\nDate: 01/01/2020")},
        {"doc_type": "Tax Receipt", "filename": "b.png", "ocr_status": "Completed",
         "text": "Owner Name: Test Owner\nSurvey No: 1\nArea 1000 sq ft\nDate: 01/04/2024",
         "fields": extract_fields("Owner Name: Test Owner\nSurvey No: 1\nArea 1000 sq ft\nDate: 01/04/2024")},
    ]
    prop = {"survey_number": "1", "area_sq_ft": 1000, "pincode": None}
    result = compute_risk(prop, docs, today=TODAY)
    assert result["score"] == 0
    assert result["level"] == "Low"
    assert result["checks_passed"] == result["checks_run"]


def test_missing_required_documents_raises_risk():
    result = compute_risk({"survey_number": None, "area_sq_ft": None, "pincode": None}, [], today=TODAY)
    assert result["score"] > 0
    titles = [f["title"] for f in result["findings"]]
    assert "Title Deed missing" in titles
    assert "Tax Receipt missing" in titles


def test_unreadable_document_is_flagged():
    docs = [{"doc_type": "Title Deed", "filename": "blurry.png", "ocr_status": "Failed", "text": "", "fields": extract_fields("")}]
    result = compute_risk({"survey_number": None, "area_sq_ft": None, "pincode": None}, docs, today=TODAY)
    titles = [f["title"] for f in result["findings"]]
    assert any("unreadable" in t for t in titles)


def test_future_date_is_flagged():
    text = "Owner: Test Owner\nDate: 01/01/2099"
    docs = [{"doc_type": "Title Deed", "filename": "a.png", "ocr_status": "Completed", "text": text, "fields": extract_fields(text)}]
    result = compute_risk({"survey_number": None, "area_sq_ft": None, "pincode": None}, docs, today=TODAY)
    assert result["features"]["future_dates"] == 1


def test_duplicate_property_claim_is_heavily_penalized():
    docs = [{"doc_type": "Title Deed", "filename": "a.png", "ocr_status": "Completed",
             "text": "Owner: Test Owner\nSurvey No: 1", "fields": extract_fields("Owner: Test Owner\nSurvey No: 1")}]
    prop = {"survey_number": "1", "area_sq_ft": None, "pincode": None}
    without = compute_risk(prop, docs, duplicate_property=False, today=TODAY)
    with_dup = compute_risk(prop, docs, duplicate_property=True, today=TODAY)
    assert with_dup["score"] > without["score"]
    assert with_dup["score"] - without["score"] == 30


def test_score_never_exceeds_100():
    # Stack every possible penalty at once and confirm the score still caps.
    docs = [
        {"doc_type": "Sale Agreement", "filename": "a.png", "ocr_status": "Failed", "text": "", "fields": extract_fields("")},
    ]
    result = compute_risk({"survey_number": "X", "area_sq_ft": 1, "pincode": "000000"}, docs, duplicate_property=True, today=TODAY)
    assert result["score"] <= 100
