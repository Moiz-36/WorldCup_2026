import streamlit as st
from google.cloud import bigquery
import pandas as pd

st.set_page_config(page_title="World Cup 2026", page_icon="⚽", layout="wide")

PROJECT = "project-062cc765-1da6-4fd5-a5b"
DATASET = "WorldCup_2026"

LIVE_STATUS = ("1H", "2H", "HT", "ET", "P", "BT", "LIVE")
DONE_STATUS = ("FT", "AET", "PEN")
SOON_STATUS = ("NS", "TBD")

STAGE_ORDER = [
    "GROUP_STAGE", "LAST_32", "LAST_16",
    "QUARTER_FINALS", "SEMI_FINALS", "THIRD_PLACE", "FINAL",
]

STATUS_LABEL = {
    "1H": "LIVE · 1ST HALF", "2H": "LIVE · 2ND HALF", "HT": "HALF TIME",
    "ET": "EXTRA TIME", "P": "PENALTIES", "BT": "BREAK", "LIVE": "LIVE",
    "FT": "FULL TIME", "AET": "AFTER EXTRA TIME", "PEN": "ON PENALTIES",
}

# Team -> ISO-2 country code (used to build flag emojis)
ISO = {
    "Algeria": "DZ", "Argentina": "AR", "Australia": "AU", "Austria": "AT",
    "Belgium": "BE", "Bosnia-Herzegovina": "BA", "Brazil": "BR", "Canada": "CA",
    "Cape Verde Islands": "CV", "Colombia": "CO", "Congo DR": "CD", "Croatia": "HR",
    "Curaçao": "CW", "Czechia": "CZ", "Ecuador": "EC", "Egypt": "EG",
    "France": "FR", "Germany": "DE", "Ghana": "GH", "Haiti": "HT", "Iran": "IR",
    "Iraq": "IQ", "Ivory Coast": "CI", "Japan": "JP", "Jordan": "JO",
    "Mexico": "MX", "Morocco": "MA", "Netherlands": "NL", "New Zealand": "NZ",
    "Norway": "NO", "Panama": "PA", "Paraguay": "PY", "Portugal": "PT",
    "Qatar": "QA", "Saudi Arabia": "SA", "Senegal": "SN", "South Africa": "ZA",
    "South Korea": "KR", "Spain": "ES", "Sweden": "SE", "Switzerland": "CH",
    "Tunisia": "TN", "Turkey": "TR", "United States": "US", "Uruguay": "UY",
    "Uzbekistan": "UZ",
}
# Subdivision flags that aren't simple ISO-2 pairs
SPECIAL_FLAGS = {"England": "🏴󠁧󠁢󠁥󠁮󠁧󠁿", "Scotland": "🏴󠁧󠁢󠁳󠁣󠁴󠁿"}


def flag(team: str) -> str:
    if team in SPECIAL_FLAGS:
        return SPECIAL_FLAGS[team]
    code = ISO.get(team)
    if not code:
        return "🏳️"
    return "".join(chr(0x1F1E6 + ord(c) - ord("A")) for c in code)


def pretty_stage(s) -> str:
    return str(s).replace("_", " ").title() if s and str(s) != "None" else "—"


def fmt_date(ts) -> str:
    if pd.isna(ts):
        return "TBD"
    return ts.strftime("%b %-d · %H:%M")


@st.cache_resource
def client():
    return bigquery.Client(project=PROJECT)


@st.cache_data(ttl=300)
def q(sql: str) -> pd.DataFrame:
    return client().query(sql).to_dataframe()


CSS = """
<style>
.block-container {padding-top: 2.2rem;}
.cards {display:flex; flex-wrap:wrap; gap:16px; margin-top:6px;}
.match-card {
  flex:1 1 330px; max-width:430px;
  background:linear-gradient(160deg,#1b2030,#13161f);
  border:1px solid #2a2f3a; border-radius:16px; padding:15px 18px;
  box-shadow:0 4px 16px rgba(0,0,0,.28);
  transition:transform .15s ease, border-color .15s ease;
}
.match-card:hover {transform:translateY(-3px); border-color:#16a34a;}
.card-top {display:flex; justify-content:space-between; align-items:center; margin-bottom:14px;}
.badge {font-size:10.5px; font-weight:700; letter-spacing:.5px; color:#9be7b4;
        background:rgba(22,163,74,.16); padding:3px 10px; border-radius:20px;}
.badge.live {color:#ff8a8a; background:rgba(220,38,38,.18);}
.date {font-size:12px; color:#8b93a3;}
.card-body {display:flex; align-items:center; justify-content:space-between; gap:6px;}
.team {display:flex; align-items:center; gap:10px; flex:1; min-width:0;}
.team .tname {font-size:15px; font-weight:600; color:#e7ebf3;
              white-space:nowrap; overflow:hidden; text-overflow:ellipsis;}
.team .flag {font-size:26px; line-height:1;}
.home {justify-content:flex-start;}
.away {justify-content:flex-end; text-align:right;}
.team.win .tname {color:#ffd24d;}
.mid {font-size:20px; font-weight:800; color:#fff; padding:0 8px; white-space:nowrap;}
.mid.vs {font-size:13px; font-weight:700; color:#6b7280;}
.card-foot {margin-top:14px; font-size:10.5px; font-weight:700; letter-spacing:.5px;
            color:#8b93a3; text-transform:uppercase;
            display:flex; align-items:center; justify-content:space-between; gap:12px;}
.conf {display:flex; align-items:center; gap:8px; flex:1; justify-content:flex-end;}
.conf-bar {flex:1; max-width:120px; height:7px; background:#2a2f3a; border-radius:6px; overflow:hidden;}
.conf-fill {height:100%; background:linear-gradient(90deg,#16a34a,#ffd24d);}
.conf-label {color:#ffd24d; font-weight:700;}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


def card_html(badge, date_str, home, away, middle, foot,
              *, live=False, vs=False, home_win=False, away_win=False, confidence=None):
    badge_cls = "badge live" if live else "badge"
    home_cls = "team home win" if home_win else "team home"
    away_cls = "team away win" if away_win else "team away"
    mid_cls = "mid vs" if vs else "mid"
    conf = ""
    if confidence is not None:
        conf = (f'<div class="conf"><div class="conf-bar">'
                f'<div class="conf-fill" style="width:{confidence}%"></div></div>'
                f'<span class="conf-label">{confidence}%</span></div>')
    return (
        f'<div class="match-card">'
        f'<div class="card-top"><span class="{badge_cls}">{badge}</span>'
        f'<span class="date">{date_str}</span></div>'
        f'<div class="card-body">'
        f'<div class="{home_cls}"><span class="flag">{flag(home)}</span>'
        f'<span class="tname">{home}</span></div>'
        f'<div class="{mid_cls}">{middle}</div>'
        f'<div class="{away_cls}"><span class="tname">{away}</span>'
        f'<span class="flag">{flag(away)}</span></div></div>'
        f'<div class="card-foot"><span>{foot}</span>{conf}</div></div>'
    )


def render(cards):
    st.markdown('<div class="cards">' + "".join(cards) + "</div>", unsafe_allow_html=True)


# ===================== Header =====================
st.title("⚽ World Cup 2026")
st.caption("Live fixtures, results and AI score predictions.")

with st.sidebar:
    st.header("⚽ Controls")
    if st.button("🔄 Refresh data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    st.caption("Data cached for 5 minutes.")

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
        SELECT date, home_team, home_goals, away_goals, away_team, stage, status
        FROM `{PROJECT}.{DATASET}.matches`
        WHERE status IN {LIVE_STATUS}
        ORDER BY date
    """)
    if df.empty:
        st.info("No matches are being played right now.")
    else:
        render([card_html(
            pretty_stage(r["stage"]), fmt_date(r["date"]),
            r["home_team"], r["away_team"],
            f'{int(r["home_goals"])} – {int(r["away_goals"])}',
            STATUS_LABEL.get(r["status"], r["status"]), live=True,
        ) for _, r in df.iterrows()])

# ===================== Results =====================
with past_tab:
    df = q(f"""
        SELECT date, home_team, home_goals, away_goals, away_team, stage, status
        FROM `{PROJECT}.{DATASET}.matches`
        WHERE status IN {DONE_STATUS}
        ORDER BY date DESC
    """)
    if df.empty:
        st.info("No finished matches yet.")
    else:
        present = [s for s in STAGE_ORDER if s in set(df["stage"])]
        labels = ["All"] + [pretty_stage(s) for s in present]
        pick = st.selectbox("Filter by stage", labels, key="past_stage")
        view = df if pick == "All" else df[df["stage"].map(pretty_stage) == pick]
        render([card_html(
            pretty_stage(r["stage"]), fmt_date(r["date"]),
            r["home_team"], r["away_team"],
            f'{int(r["home_goals"])} – {int(r["away_goals"])}',
            STATUS_LABEL.get(r["status"], r["status"]),
            home_win=r["home_goals"] > r["away_goals"],
            away_win=r["away_goals"] > r["home_goals"],
        ) for _, r in view.iterrows()])

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
        render([card_html(
            pretty_stage(r["stage"]), fmt_date(r["date"]),
            r["home_team"], r["away_team"], "vs", "Scheduled", vs=True,
        ) for _, r in df.iterrows()])

# ===================== Predictions =====================
with pred_tab:
    df = q(f"""
        SELECT m.home_team, m.away_team, m.date, m.stage,
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
        cards = []
        for _, r in df.iterrows():
            winner = r["predicted_winner"]
            foot = "🤖 AI Prediction" if winner != "Draw" else "🤖 Draw predicted"
            cards.append(card_html(
                pretty_stage(r["stage"]), fmt_date(r["date"]),
                r["home_team"], r["away_team"],
                f'{r["predicted_home_goals"]:.1f} – {r["predicted_away_goals"]:.1f}',
                foot,
                home_win=winner == r["home_team"],
                away_win=winner == r["away_team"],
                confidence=int(round(r["confidence"] * 100)),
            ))
        render(cards)
