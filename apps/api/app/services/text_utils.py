import unicodedata


def fold(text: str) -> str:
    """Strip diacritics + lowercase, so 'jokic' matches 'Jokić' either direction."""
    normalized = unicodedata.normalize("NFKD", text)
    return "".join(c for c in normalized if not unicodedata.combining(c)).lower()
