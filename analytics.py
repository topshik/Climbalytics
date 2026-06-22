"""Data loading and metric aggregation for the Climbalytics dashboard.

Pure functions only: each takes a DataFrame and returns a DataFrame/scalar.
No Streamlit imports here so the metrics stay testable and reusable.

Layout:
  load_sessions()  -> wide DataFrame (one row per session, one column per color)
  to_long()        -> long DataFrame (one row per session*color), with points/score
  metric_*()       -> aggregated frames ready to chart
"""

import pandas as pd

from scoring import COLOR_ORDER, points_for

# Identifying (non-color) columns in output/sessions.csv.
META_COLUMNS: list[str] = ["date", "athlete", "gym", "city", "trainer"]
# Trainer-route tallies — counts of routes done with a trainer, not colors.
TRAINER_COLUMNS: list[str] = ["гришины", "женины"]


def load_sessions(path: str = "output/sessions.csv") -> pd.DataFrame:
    """Load the ETL output as a wide DataFrame with a parsed datetime column."""
    df = pd.read_csv(path)
    df["date"] = pd.to_datetime(df["date"])
    df["day"] = df["date"].dt.normalize()
    df["month"] = df["date"].dt.to_period("M").dt.to_timestamp()
    return df


def to_long(df: pd.DataFrame) -> pd.DataFrame:
    """Melt color columns into long format and attach points + score.

    Result columns: date, day, month, athlete, gym, city, trainer, color, count,
    points (per route), score (count * points). Zero-count rows are dropped.
    """
    id_vars = META_COLUMNS + ["day", "month"]
    long = df.melt(
        id_vars=id_vars,
        value_vars=COLOR_ORDER,
        var_name="color",
        value_name="count",
    )
    long = long[long["count"] > 0].copy()
    long["points"] = long["color"].map(points_for)
    long["score"] = long["count"] * long["points"]
    # Keep colors ordered by difficulty for stable chart legends.
    long["color"] = pd.Categorical(long["color"], categories=COLOR_ORDER, ordered=True)
    return long


# --- Metrics ---------------------------------------------------------------

def routes_per_day(long: pd.DataFrame) -> pd.DataFrame:
    """Total routes climbed per day."""
    return (
        long.groupby("day", as_index=False)["count"]
        .sum()
        .rename(columns={"count": "routes"})
    )


def score_per_day(long: pd.DataFrame) -> pd.DataFrame:
    """Total score per day."""
    return long.groupby("day", as_index=False)["score"].sum()


def points_per_gym(long: pd.DataFrame) -> pd.DataFrame:
    """Total score accumulated at each gym, descending."""
    return (
        long.groupby("gym", as_index=False)["score"]
        .sum()
        .sort_values("score", ascending=False)
    )


def sessions_per_gym_per_month(df: pd.DataFrame) -> pd.DataFrame:
    """Count of sessions per gym per month (long form for a stacked bar)."""
    return (
        df.groupby(["month", "gym"], as_index=False)
        .size()
        .rename(columns={"size": "sessions"})
    )


def routes_by_color(long: pd.DataFrame) -> pd.DataFrame:
    """Total routes per color across the selection (difficulty-ordered)."""
    out = long.groupby("color", as_index=False, observed=True)["count"].sum()
    return out.sort_values("color")


# --- Fun stats / KPIs ------------------------------------------------------

def kpis(df: pd.DataFrame, long: pd.DataFrame) -> dict[str, object]:
    """Headline numbers for the KPI cards."""
    hardest = ""
    if not long.empty:
        # Hardest color sent = highest-difficulty color with any routes.
        sent = long.groupby("color", observed=True)["count"].sum()
        sent = sent[sent > 0]
        if not sent.empty:
            hardest = str(sent.index.max())
    return {
        "total_routes": int(long["count"].sum()),
        "total_score": int(long["score"].sum()),
        "sessions": int(len(df)),
        "gyms_visited": int(df["gym"].nunique()),
        "hardest_color": hardest,
    }


def athlete_comparison(long: pd.DataFrame) -> pd.DataFrame:
    """Routes and score per athlete."""
    return long.groupby("athlete", as_index=False).agg(
        routes=("count", "sum"),
        score=("score", "sum"),
    )
