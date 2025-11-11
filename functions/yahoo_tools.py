# functions/yahoo_tools.py
"""
=========================================================
📈 Yahoo Tools — Fetch & Plot OHLC Data for Indices/Stocks
=========================================================

Fonctions utilitaires pour :
- Télécharger des données OHLC depuis Yahoo Finance
- Générer un graphique Plotly candlestick

Dépendances :
    pip install yfinance plotly pandas
"""

import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta


# ============================================================
# 1️⃣ Téléchargement des données Yahoo (indices + actions)
# ============================================================
import yfinance as yf
import pandas as pd

def load_indices_ohlc():
    """
    Charge les données OHLC pour indices + principaux stocks.
    Retourne un dict {ticker: DataFrame}.
    """
    tickers = {
        # --- Indices ---
        "SPX": "^GSPC",
        "SX5E": "^STOXX50E",
        "RUT": "^RUT",
        "NDX": "^NDX",
        "HSI": "^HSI",
        "CAC": "^FCHI",

        # --- Stocks (ajout) ---
        "META": "META",
        "AAPL": "AAPL",
        "AMZN": "AMZN",
        "GOOGL": "GOOGL",
        "MSFT": "MSFT",
        "NVDA": "NVDA",
        "TSLA": "TSLA",
        "PLTR": "PLTR",
        "AVGO": "AVGO",
        "WMT": "WMT",
        "TGT": "TGT",
        "HD": "HD",
        "JPM": "JPM",
    }

    data = yf.download(
        list(tickers.values()),
        period="3mo",
        interval="1d",
        auto_adjust=False,
    )

    out = {}
    for code, yahoo in tickers.items():
        ohlc = data.xs(yahoo, level=1, axis=1)[["Open", "High", "Low", "Close"]]
        out[code] = ohlc

    return out  # dict: {"SPX": df, "SX5E": df, "RUT": df}

# ============================================================
# 2️⃣ Génération du graphique Plotly OHLC
# ============================================================
def generate_ohlc(ohlc_df: pd.DataFrame, name: str = "SPX"):
    """Generate an interactive OHLC Plotly figure from a single-index OHLC DataFrame."""

    # ✅ Allow passing the full dict {code: df} — keep only the selected one
    if isinstance(ohlc_df, dict):
        ohlc_df = ohlc_df.get(name)
        ohlc_df =ohlc_df.dropna()
        if ohlc_df is None:
            raise ValueError(f"{name} not found in provided OHLC dict")
    # --- détecter les jours manquants (fériés) ---
    full_index = pd.date_range(start=ohlc_df.index.min(), end=ohlc_df.index.max(), freq="B")
    missing = full_index.difference(ohlc_df.index)

    # --- perfs 1d & 3m ---
    closes = ohlc_df["Close"].dropna()
    if len(closes) < 2:
        raise ValueError(f"Not enough data to compute performance for {name}")

    last_close = closes.iloc[-1]
    prev_close = closes.iloc[-2]
    start_close = closes.iloc[0]   # début des 3 mois

    perf_1d = (last_close / prev_close - 1) * 100
    perf_3m = (last_close / start_close - 1) * 100

    perf_1d_str = f"{perf_1d:+.1f}%"
    perf_3m_str = f"{perf_3m:+.1f}%"

    # --- figure OHLC ---
    fig = go.Figure(
        data=go.Ohlc(
            x=ohlc_df.index,
            open=ohlc_df["Open"],
            high=ohlc_df["High"],
            low=ohlc_df["Low"],
            close=ohlc_df["Close"],
            name=name,
        )
    )

    fig.update_xaxes(
        rangebreaks=[
            dict(bounds=["sat", "mon"]),
            dict(values=missing),
        ],
        tickformat="%b %d",
        tickangle=-45,
        nticks=8,
    )

    fig.update_layout(
        title=f"{name} – 1d: {perf_1d_str} • 3m: {perf_3m_str}",
        xaxis_title="Date",
        yaxis_title="Index level",
        xaxis_rangeslider_visible=False,
        template="plotly_white",
        height=350,
        margin=dict(l=40, r=10, t=40, b=60),
    )

    return fig
