"""Language-resolution contract tests.

These pin the bug that shipped in the first refactor: caller languages such as
``fr`` and ``ru`` were mapped to ``latin`` / ``cyrillic``, which are recognition
model prefixes rather than values ``PaddleOCR(lang=...)`` accepts. Every request
for those languages failed with a 503 at model-load time.
"""

import pytest

from polyocr.api.errors import ServiceError
from polyocr.services.languages import (
    normalize_language,
    resolve_language,
    supported_languages,
)

# Recognition-model prefixes. PaddleOCR derives these from a language code and
# rejects them when passed as `lang`, so they must never be a `paddle_code`.
MODEL_PREFIXES = frozenset({"latin", "cyrillic", "eslav", "arabic", "devanagari", "korean_latin"})

# Language codes PaddleOCR 3.x resolves to a real model, verified against
# paddleocr._utils.langs and PaddleOCR._get_ocr_model_names.
PADDLE_RESOLVABLE_CODES = frozenset(
    {
        "ch",
        "chinese_cht",
        "en",
        "japan",
        "korean",
        "th",
        "el",
        "ka",
        "ta",
        "te",
        "af",
        "az",
        "bs",
        "ca",
        "cs",
        "cy",
        "da",
        "de",
        "es",
        "et",
        "eu",
        "fi",
        "fr",
        "french",
        "ga",
        "german",
        "gl",
        "hr",
        "hu",
        "id",
        "is",
        "it",
        "ku",
        "la",
        "lb",
        "lt",
        "lv",
        "mi",
        "ms",
        "mt",
        "nl",
        "no",
        "oc",
        "pi",
        "pl",
        "pt",
        "qu",
        "rm",
        "ro",
        "rs_latin",
        "sk",
        "sl",
        "sq",
        "sv",
        "sw",
        "tl",
        "tr",
        "uz",
        "vi",
        "ru",
        "be",
        "uk",
        "bg",
        "kk",
        "ky",
        "mk",
        "mn",
        "rs_cyrillic",
        "tg",
        "tt",
        "abq",
        "ady",
        "ava",
        "ba",
        "bua",
        "che",
        "cv",
        "dar",
        "inh",
        "kaa",
        "kbd",
        "kv",
        "lbe",
        "lez",
        "mhr",
        "mo",
        "os",
        "sah",
        "tab",
        "tyv",
        "udm",
        "xal",
        "ar",
        "fa",
        "ps",
        "sd",
        "ug",
        "ur",
        "bal",
        "hi",
        "mr",
        "ne",
        "sa",
        "ang",
        "bgc",
        "bh",
        "bho",
        "gom",
        "mah",
        "mai",
        "new",
        "sck",
    }
)


def test_every_paddle_code_is_accepted_by_paddleocr() -> None:
    for language in supported_languages():
        assert language.paddle_code in PADDLE_RESOLVABLE_CODES, (
            f"{language.code}: paddle_code {language.paddle_code!r} is not a language "
            "code PaddleOCR can resolve to a model"
        )


def test_no_paddle_code_is_a_recognition_model_prefix() -> None:
    for language in supported_languages():
        assert language.paddle_code not in MODEL_PREFIXES, (
            f"{language.code}: {language.paddle_code!r} is a model prefix, not a valid lang value"
        )


@pytest.mark.parametrize(
    ("request_value", "expected_paddle_code"),
    [
        ("fr", "fr"),
        ("french", "fr"),
        ("法文", "fr"),
        ("de", "de"),
        ("german", "de"),
        ("es", "es"),
        ("pt", "pt"),
        ("it", "it"),
        ("nl", "nl"),
        ("ru", "ru"),
        ("russian", "ru"),
        ("be", "be"),
        ("uk", "uk"),
    ],
)
def test_regression_previously_broken_languages(
    request_value: str, expected_paddle_code: str
) -> None:
    """These returned 503 before: they resolved to `latin` / `cyrillic`."""
    assert normalize_language(request_value) == expected_paddle_code


@pytest.mark.parametrize(
    ("request_value", "expected_paddle_code"),
    [
        ("zh", "ch"),
        ("ZH", "ch"),
        ("  zh  ", "ch"),
        ("中文", "ch"),
        ("zh-Hant", "chinese_cht"),
        ("zh-TW", "chinese_cht"),
        ("en", "en"),
        ("ja", "japan"),
        ("japanese", "japan"),
        ("ko", "korean"),
        ("th", "th"),
        ("el", "el"),
        ("ar", "ar"),
        ("hi", "hi"),
        ("ta", "ta"),
        ("te", "te"),
        ("ka", "ka"),
        ("sr-Latn", "rs_latin"),
        ("sr-Cyrl", "rs_cyrillic"),
    ],
)
def test_alias_resolution(request_value: str, expected_paddle_code: str) -> None:
    assert normalize_language(request_value) == expected_paddle_code


@pytest.mark.parametrize("value", ["cyrillic", "eslav", "devanagari"])
def test_script_only_prefixes_are_rejected_as_input(value: str) -> None:
    """A caller passing a model prefix gets 422, not a 503 at model load."""
    with pytest.raises(ServiceError) as exc:
        normalize_language(value)
    assert exc.value.code == "unsupported_language"
    assert exc.value.status_code == 422


@pytest.mark.parametrize(
    ("value", "expected_paddle_code"),
    [("latin", "la"), ("arabic", "ar")],
)
def test_prefixes_that_name_a_real_language_map_to_that_language(
    value: str, expected_paddle_code: str
) -> None:
    """`latin` and `arabic` name real languages, so they stay accepted.

    What matters is that they resolve to a usable `lang` code rather than to the
    model prefix of the same name.
    """
    assert normalize_language(value) == expected_paddle_code
    assert normalize_language(value) not in MODEL_PREFIXES


@pytest.mark.parametrize("value", ["", "  ", "klingon", "xx-YY", "zz"])
def test_unknown_languages_are_rejected(value: str) -> None:
    with pytest.raises(ServiceError) as exc:
        normalize_language(value)
    assert exc.value.code == "unsupported_language"


def test_aliases_are_unique_across_languages() -> None:
    owners: dict[str, str] = {}
    for language in supported_languages():
        for alias in language.all_aliases:
            assert alias not in owners or owners[alias] == language.code, (
                f"alias {alias!r} is claimed by {owners[alias]} and {language.code}"
            )
            owners[alias] = language.code


def test_language_codes_are_unique() -> None:
    codes = [language.code for language in supported_languages()]
    assert len(codes) == len(set(codes))


def test_every_language_resolves_by_its_own_code_and_paddle_code() -> None:
    for language in supported_languages():
        assert resolve_language(language.code) is language
        assert resolve_language(language.paddle_code) is language


def test_catalogue_covers_the_documented_scripts() -> None:
    scripts = {language.script for language in supported_languages()}
    assert {
        "Han",
        "Japanese",
        "Hangul",
        "Latin",
        "Cyrillic",
        "Arabic",
        "Devanagari",
        "Thai",
        "Greek",
    } <= scripts
    assert len(supported_languages()) >= 70
