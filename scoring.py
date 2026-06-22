"""Scoring configuration for climbing routes.

The website assigns a point value to each route based on its (Sektor-normalized)
color. Everything score-related is driven by this single module so the scheme can
be tuned without touching analytics or UI code.

To change the scoring later:
  - adjust POINTS in the active scheme, or
  - add a new scheme to SCHEMES and switch ACTIVE_SCHEME.
"""

# Canonical Sektor44 colors in ascending difficulty order. Same set as SEKTOR_COLORS in colors.py.
# Kept independent here to avoid importing pymorphy2 just to render the dashboard.
COLOR_ORDER: list[str] = [
    "белый", "жёлтый", "зелёный", "фиолетовый", "розовый",
    "красный", "оранжевый", "синий", "чёрный",
]

# Display colors (hex) so charts roughly match real route colors.
COLOR_HEX: dict[str, str] = {
    "белый": "#cfcfcf",       # rendered grey so it's visible on white bg
    "жёлтый": "#f1c40f",
    "зелёный": "#2ecc71",
    "розовый": "#ff6fa5",
    "красный": "#e74c3c",
    "фиолетовый": "#9b59b6",
    "оранжевый": "#e67e22",
    "синий": "#3498db",
    "чёрный": "#2c3e50",
}


def _linear_points() -> dict[str, int]:
    """1 point for the easiest color, +1 per step up the difficulty scale."""
    return {color: i + 1 for i, color in enumerate(COLOR_ORDER)}

def _arithmetic_points() -> dict[str, int]:
    """1 point for the easiest color, +k per step up the difficulty scale."""
    k = 2
    return {color: k * i + 1 for i, color in enumerate(COLOR_ORDER)}

def _exponential_points() -> dict[str, int]:
    """1 point for the easiest color, k times more per step up the difficulty scale."""
    k = 1.5
    return {color: i**k + 1 for i, color in enumerate(COLOR_ORDER)}


# Registry of named scoring schemes. Add more (e.g. exponential) here.
SCHEMES: dict[str, dict[str, int]] = {
    "linear": _linear_points(),
    "arithmetic": _arithmetic_points(),
    "exponential": _exponential_points(),
}

ACTIVE_SCHEME: str = "arithmetic"


def color_points() -> dict[str, int]:
    """Return the {color: points} map for the active scheme."""
    return SCHEMES[ACTIVE_SCHEME]


def points_for(color: str) -> int:
    """Points awarded for a single route of the given color (0 if unknown)."""
    return color_points().get(color, 0)
