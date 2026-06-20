"""Climbalytics dashboard — Streamlit app over output/sessions.csv.

Run locally:
    uv run streamlit run app.py

This module is the thin UI layer: it loads data, exposes sidebar filters, and
renders charts. All aggregation lives in analytics.py; all scoring in scoring.py.
"""

import plotly.express as px
import streamlit as st

import analytics
from scoring import ACTIVE_SCHEME, COLOR_HEX, color_points

st.set_page_config(page_title="Climbalytics", page_icon="🧗", layout="wide")


@st.cache_data
def get_data(path: str = "output/sessions.csv"):
    df = analytics.load_sessions(path)
    return df


st.title("🧗 Climbalytics")
st.caption(f"Bouldering session stats · scoring scheme: **{ACTIVE_SCHEME}**")

try:
    df = get_data()
except FileNotFoundError:
    st.error("output/sessions.csv not found. Run `uv run python convert_to_db.py` first.")
    st.stop()

# --- Sidebar filters -------------------------------------------------------
with st.sidebar:
    st.header("Filters")

    min_day = df["day"].min().date()
    max_day = df["day"].max().date()
    date_range = st.date_input(
        "Date range",
        value=(min_day, max_day),
        min_value=min_day,
        max_value=max_day,
    )

    athletes = sorted(df["athlete"].unique())
    sel_athletes = st.multiselect("Athletes", athletes, default=athletes)

    gyms = sorted(df["gym"].unique())
    sel_gyms = st.multiselect("Gyms", gyms, default=gyms)

    with st.expander("Scoring (linear)"):
        st.table(
            {"color": list(color_points()), "points": list(color_points().values())}
        )

# Apply filters.
mask = df["athlete"].isin(sel_athletes) & df["gym"].isin(sel_gyms)
if isinstance(date_range, (tuple, list)) and len(date_range) == 2:
    start, end = date_range
    mask &= (df["day"].dt.date >= start) & (df["day"].dt.date <= end)
fdf = df[mask].copy()

if fdf.empty:
    st.warning("No sessions match the current filters.")
    st.stop()

long = analytics.to_long(fdf)

# --- KPI cards -------------------------------------------------------------
k = analytics.kpis(fdf, long)
c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("Sessions", k["sessions"])
c2.metric("Total routes", k["total_routes"])
c3.metric("Total score", k["total_score"])
c4.metric("Gyms visited", k["gyms_visited"])
c5.metric("Hardest color", k["hardest_color"] or "—")
# c6.metric("Longest streak", f"{k['longest_streak']} d")

st.divider()

# --- Time series -----------------------------------------------------------
left, right = st.columns(2)

with left:
    st.subheader("Routes per day")
    rpd = analytics.routes_per_day(long)
    fig = px.bar(rpd, x="day", y="routes")
    st.plotly_chart(fig, width='stretch')

with right:
    st.subheader("Score per day")
    spd = analytics.score_per_day(long)
    fig = px.bar(spd, x="day", y="score")
    st.plotly_chart(fig, width='stretch')

# --- Gym breakdowns --------------------------------------------------------
left, right = st.columns(2)

with left:
    st.subheader("Points per gym")
    ppg = analytics.points_per_gym(long)
    fig = px.bar(ppg, x="gym", y="score")
    st.plotly_chart(fig, width='stretch')

with right:
    st.subheader("Sessions per gym per month")
    spm = analytics.sessions_per_gym_per_month(fdf)
    fig = px.bar(spm, x="month", y="sessions", color="gym")
    st.plotly_chart(fig, width='stretch')

# --- Color distribution ----------------------------------------------------
st.subheader("Routes by color")
rbc = analytics.routes_by_color(long)
rbc["color"] = rbc["color"].astype(str)
fig = px.bar(
    rbc,
    x="color",
    y="count",
    color="color",
    color_discrete_map=COLOR_HEX,
)
fig.update_layout(showlegend=False)
st.plotly_chart(fig, width='stretch')

# --- Athlete comparison ----------------------------------------------------
if len(sel_athletes) > 1:
    st.subheader("Athlete comparison")
    cmp = analytics.athlete_comparison(long)
    a, b = st.columns(2)
    with a:
        st.plotly_chart(
            px.bar(cmp, x="athlete", y="routes", title="Routes"),
            width='stretch',
        )
    with b:
        st.plotly_chart(
            px.bar(cmp, x="athlete", y="score", title="Score"),
            width='stretch',
        )

with st.expander("Raw sessions"):
    st.dataframe(fdf.drop(columns=["day", "month"]), width='stretch')
