"""Canonical PaddleOCR language codes and caller-facing aliases.

``PaddleOCR(lang=...)`` accepts a *language* code such as ``fr`` or ``ru``. It does
not accept a recognition-model prefix such as ``latin`` or ``cyrillic``: those are
derived internally from the language code, and passing them raises
``ValueError: No models are available for lang=...``.

Every ``paddle_code`` below is therefore a language code that PaddleOCR 3.x can
resolve to a real detection/recognition model pair. ``tests/unit/test_languages.py``
pins that contract, and the optional integration test re-checks it against the
installed PaddleOCR build.
"""

from dataclasses import dataclass, field

from polyocr.api.errors import ServiceError


@dataclass(frozen=True)
class Language:
    """A caller-facing language exposed by ``GET /v1/languages``."""

    code: str
    paddle_code: str
    name: str
    script: str
    aliases: tuple[str, ...] = field(default_factory=tuple)

    @property
    def all_aliases(self) -> tuple[str, ...]:
        """Aliases accepted for this language, always including its own codes."""
        ordered = (self.code, self.paddle_code, *self.aliases)
        seen: dict[str, None] = {}
        for alias in ordered:
            seen.setdefault(alias.casefold(), None)
        return tuple(seen)


# Ordered by script, then by language name. ``paddle_code`` values are verified
# against PaddleOCR's own language tables; see the module docstring.
_LANGUAGES: tuple[Language, ...] = (
    # --- Chinese / Japanese / Korean -------------------------------------
    Language("zh", "ch", "简体中文", "Han", ("chinese", "zh-cn", "zh-hans", "中文", "简体中文")),
    Language("zh-Hant", "chinese_cht", "繁體中文", "Han", ("zh-tw", "zh-hk", "cht", "繁体中文")),
    Language("ja", "japan", "日本語", "Japanese", ("jp", "japanese", "日文", "日语")),
    Language("ko", "korean", "한국어", "Hangul", ("kr", "korean", "韩文", "韩语")),
    # --- Latin script ----------------------------------------------------
    Language("en", "en", "English", "Latin", ("english", "英文", "英语")),
    Language("af", "af", "Afrikaans", "Latin", ("afrikaans",)),
    Language("az", "az", "Azərbaycan", "Latin", ("azerbaijani",)),
    Language("bs", "bs", "Bosanski", "Latin", ("bosnian",)),
    Language("ca", "ca", "Català", "Latin", ("catalan",)),
    Language("cs", "cs", "Čeština", "Latin", ("czech",)),
    Language("cy", "cy", "Cymraeg", "Latin", ("welsh",)),
    Language("da", "da", "Dansk", "Latin", ("danish",)),
    Language("de", "de", "Deutsch", "Latin", ("german", "德文", "德语")),
    Language("es", "es", "Español", "Latin", ("spanish", "西班牙文", "西班牙语")),
    Language("et", "et", "Eesti", "Latin", ("estonian",)),
    Language("eu", "eu", "Euskara", "Latin", ("basque",)),
    Language("fi", "fi", "Suomi", "Latin", ("finnish",)),
    Language("fr", "fr", "Français", "Latin", ("french", "法文", "法语")),
    Language("ga", "ga", "Gaeilge", "Latin", ("irish",)),
    Language("gl", "gl", "Galego", "Latin", ("galician",)),
    Language("hr", "hr", "Hrvatski", "Latin", ("croatian",)),
    Language("hu", "hu", "Magyar", "Latin", ("hungarian",)),
    Language("id", "id", "Bahasa Indonesia", "Latin", ("indonesian",)),
    Language("is", "is", "Íslenska", "Latin", ("icelandic",)),
    Language("it", "it", "Italiano", "Latin", ("italian", "意大利文", "意大利语")),
    Language("ku", "ku", "Kurdî", "Latin", ("kurdish",)),
    Language("la", "la", "Latina", "Latin", ("latin", "拉丁文", "拉丁语")),
    Language("lb", "lb", "Lëtzebuergesch", "Latin", ("luxembourgish",)),
    Language("lt", "lt", "Lietuvių", "Latin", ("lithuanian",)),
    Language("lv", "lv", "Latviešu", "Latin", ("latvian",)),
    Language("mi", "mi", "Te Reo Māori", "Latin", ("maori",)),
    Language("ms", "ms", "Bahasa Melayu", "Latin", ("malay",)),
    Language("mt", "mt", "Malti", "Latin", ("maltese",)),
    Language("nl", "nl", "Nederlands", "Latin", ("dutch", "荷兰文", "荷兰语")),
    Language("no", "no", "Norsk", "Latin", ("norwegian",)),
    Language("oc", "oc", "Occitan", "Latin", ("occitan",)),
    Language("pi", "pi", "Pāli", "Latin", ("pali",)),
    Language("pl", "pl", "Polski", "Latin", ("polish",)),
    Language("pt", "pt", "Português", "Latin", ("portuguese", "葡萄牙文", "葡萄牙语")),
    Language("qu", "qu", "Runasimi", "Latin", ("quechua",)),
    Language("rm", "rm", "Rumantsch", "Latin", ("romansh",)),
    Language("ro", "ro", "Română", "Latin", ("romanian",)),
    Language("sk", "sk", "Slovenčina", "Latin", ("slovak",)),
    Language("sl", "sl", "Slovenščina", "Latin", ("slovenian",)),
    Language("sq", "sq", "Shqip", "Latin", ("albanian",)),
    Language("sr-Latn", "rs_latin", "Srpski (latinica)", "Latin", ("serbian-latin",)),
    Language("sv", "sv", "Svenska", "Latin", ("swedish",)),
    Language("sw", "sw", "Kiswahili", "Latin", ("swahili",)),
    Language("tl", "tl", "Tagalog", "Latin", ("tagalog", "filipino")),
    Language("tr", "tr", "Türkçe", "Latin", ("turkish",)),
    Language("uz", "uz", "O'zbek", "Latin", ("uzbek",)),
    Language("vi", "vi", "Tiếng Việt", "Latin", ("vietnamese",)),
    # --- Cyrillic script -------------------------------------------------
    Language("ru", "ru", "Русский", "Cyrillic", ("russian", "俄文", "俄语")),
    Language("be", "be", "Беларуская", "Cyrillic", ("belarusian",)),
    Language("uk", "uk", "Українська", "Cyrillic", ("ukrainian",)),
    Language("bg", "bg", "Български", "Cyrillic", ("bulgarian",)),
    Language("kk", "kk", "Қазақ", "Cyrillic", ("kazakh",)),
    Language("ky", "ky", "Кыргызча", "Cyrillic", ("kyrgyz",)),
    Language("mk", "mk", "Македонски", "Cyrillic", ("macedonian",)),
    Language("mn", "mn", "Монгол", "Cyrillic", ("mongolian",)),
    Language("sr-Cyrl", "rs_cyrillic", "Српски (ћирилица)", "Cyrillic", ("serbian-cyrillic",)),
    Language("tg", "tg", "Тоҷикӣ", "Cyrillic", ("tajik",)),
    Language("tt", "tt", "Татар", "Cyrillic", ("tatar",)),
    # --- Arabic script ---------------------------------------------------
    Language("ar", "ar", "العربية", "Arabic", ("arabic", "阿拉伯文", "阿拉伯语")),
    Language("fa", "fa", "فارسی", "Arabic", ("persian", "farsi")),
    Language("ps", "ps", "پښتو", "Arabic", ("pashto",)),
    Language("sd", "sd", "سنڌي", "Arabic", ("sindhi",)),
    Language("ug", "ug", "ئۇيغۇرچە", "Arabic", ("uyghur",)),
    Language("ur", "ur", "اردو", "Arabic", ("urdu",)),
    # --- Devanagari script -----------------------------------------------
    Language("hi", "hi", "हिन्दी", "Devanagari", ("hindi", "印地文", "印地语")),
    Language("mr", "mr", "मराठी", "Devanagari", ("marathi",)),
    Language("ne", "ne", "नेपाली", "Devanagari", ("nepali",)),
    Language("sa", "sa", "संस्कृतम्", "Devanagari", ("sanskrit",)),
    # --- Other scripts ---------------------------------------------------
    Language("th", "th", "ไทย", "Thai", ("thai", "泰文", "泰语")),
    Language("el", "el", "Ελληνικά", "Greek", ("greek", "希腊文", "希腊语")),
    Language("ka", "ka", "ქართული", "Georgian", ("georgian",)),
    Language("ta", "ta", "தமிழ்", "Tamil", ("tamil",)),
    Language("te", "te", "తెలుగు", "Telugu", ("telugu",)),
)


def _build_alias_index() -> dict[str, Language]:
    index: dict[str, Language] = {}
    for language in _LANGUAGES:
        for alias in language.all_aliases:
            existing = index.get(alias)
            if existing is not None and existing is not language:
                raise RuntimeError(
                    f"Alias {alias!r} maps to both {existing.code!r} and {language.code!r}"
                )
            index[alias] = language
    return index


_BY_ALIAS = _build_alias_index()


def resolve_language(value: str) -> Language:
    """Resolve a caller-supplied language string, or raise ``ServiceError``."""
    language = _BY_ALIAS.get(value.strip().casefold()) if value else None
    if language is None:
        raise ServiceError(
            "unsupported_language",
            f"Unsupported OCR language: {value!r}. See GET /v1/languages.",
            422,
        )
    return language


def normalize_language(value: str) -> str:
    """Return the PaddleOCR ``lang`` code for a caller-supplied language."""
    return resolve_language(value).paddle_code


def supported_languages() -> tuple[Language, ...]:
    return _LANGUAGES
