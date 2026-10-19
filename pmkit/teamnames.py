"""Team-name normalisation for joining data from sources that spell names differently.

Handles flag emojis, shortcodes (``:mx:``), venue icons, sort hints (``@@12``),
accents, punctuation and common aliases ("USA" vs "United States").
"""
import re
import unicodedata

_FLAG_RE = re.compile(r":[a-z]{2}:")
_ICON_RE = re.compile(r"[\U0001F3E0-\U0001F3FF\U0001F1E6-\U0001F1FF🏆🏟️]")
_SORT_RE = re.compile(r"@@\d+")

_ALIASES = {
    "usa": "unitedstates", "us": "unitedstates",
    "korearepublic": "southkorea", "republicofkorea": "southkorea",
    "iriran": "iran", "czechrepublic": "czechia",
    "bosniaherzegovina": "bosniaandherzegovina", "caboverde": "capeverde",
    "congodr": "drcongo", "cotedivoire": "ivorycoast",
    "turkiye": "turkey", "trkiye": "turkey",
}


def strip_flag(text: str) -> str:
    text = _FLAG_RE.sub("", text)
    text = _ICON_RE.sub("", text)
    return _SORT_RE.sub("", text).strip()


def _transliterate(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(c for c in decomposed if not unicodedata.combining(c))


def normalize(name: str) -> str:
    base = re.sub(r"[^a-z]", "", _transliterate(strip_flag(name)).lower())
    return _ALIASES.get(base, base)


def match_team(raw: str, keys) -> str | None:
    """Best-matching key for ``raw``: exact normalised match, then a guarded substring match."""
    target = normalize(raw)
    if not target:
        return None
    for key in keys:
        if normalize(key) == target:
            return key
    for key in keys:
        nk = normalize(key)
        # Short codes ("ne") would substring-match inside long names ("netherlands").
        if nk and len(nk) >= 4 and (nk in target or target in nk):
            return key
    return None
