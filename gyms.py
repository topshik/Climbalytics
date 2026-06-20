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

    for city in _GYM_CITIES.values():
        if name.strip().lower().endswith(city.lower()):
            name = name[: -len(city)].strip()
            break

    name_lower = name.lower()
    if name_lower in _GYM_ALIASES:
        return _GYM_ALIASES[name_lower]

    return name.title()


def get_gym_city(gym: str) -> str:
    return _GYM_CITIES.get(gym, "")
