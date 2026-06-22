import streamlit as st
from google.cloud import bigquery
import pandas as pd

st.set_page_config(page_title="World Cup_2026", page_icon="⚽", layout="wide")
st.title("World Cup 2026 Dashboard")

PROJECT = "project-062cc765-1da6-4fd5-a5b"
DATASET = "WorldCup_2026"


@st.cache_resource
def client():
    return bigquery.Client(project=PROJECT)


@st.cache_data(ttl=300)
def q(sql: str) -> pd.DataFrame:
    return client().query(sql).to_dataframe()


live, past, upcoming, preds = st.tabs(
    ["🔴 Live", "✅ Past", "📅 Upcoming", "🤖 Predictions"]
)

with live:
    df = q(f"""
        SELECT date, home_team, home_goals, away_goals, away_team, status
        FROM `{PROJECT}.{DATASET}.matches`
        WHERE status IN ('1H','2H','HT','ET','P','LIVE')
        ORDER BY date
    """)
    st.dataframe(df, use_container_width=True) if not df.empty else st.info("No live games right now.")

with past:
    df = q(f"""
        SELECT date, home_team, home_goals, away_goals, away_team, stage
        FROM `{PROJECT}.{DATASET}.matches`
        WHERE status IN ('FT','AET','PEN')
        ORDER BY date DESC
    """)
    st.dataframe(df, use_container_width=True) if not df.empty else st.info("No finished games yet.")

with upcoming:
    df = q(f"""
        SELECT date, home_team, away_team, stage
        FROM `{PROJECT}.{DATASET}.matches`
        WHERE status IN ('NS','TBD')
        ORDER BY date
    """)
    st.dataframe(df, use_container_width=True) if not df.empty else st.info("No upcoming games scheduled.")

with preds:
    df = q(f"""
        SELECT m.home_team, m.away_team,
               p.predicted_home_goals, p.predicted_away_goals,
               p.predicted_winner, p.confidence
        FROM `{PROJECT}.{DATASET}.predictions` p
        JOIN `{PROJECT}.{DATASET}.matches` m USING (match_id)
        ORDER BY p.confidence DESC
    """)
    st.dataframe(df, use_container_width=True) if not df.empty else st.info("No predictions yet.")