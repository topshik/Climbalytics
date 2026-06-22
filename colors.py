import inspect
import re

import pymorphy2

# pymorphy2 0.9.1 uses inspect.getargspec (removed in Python 3.11+).
inspect.getargspec = lambda f: inspect.getfullargspec(f)[:4]

_MORPH: pymorphy2.MorphAnalyzer = pymorphy2.MorphAnalyzer()

_COLOR_CANONICAL: set[str] = {
    "белый", "жёлтый", "розовый", "красный", "зелёный",
    "фиолетовый", "оранжевый", "синий", "чёрный", "голубой",
}

SEKTOR_COLORS: list[str] = ["белый", "жёлтый", "розовый", "красный", "зелёный", "фиолетовый", "оранжевый", "синий", "чёрный"]
TRAINER_COLORS: list[str] = ["гришины", "женины"]

# Per-gym color mappings to Sektor equivalents (derived from gym notes in chat.json)
_GYM_COLOR_MAP: dict[str, dict[str, str]] = {
    # Puls: "purple=yellow, green=green, orange=purple, blue=pink, yellow=red, pink=orange"
    "Puls": {
        "фиолетовый": "жёлтый",
        "зелёный": "зелёный",
        "оранжевый": "фиолетовый",
        "синий": "розовый",
        "голубой": "розовый",
        "жёлтый": "красный",
        "розовый": "оранжевый",
    },
    "Climb Lab": {
        "белый": "зелёный",
        "жёлтый": "фиолетовый",
        "зелёный": "розовый",
        "синий": "красный",
        "красный": "оранжевый",
        "чёрный": "синий",
        "серый": "чёрный",
    },
    # Element Munich: "3 — зелёная, 4 — фиолетовая, 5 — розовая, 6 — красная"
    "Element": {
        "уровень 2": "белый",
        "уровень 3": "зелёный",
        "уровень 4": "фиолетовый",
        "уровень 5": "розовый",
        "уровень 6": "красный",
    },
    # Kreuzberg: "зеленые-желтые, желтые-зеленые, синие-фиолетовые, красные-розовые"
    "Kreuzberg Boulderhalle": {
        "зелёный": "жёлтый",
        "жёлтый": "зелёный",
        "синий": "фиолетовый",
        "красный": "розовый",
    },
    # Urban Apes: "2-жёлтые; 3-зелёные; 4-фиолетовые; 5-розовые; 6-красные"
    "Urban Apes": {
        "уровень 2": "жёлтый",
        "уровень 3": "зелёный",
        "уровень 4": "фиолетовый",
        "уровень 5": "розовый",
        "уровень 6": "красный",
    },
    # Berta: "желтые-зеленые, розовые-фиолетовые, зеленые-фиолетовые, синие-красные"
    "Berta": {
        "жёлтый": "зелёный",
        "розовый": "фиолетовый",
        "зелёный": "фиолетовый",
        "синий": "красный",
    },
    # Monk Amsterdam — colors already match Sektor
    "Monk": {},
}


def normalize_text(raw_text: str) -> str:
    """Lowercase and standardize color adjectives to nominative singular masculine."""
    text = raw_text.lower()
    tokens = re.findall(r"\w+|\W+", text)
    for i, token in enumerate(tokens):
        if token in _COLOR_CANONICAL:
            continue
        for p in _MORPH.parse(token):
            if p.tag.POS in {"ADJF", "ADJS"} and p.normal_form in _COLOR_CANONICAL:
                tokens[i] = p.normal_form
                break
    return "".join(tokens)


def map_color(gym: str, color: str) -> str:
    """Map a gym-local color to its Sektor equivalent."""
    return _GYM_COLOR_MAP.get(gym, {}).get(color, color)
