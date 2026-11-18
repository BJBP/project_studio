# Texts of the current language from web/locales/<lang>.json (Spanish by default). t(key, **params) fills
# {placeholders}; a missing key returns the key itself so nothing breaks.
import json
import os
from functools import lru_cache
from pathlib import Path

LOCALES_DIR = Path(__file__).resolve().parents[2] / "web" / "locales"


@lru_cache(maxsize=4)
def _table(lang: str) -> dict:
    path = LOCALES_DIR / f"{lang}.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def t(key: str, **params) -> str:
    text = _table(os.environ.get("STUDIO_LANG", "es")).get(key, key)
    try:
        return text.format(**params)
    except (KeyError, IndexError):
        return text


def describe(issue: dict) -> dict:
    """Adds a readable message to a domain issue."""
    return {**issue, "message": t("issue." + issue["code"], **issue)}
