"""Tests for analysis/matcher.py -- fuzzy name matching and comparison helpers."""
from analysis.matcher import name_similarity, normalize_name, normalize_survey, percent_diff


def test_identical_names_match_fully():
    assert name_similarity("Priya Deshmukh", "Priya Deshmukh") == 1.0


def test_name_with_initial_is_treated_as_near_match():
    # "Priya D. Deshmukh" vs "Priya Deshmukh" -- the initial "D." should not
    # cause this to read as two different people.
    sim = name_similarity("Priya D. Deshmukh", "Priya Deshmukh")
    assert sim >= 0.85


def test_reordered_tokens_still_match():
    sim = name_similarity("Kumar Sharma Rajesh", "Rajesh Kumar Sharma")
    assert sim >= 0.85


def test_honorific_is_ignored():
    sim = name_similarity("Mr. Anil Kapadia", "Anil Kapadia")
    assert sim >= 0.85


def test_genuinely_different_names_score_low():
    sim = name_similarity("Sanjay Patil", "Mahesh Rane")
    assert sim < 0.5


def test_empty_name_scores_zero():
    assert name_similarity("", "Anil Kapadia") == 0.0
    assert name_similarity(None, "Anil Kapadia") == 0.0


def test_normalize_survey_strips_formatting():
    assert normalize_survey("118/2") == normalize_survey("118 / 2")
    assert normalize_survey("Survey No. 45") != normalize_survey("45")  # extra words aren't stripped here


def test_percent_diff_basic():
    assert round(percent_diff(100, 110), 2) == 9.09


def test_percent_diff_handles_none_or_zero():
    assert percent_diff(None, 100) is None
    assert percent_diff(100, None) is None
    assert percent_diff(0, 100) is None
