"""Canonical PaddleOCR language aliases."""

from dataclasses import dataclass

from polyocr.api.errors import ServiceError


@dataclass(frozen=True)
class Language:
    code: str
    paddle_code: str
    name: str
    aliases: tuple[str, ...]


_LANGUAGES = (
    Language("zh", "ch", "中文", ("zh", "ch", "zh-cn", "中文", "简体中文")),
    Language("zh-Hant", "chinese_cht", "繁體中文", ("zh-hant", "zh-tw", "繁体中文")),
    Language("en", "en", "English", ("en", "english", "英文", "英语")),
    Language("ja", "japan", "日本語", ("ja", "jp", "japan", "japanese", "日文", "日语")),
    Language("ko", "korean", "한국어", ("ko", "kr", "korean", "韩文", "韩语")),
    Language("fr", "latin", "Français", ("fr", "french", "法文", "法语")),
    Language("de", "latin", "Deutsch", ("de", "german", "德文", "德语")),
    Language("es", "latin", "Español", ("es", "spanish", "西班牙文", "西班牙语")),
    Language("pt", "latin", "Português", ("pt", "portuguese", "葡萄牙文", "葡萄牙语")),
    Language("ru", "cyrillic", "Русский", ("ru", "russian", "俄文", "俄语")),
    Language("th", "th", "ไทย", ("th", "thai", "泰文", "泰语")),
    Language("latin", "latin", "Latin", ("latin", "la", "拉丁语")),
)

_BY_ALIAS = {
    alias.casefold(): language for language in _LANGUAGES for alias in language.aliases
}


def resolve_language(value: str) -> Language:
    language = _BY_ALIAS.get(value.strip().casefold())
    if language is None:
        raise ServiceError(
            "unsupported_language",
            f"Unsupported OCR language: {value!r}.",
            422,
        )
    return language


def normalize_language(value: str) -> str:
    return resolve_language(value).paddle_code


def supported_languages() -> tuple[Language, ...]:
    return _LANGUAGES
