import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="🌍 Global Market Overview", layout="centered")
st.title("🌍 Global Market Overview")

# Major indices (US, Europe, Asia)
indices = {
    "S&P 500": "^GSPC",
    "Dow Jones": "^DJI",
    "Nasdaq": "^IXIC",
    "FTSE 100 (UK)": "^FTSE",
    "DAX (Germany)": "^GDAXI",
    "CAC 40 (France)": "^FCHI",
    "Nikkei 225 (Japan)": "^N225",
    "Hang Seng (HK)": "^HSI",
    "Shanghai Composite": "000001.SS",
    "Sensex (India)": "^BSESN",
}

period = st.selectbox("Period", ["5d", "1mo", "3mo", "6mo", "1y"], index=0)
st.write(f"Showing % change based on last two closes (period fetched: {period})")

rows = []
for name, ticker in indices.items():
    df = yf.download(ticker, period=period, progress=False)
    if df is None or df.empty or "Close" not in df:
        rows.append({"Index": name, "Ticker": ticker, "% Change (last 2 closes)": None})
        continue
    if len(df["Close"]) < 2:
        rows.append({"Index": name, "Ticker": ticker, "% Change (last 2 closes)": None})
        continue
    pct = (df["Close"].iloc[-1] - df["Close"].iloc[-2]) / df["Close"].iloc[-2] * 100
    rows.append({"Index": name, "Ticker": ticker, "% Change (last 2 closes)": round(pct, 2)})

table = pd.DataFrame(rows).set_index("Index")
st.subheader("📈 Last Move (%)")
st.dataframe(table)

# Optional: quick line chart of the selected index
choice = st.selectbox("Chart an index", list(indices.keys()))
hist = yf.download(indices[choice], period=period, progress=False)
if not hist.empty:
    st.line_chart(hist["Close"])
else:
    st.info("No data available for that selection.")