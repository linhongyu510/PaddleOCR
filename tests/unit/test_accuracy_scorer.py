"""Tests for the accuracy benchmark scorer.

The scorer is measurement code: if it is wrong, every number it reports is wrong.
It initially charged a ~0.6 character error rate to output that was perfectly
correct but returned in a different detection order, so ordering is pinned here.
"""

import importlib.util
from pathlib import Path

import pytest

MODULE_PATH = Path(__file__).parents[2] / "benchmarks" / "run_accuracy_benchmark.py"

spec = importlib.util.spec_from_file_location("run_accuracy_benchmark", MODULE_PATH)
assert spec and spec.loader
benchmark = importlib.util.module_from_spec(spec)
spec.loader.exec_module(benchmark)

score = benchmark.score
normalize = benchmark.normalize
levenshtein = benchmark.levenshtein


def test_perfect_recognition_scores_perfectly() -> None:
    expected = ["Hallo Wereld", "Nederlandse test"]
    result = score(expected, list(expected))
    assert result["exact"] == 1.0
    assert result["cer"] == 0.0


def test_detection_order_does_not_affect_the_score() -> None:
    """Regression: reversed output previously reported cer≈0.65 at exact=1.00."""
    expected = [
        "Hallo Wereld",
        "Nederlandse test",
        "OCR herkenning",
        "Meertalige ondersteuning",
        "Tekstextractie uit afbeelding",
    ]
    result = score(expected, list(reversed(expected)))
    assert result["exact"] == 1.0
    assert result["cer"] == 0.0


def test_greek_reordering_regression() -> None:
    expected = ["Γεια σας Κόσμε", "Ελληνικό τεστ", "OCR αναγνώριση"]
    recognised = ["OCR αναγνώριση", "Ελληνικό τεστ", "Γεια σας Κόσμε"]
    result = score(expected, recognised)
    assert result["exact"] == 1.0
    assert result["cer"] == 0.0


def test_single_confusable_character_is_a_small_error_not_a_total_miss() -> None:
    """The real Russian case: Cyrillic С substituted for Latin C in "OCR"."""
    expected = ["Привет", "OCR распознавание"]
    recognised = ["Привет", "OСR распознавание"]
    result = score(expected, recognised)
    assert result["exact"] == 0.5
    assert 0 < result["cer"] < 0.1


def test_missing_lines_are_penalised() -> None:
    result = score(["one", "two", "three"], ["one"])
    assert result["exact"] == pytest.approx(1 / 3, abs=1e-4)
    assert result["cer"] > 0.5
    assert result["recognised_lines"] == 1


def test_spurious_extra_output_is_penalised() -> None:
    clean = score(["one"], ["one"])
    noisy = score(["one"], ["one", "unexpected garbage"])
    assert clean["cer"] == 0.0
    assert noisy["cer"] > clean["cer"], "extra output must not be free"


def test_empty_recognition_is_a_total_miss() -> None:
    result = score(["something"], [])
    assert result["exact"] == 0.0
    assert result["cer"] == 1.0


def test_cer_is_capped_at_one() -> None:
    result = score(["ab"], ["completely different and much longer text"])
    assert result["cer"] <= 1.0


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("  Hello   World  ", "hello world"),
        ("HELLO world", "hello world"),
        ("Ελληνικό  τεστ", "ελληνικό τεστ"),
    ],
)
def test_normalisation_folds_case_and_whitespace(raw: str, expected: str) -> None:
    assert normalize(raw) == expected


def test_normalisation_preserves_accents_and_script() -> None:
    """Stripping accents would flatter Latin scripts and hide real errors."""
    assert normalize("Café") != normalize("Cafe")
    assert normalize("Привет") == "привет"


@pytest.mark.parametrize(
    ("a", "b", "distance"),
    [("", "", 0), ("abc", "abc", 0), ("abc", "", 3), ("", "abc", 3), ("kitten", "sitting", 3)],
)
def test_levenshtein(a: str, b: str, distance: int) -> None:
    assert levenshtein(a, b) == distance
