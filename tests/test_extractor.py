"""Tests for analysis/extractor.py -- NLP field extraction from OCR text."""
from analysis.extractor import extract_fields


def test_extracts_owner_name():
    text = "TITLE DEED\nOwner: Rajesh Kumar Sharma\nSurvey No: 118/2\nArea: 1200 sq ft"
    fields = extract_fields(text)
    assert fields["owner_names"] == ["Rajesh Kumar Sharma"]


def test_extracts_owner_name_with_honorific():
    text = "Owner Name: Mr. Anil Kapadia\nSurvey No: 204/A"
    fields = extract_fields(text)
    assert fields["owner_names"] == ["Anil Kapadia"]


def test_extracts_seller_as_owner_and_buyer_as_other_party():
    text = "AGREEMENT FOR SALE\nSeller: Rajesh Kumar Sharma\nBuyer: Amit Verma\nSurvey No: 118/2"
    fields = extract_fields(text)
    assert fields["owner_names"] == ["Rajesh Kumar Sharma"]
    assert fields["other_parties"] == ["Amit Verma"]


def test_extracts_survey_number():
    text = "Survey No: 118/2\nArea: 1200 sq ft"
    fields = extract_fields(text)
    assert "118/2" in fields["survey_numbers"]


def test_extracts_area_in_sqft():
    text = "Area: 1200 sq ft"
    fields = extract_fields(text)
    assert fields["areas_sq_ft"] == [1200.0]


def test_extracts_area_in_sqm_and_converts_to_sqft():
    text = "Area: 100 sq m"
    fields = extract_fields(text)
    assert len(fields["areas_sq_ft"]) == 1
    assert fields["areas_sq_ft"][0] == round(100 * 10.7639, 2)


def test_extracts_numeric_date():
    text = "Date: 12/03/2019"
    fields = extract_fields(text)
    assert "2019-03-12" in fields["dates"]


def test_extracts_textual_date():
    text = "Date: 20 August 2024"
    fields = extract_fields(text)
    assert "2024-08-20" in fields["dates"]


def test_extracts_pincode():
    text = "Dharampeth, Nagpur PIN 440010"
    fields = extract_fields(text)
    assert "440010" in fields["pincodes"]


def test_extracts_amount():
    text = "Consideration Rs. 5,500,000"
    fields = extract_fields(text)
    assert "5500000" in fields["amounts"]


def test_empty_text_returns_empty_fields():
    fields = extract_fields("")
    assert fields["owner_names"] == []
    assert fields["survey_numbers"] == []
    assert fields["areas_sq_ft"] == []
    assert fields["dates"] == []


def test_none_text_does_not_raise():
    fields = extract_fields(None)
    assert fields["owner_names"] == []


def test_invalid_date_is_ignored():
    # 32nd of a month doesn't exist -- extractor should skip it, not crash.
    text = "Date: 32/13/2019"
    fields = extract_fields(text)
    assert fields["dates"] == []
