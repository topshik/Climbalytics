from colors import _COLOR_CANONICAL, SEKTOR_COLORS, map_color, normalize_text
from gyms import clean_gym_name, get_gym_city

_ATHLETE_MAP: dict[str, str] = {
    "user92307774": "Катя",
    "user59707296": "Антон",
}


class Session:
    def __init__(self, text_description: str, date: str, athlete: str):
        self._date = date
        self._athlete = athlete
        self._text = normalize_text(text_description)
        self._gym: str = ""
        self._city: str = ""
        self._trainer: str = ""
        self._grishin_routes: int = 0
        self._zhenya_routes: int = 0
        self._routes: dict[str, int] = {}

        self._parse_gym_and_routes()
        self._detect_trainer()

    def _parse_gym_and_routes(self) -> None:
        lines = self._text.split("\n")
        first_line = lines[0]

        first_word = first_line.split()[0]
        if first_word in _COLOR_CANONICAL or first_word == "гришины":
            self._gym = "Sektor44"
            self._city = get_gym_city(self._gym)
            self._routes = self._build_routes_dict(lines)
            return

        raw_gym = first_line.split(" (")[0]
        self._gym = clean_gym_name(raw_gym)
        self._city = get_gym_city(self._gym)
        self._routes = self._build_routes_dict(lines[1:])

    def _build_routes_dict(self, lines: list[str]) -> dict[str, int]:
        routes: dict[str, int] = {color: 0 for color in SEKTOR_COLORS}
        for line in lines:
            tokens = line.strip().split()
            if len(tokens) < 2:
                continue
            try:
                count = int(tokens[-1])
            except ValueError:
                continue
            color = " ".join(tokens[:-1])

            if color == "гришины":
                self._grishin_routes = count
                continue
            if color == "женины":
                self._zhenya_routes = count
                continue
            if color == "партнер":
                continue

            if color.startswith("уровень"):
                sektor = map_color(self._gym, color)
                if sektor != color:
                    color = sektor
                else:
                    continue

            sektor = map_color(self._gym, color)
            if sektor in SEKTOR_COLORS:
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
