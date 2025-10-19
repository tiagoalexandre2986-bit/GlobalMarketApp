import time
from datetime import datetime
import streamlit as st
import pandas as pd
import yfinance as yf

st.set_page_config(
    page_title="Global Market Dashboard",
    page_icon="🌍",
    layout="wide"
)

# -----------------------------
# Sidebar controls
# -----------------------------
st.sidebar.title("⚙️ Controls")

# Period options accepted by yfinance
PERIOD_OPTIONS = ["5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y"]
period = st.sidebar.selectbox("Analysis period", PERIOD_OPTIONS, index=1)

show_intraday_change = st.sidebar.checkbox("Show 1-day change column", value=True)
show_trend_charts = st.sidebar.checkbox("Show trend charts", value=True)
normalize_charts = st.sidebar.checkbox("Normalize charts to 100 (relative performance)", value=True)

if st.sidebar.button("🔄 Refresh data"):
    st.toast("Refreshing…")
    st.cache_data.clear()
    time.sleep(0.2)
    st.rerun()

# -----------------------------
# Universe (indices, FX, commodities)
# Yahoo Finance tickers
# -----------------------------
UNIVERSE = {
    "US": {
        "S&P 500": "^GSPC",
        "NASDAQ 100": "^NDX",
        "Dow Jones": "^DJI",
        "Russell 2000": "^RUT",
    },
    "Europe": {
        "Euro Stoxx 50": "^STOXX50E",
        "DAX (Germany)": "^GDAXI",
        "CAC 40 (France)": "^FCHI",
        "FTSE 100 (UK)": "^FTSE",
        "IBEX 35 (Spain)": "^IBEX",
        "FTSE MIB (Italy)": "FTSEMIB.MI",
    },
    "Asia Pacific": {
        "Nikkei 225 (Japan)": "^N225",
        "TOPIX (Japan)": "^TOPX",
        "Hang Seng (HK)": "^HSI",
        "CSI 300 (China A)": "000300.SS",
        "KOSPI (Korea)": "^KS11",
        "ASX 200 (Australia)": "^AXJO",
        "NIFTY 50 (India)": "^NSEI",
    },
    "Latin America": {
        "Ibovespa (Brazil)": "^BVSP",      # 🇧🇷 B3 / Bovespa
        "Merval (Argentina)": "^MERV",
        "IPSA (Chile)": "^IPSA",
        "Colcap (Colombia)": "^COLCAP",
        "S&P/BMV IPC (Mexico)": "^MXX",
        "SP IPSA Select (Chile USD)": "CHILE.SN",
    },
    "FX & Commodities": {
        "EUR/USD": "EURUSD=X",
        "USD/JPY": "JPY=X",
        "GBP/USD": "GBPUSD=X",
        "USD/BRL": "BRL=X",
        "WTI Crude": "CL=F",
        "Brent Crude": "BZ=F",
        "Gold": "GC=F",
        "Silver": "SI=F",
        "Copper": "HG=F",
    },
}

# Build a flat map for convenience
ALL_SERIES = {}
for group, mapping in UNIVERSE.items():
    for label, ticker in mapping.items():
        ALL_SERIES[label] = {"group": group, "ticker": ticker}

# Allow user to pick which groups to show
group_choices = st.sidebar.multiselect(
    "Groups to include",
    options=list(UNIVERSE.keys()),
    default=list(UNIVERSE.keys())
)
selected_labels = [
    label for label, meta in ALL_SERIES.items() if meta["group"] in group_choices
]

st.title("🌍 Global Market Overview")
st.caption(
    f"Period: **{period}** · Data source: Yahoo Finance via `yfinance` · "
    f"Last refresh: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}"
)

# -----------------------------
# Data loading
# -----------------------------
@st.cache_data(ttl=600, show_spinner=False)
def fetch_series(tickers: dict[str, str], period: str) -> dict:
    """
    Returns dict[label] -> DataFrame with columns ['Close'] (and maybe 'Adj Close'].
    Skips empties and handles Yahoo quirks.
    """
    out: dict[str, pd.DataFrame] = {}
    for label, ticker in tickers.items():
        try:
            df = yf.download(ticker, period=period, auto_adjust=False, progress=False)
            if df.empty:
                continue
            # Normalize column names
            df = df[["Close"]].dropna().copy()
            out[label] = df
        except Exception:
            # Skip on any download error; keep UI responsive
            continue
    return out

# Build map for selected labels -> tickers
label_to_ticker = {label: ALL_SERIES[label]["ticker"] for label in selected_labels}
data = fetch_series(label_to_ticker, period)

if not data:
    st.error("⚠️ Could not load any data. Try a shorter period, or hit **Refresh data**.")
    st.stop()

# -----------------------------
# Compute returns table
# -----------------------------
def pct_change_over_period(df: pd.DataFrame) -> float:
    if df.shape[0] < 2:
        return float("nan")
    start = df["Close"].iloc[0]
    end = df["Close"].iloc[-1]
    return (end / start - 1.0) * 100

def one_day_change(df: pd.DataFrame) -> float:
    if df.shape[0] < 2:
        return float("nan")
    return df["Close"].pct_change().iloc[-1] * 100

rows = []
for label, df in data.items():
    rows.append({
        "Label": label,
        "Group": ALL_SERIES[label]["group"],
        "Period %": round(pct_change_over_period(df), 2),
        "1D %": round(one_day_change(df), 2) if show_intraday_change else None,
        "Last": round(df["Close"].iloc[-1], 2)
    })

table = pd.DataFrame(rows).sort_values(by="Period %", ascending=True, na_position="last").reset_index(drop=True)

# -----------------------------
# UI: Tabs (Overview, Groups, Charts)
# -----------------------------
tab_overview, tab_groups, tab_charts = st.tabs(["📋 Overview", "🗂️ By Group", "📈 Charts"])

with tab_overview:
    # Top losers / gainers over the chosen period
    left, right = st.columns(2)
    with left:
        st.subheader("📉 Bottom 10 (by Period %)")
        st.dataframe(table.nsmallest(10, "Period %")[["Label", "Group", "Period %", "1D %", "Last"]], use_container_width=True)
    with right:
        st.subheader("📈 Top 10 (by Period %)")
        st.dataframe(table.nlargest(10, "Period %")[["Label", "Group", "Period %", "1D %", "Last"]], use_container_width=True)

    st.subheader("🧮 Full Table")
    st.dataframe(table[["Label", "Group", "Period %", "1D %", "Last"]], use_container_width=True)

with tab_groups:
    for group in group_choices:
        st.markdown(f"### {group}")
        subset_labels = [lbl for lbl in data.keys() if ALL_SERIES[lbl]["group"] == group]
        if not subset_labels:
            st.info("No data for this group.")
            continue
        sub = table[table["Group"] == group][["Label", "Period %", "1D %", "Last"]]
        st.dataframe(sub.sort_values(by="Period %"), use_container_width=True)

with tab_charts:
    st.write("Tip: Use the sidebar to toggle normalization and chart visibility.")
    if not show_trend_charts:
        st.info("Enable **Show trend charts** in the sidebar to render charts.")
    else:
        # Multi-select for which lines to chart together
        default_for_chart = [lbl for lbl in data.keys() if "Brazil" in lbl or "Ibovespa" in lbl] or list(data.keys())[:5]
        selected_for_chart = st.multiselect(
            "Series to plot together",
            options=list(data.keys()),
            default=default_for_chart
        )
        if selected_for_chart:
            chart_df = pd.DataFrame(index=next(iter(data.values())).index)
            for lbl in selected_for_chart:
                s = data[lbl]["Close"].copy()
                if normalize_charts:
                    s = s / s.iloc[0] * 100.0
                chart_df[lbl] = s
            st.line_chart(chart_df, use_container_width=True)

        st.divider()

        # Small charts per group
        for group in group_choices:
            st.markdown(f"#### {group} — trend mini-charts")
            cols = st.columns(3)
            i = 0
            for lbl in [l for l in data.keys() if ALL_SERIES[l]["group"] == group]:
                with cols[i % 3]:
                    s = data[lbl]["Close"].copy()
                    if normalize_charts and s.shape[0] > 0:
                        s = s / s.iloc[0] * 100.0
                    st.caption(lbl)
                    st.line_chart(s, use_container_width=True)
                i += 1

# Footer
st.write("")
st.caption("Built with Streamlit • Data from Yahoo Finance (`yfinance`).")
