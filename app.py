import streamlit as st
from google.cloud import bigquery
import pandas as pd

st.set_page_config(page_title="World Cup 2026", page_icon="⚽", layout="wide")

PROJECT = "project-062cc765-1da6-4fd5-a5b"
DATASET = "WorldCup_2026"

LIVE_STATUS = ("1H", "2H", "HT", "ET", "P", "LIVE")
DONE_STATUS = ("FT", "AET", "PEN")
SOON_STATUS = ("NS", "TBD")

STAGE_ORDER = [
    "GROUP_STAGE", "LAST_32", "LAST_16",
    "QUARTER_FINALS", "SEMI_FINALS", "THIRD_PLACE", "FINAL",
]


@st.cache_resource
def client():
    return bigquery.Client(project=PROJECT)


@st.cache_data(ttl=300)
def q(sql: str) -> pd.DataFrame:
    return client().query(sql).to_dataframe()


def pretty_stage(s: str) -> str:
    return str(s).replace("_", " ").title() if s else "—"


def score(df: pd.DataFrame) -> pd.Series:
    return (df["home_goals"].astype("Int64").astype(str)
            + "  –  "
            + df["away_goals"].astype("Int64").astype(str))


# ----- shared column configs -----
DATE_COL = st.column_config.DatetimeColumn("Date", format="MMM D,  HH:mm")
STAGE_COL = st.column_config.TextColumn("Stage")


# ===================== Header =====================
st.title("⚽ World Cup 2026 Dashboard")
st.caption("Live fixtures, results and AI score predictions — data from BigQuery.")

with st.sidebar:
    st.header("Controls")
    if st.button("🔄 Refresh data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    st.caption("Data is cached for 5 minutes.")

# ----- summary metrics -----
counts = q(f"""
    SELECT
      COUNTIF(status IN {DONE_STATUS}) AS finished,
      COUNTIF(status IN {LIVE_STATUS}) AS live,
      COUNTIF(status IN {SOON_STATUS}) AS upcoming,
      COUNT(*) AS total
    FROM `{PROJECT}.{DATASET}.matches`
""").iloc[0]
preds_n = q(f"SELECT COUNT(*) AS n FROM `{PROJECT}.{DATASET}.predictions`").iloc[0]["n"]

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total matches", int(counts["total"]))
c2.metric("🔴 Live now", int(counts["live"]))
c3.metric("✅ Finished", int(counts["finished"]))
c4.metric("🤖 Predictions", int(preds_n))

st.divider()

live_tab, past_tab, soon_tab, pred_tab = st.tabs(
    ["🔴 Live", "✅ Results", "📅 Upcoming", "🤖 Predictions"]
)

# ===================== Live =====================
with live_tab:
    df = q(f"""
        SELECT date, home_team, home_goals, away_goals, away_team, status
        FROM `{PROJECT}.{DATASET}.matches`
        WHERE status IN {LIVE_STATUS}
        ORDER BY date
    """)
    if df.empty:
        st.info("No matches are being played right now.")
    else:
        df["Score"] = score(df)
        view = df[["date", "home_team", "Score", "away_team", "status"]]
        st.dataframe(
            view, hide_index=True, use_container_width=True,
            column_config={
                "date": DATE_COL,
                "home_team": "Home",
                "away_team": "Away",
                "status": "Status",
            },
        )

# ===================== Results =====================
with past_tab:
    df = q(f"""
        SELECT date, home_team, home_goals, away_goals, away_team, stage
        FROM `{PROJECT}.{DATASET}.matches`
        WHERE status IN {DONE_STATUS}
        ORDER BY date DESC
    """)
    if df.empty:
        st.info("No finished matches yet.")
    else:
        df["stage"] = df["stage"].map(pretty_stage)
        stages = ["All"] + [pretty_stage(s) for s in STAGE_ORDER if pretty_stage(s) in set(df["stage"])]
        pick = st.selectbox("Filter by stage", stages, key="past_stage")
        if pick != "All":
            df = df[df["stage"] == pick]
        df["Score"] = score(df)
        view = df[["date", "home_team", "Score", "away_team", "stage"]]
        st.dataframe(
            view, hide_index=True, use_container_width=True,
            column_config={
                "date": DATE_COL,
                "home_team": "Home",
                "away_team": "Away",
                "stage": STAGE_COL,
            },
        )

# ===================== Upcoming =====================
with soon_tab:
    df = q(f"""
        SELECT date, home_team, away_team, stage
        FROM `{PROJECT}.{DATASET}.matches`
        WHERE status IN {SOON_STATUS}
        ORDER BY date
    """)
    if df.empty:
        st.info("No upcoming matches scheduled.")
    else:
        df["stage"] = df["stage"].map(pretty_stage)
        st.dataframe(
            df[["date", "home_team", "away_team", "stage"]],
            hide_index=True, use_container_width=True,
            column_config={
                "date": DATE_COL,
                "home_team": "Home",
                "away_team": "Away",
                "stage": STAGE_COL,
            },
        )

# ===================== Predictions =====================
with pred_tab:
    df = q(f"""
        SELECT m.home_team, m.away_team, m.date,
               p.predicted_home_goals, p.predicted_away_goals,
               p.predicted_winner, p.confidence
        FROM `{PROJECT}.{DATASET}.predictions` p
        JOIN `{PROJECT}.{DATASET}.matches` m
          ON CAST(p.match_id AS STRING) = CAST(m.match_id AS STRING)
        ORDER BY p.confidence DESC, m.date
    """)
    if df.empty:
        st.info("No predictions available yet.")
    else:
        df["Predicted score"] = (
            df["predicted_home_goals"].round(1).astype(str)
            + "  –  "
            + df["predicted_away_goals"].round(1).astype(str)
        )
        df["Confidence"] = (df["confidence"] * 100).round(0)
        view = df[["date", "home_team", "away_team",
                   "Predicted score", "predicted_winner", "Confidence"]]
        st.dataframe(
            view, hide_index=True, use_container_width=True,
            column_config={
                "date": DATE_COL,
                "home_team": "Home",
                "away_team": "Away",
                "predicted_winner": "Predicted winner",
                "Confidence": st.column_config.ProgressColumn(
                    "Confidence", min_value=0, max_value=100, format="%d%%"
                ),
            },
        )
