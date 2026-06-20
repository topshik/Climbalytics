import csv
import json
import re

import pymorphy2

# pymorphy2 0.9.1 uses inspect.getargspec (removed in Python 3.11+).
# Patch it on the inspect module pymorphy2 imports.
import inspect
inspect.getargspec = lambda f: inspect.getfullargspec(f)[:4]

_MORPH = pymorphy2.MorphAnalyzer()

# Canonical color forms (nominative singular masculine, as returned by pymorphy2)
_COLOR_CANONICAL = {
    "белый", "жёлтый", "розовый", "красный", "зелёный",
    "фиолетовый", "оранжевый", "синий", "чёрный", "голубой",
}


def normalize_text(raw_text: str) -> str:
    """Lowercase and standardize color adjectives to nominative singular masculine
    (e.g. 'желтые'/'желтая' → 'жёлтый', 'белые' → 'белый')."""
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


_GYM_ALIASES: dict[str, str] = {
    "лаба": "Climb Lab",
    "пульс": "Puls",
    "элемент": "Element",
    "kreuzberg boulderhalle": "Kreuzberg Boulderhalle",
    "urban apes": "Urban Apes",
    "berta": "Berta",
}

_GYM_CITIES: dict[str, str] = {
    "Sektor44": "Belgrade",
    "Puls": "Belgrade",
    "Climb Lab": "Moscow",
    "Element": "Munich",
    "Monk": "Amsterdam",
    "Kreuzberg Boulderhalle": "Berlin",
    "Urban Apes": "Berlin",
    "Berta": "Berlin",
}

def clean_gym_name(raw: str) -> str:
    """Normalize gym name: strip colon/city suffix, apply aliases, title-case."""
    name = raw.rstrip(":").strip()

    # Strip trailing city tokens like "Monk Amsterdam" → "Monk"
    for city in _GYM_CITIES.values():
        if name.strip().lower().endswith(city.lower()):
            name = name[: -len(city)].strip()
            break

    name_lower = name.lower()
    if name_lower in _GYM_ALIASES:
        return _GYM_ALIASES[name_lower]

    return name.title()


def get_gym_city(gym: str) -> str:
    """Return city for a known gym."""
    return _GYM_CITIES.get(gym, "")

_SEKTOR_COLORS = ["белый", "жёлтый", "розовый", "красный", "зелёный", "фиолетовый", "оранжевый", "синий", "чёрный"]
_TRAINER_COLORS = ["гришины", "женины"]

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


def _map_color(gym: str, color: str) -> str:
    """Map a gym-local color to Sektor equivalent."""
    mapping = _GYM_COLOR_MAP.get(gym, {})
    return mapping.get(color, color)

_ATHLETE_MAP: dict[str, str] = {
    "user92307774": "Катя",
    "user59707296": "Антон",
}


class Session:
    def __init__(self, text_description: str, date: str, athlete: str):
        self._date = date
        self._athlete = athlete
        self._original_text = text_description
        self._text = normalize_text(text_description)
        self._gym: str = ""
        self._city: str = ""
        self._trainer: str = ""
        self._grishin_routes: int = 0
        self._zhenya_routes: int = 0
        self._routes: dict[str, int] = {}
        self._total_points: int = 0

        self._parse_gym_and_routes()
        self._detect_trainer()

    def _parse_gym_and_routes(self) -> None:
        lines = self._text.split("\n")
        first_line = lines[0]
        rest_lines = lines[1:]

        if first_line.split()[0] in _COLOR_CANONICAL:
            self._gym = "Sektor44"
            self._city = get_gym_city(self._gym)
            self._routes = self._build_routes_dict(lines)
            return

        raw_gym = first_line.split(" (")[0]
        self._gym = clean_gym_name(raw_gym)
        self._city = get_gym_city(self._gym)
        self._routes = self._build_routes_dict(rest_lines)

    def _build_routes_dict(self, lines: list[str]) -> dict[str, int]:
        routes: dict[str, int] = {
            color: 0 for color in _SEKTOR_COLORS
        }
        for line in lines:
            tokens = line.strip().split()
            if len(tokens) < 2:
                continue
            try:
                count = int(tokens[-1])
            except ValueError:
                continue
            color = " ".join(tokens[:-1])

            # Trainer-colored routes — track in their own counters
            if color == "гришины":
                self._grishin_routes = count
                continue
            if color == "женины":
                self._zhenya_routes = count
                continue

            # Skip noise tokens
            if color == "партнер":
                continue

            # Map уровень-style grades (Element, Urban Apes)
            if color.startswith("уровень"):
                sektor = _map_color(self._gym, color)
                if sektor != color:
                    color = sektor
                else:
                    continue  # unknown gym + уровень → skip

            # Map gym-local colors to Sektor equivalents
            sektor = _map_color(self._gym, color)
            if sektor in _SEKTOR_COLORS:
                routes[sektor] = routes.get(sektor, 0) + count
        return routes

    def _detect_trainer(self) -> None:
        if self._grishin_routes > 0:
            self._trainer = "Гриша"
        elif self._zhenya_routes > 0:
            self._trainer = "Женя"

    def to_dict(self) -> dict[str, object]:
        return {
            "date": self._date,
            "athlete": self._athlete,
            "gym": self._gym,
            "city": self._city,
            "trainer": self._trainer,
            **self._routes,
            "гришины": self._grishin_routes,
            "женины": self._zhenya_routes,
        }


def entry_is_valid(entry: dict[str, object]):
    return "date" in entry and "from" in entry and "text" in entry


if __name__ == "__main__":
    sessions: list[Session] = []

    with open("input/chat.json", "r") as f:
        data = json.load(f)

    for entry in data["messages"]:
        if entry_is_valid(entry):
            athlete = _ATHLETE_MAP.get(entry.get("from_id", ""), "?")
            if athlete == "?":
                continue
            sessions.append(Session(entry["text"], entry["date"], athlete))

    rows = [s.to_dict() for s in sessions]
    fieldnames = ["date", "athlete", "gym", "city", "trainer"] + _SEKTOR_COLORS + _TRAINER_COLORS

    with open("output/sessions.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Exported {len(rows)} sessions to output/sessions.csv")