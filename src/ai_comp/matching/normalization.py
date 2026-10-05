import re
import unicodedata


_SPACE_RE = re.compile(r"\s+")
_PUNCT_RE = re.compile(r"[\u200b\ufeff]")


def normalize_question_text(text: str) -> str:
    value = unicodedata.normalize("NFKC", text)
    value = _PUNCT_RE.sub("", value)
    value = value.casefold()
    value = re.sub(r"[^\w\u0900-\u097f\s]", " ", value)
    return _SPACE_RE.sub(" ", value).strip()


def question_text_key(text: str) -> str:
    return normalize_question_text(text)
