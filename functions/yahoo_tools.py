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
def load_indices_ohlc(period: str = "3mo", interval: str = "1d"):
    """
    Télécharge les prix OHLC pour une liste d'indices et d'actions.
    Retourne un dict {ticker: DataFrame}.
    """
    tickers = [
        # --- Indices ---
        "^GSPC",  # SPX
        "^STOXX50E",  # SX5E
        "^NDX",  # Nasdaq 100
        "^FCHI",  # CAC 40
        "^GDAXI",  # DAX

        # --- Stocks ---
        "META", "AAPL", "AMZN", "GOOGL", "MSFT", "NVDA",
        "TSLA", "PLTR", "AVGO", "WMT", "TGT", "HD", "JPM",
    ]

    all_data = {}
    for t in tickers:
        try:
            df = yf.download(t, period=period, interval=interval, progress=False)
            if df.empty:
                continue
            df = df.rename(columns=str.title)  # Open/High/Low/Close
            all_data[t.replace("^", "")] = df
        except Exception:
            continue

    return all_data


# ============================================================
# 2️⃣ Génération du graphique Plotly OHLC
# ============================================================
def generate_ohlc(ohlc_df: pd.DataFrame, name: str = "SPX"):
    """
    Crée un graphique Plotly OHLC / candlestick.
    ohlc_df doit contenir Open, High, Low, Close.
    """

    if ohlc_df is None or ohlc_df.empty:
        return None

    fig = go.Figure(
        data=[
            go.Candlestick(
                x=ohlc_df.index,
                open=ohlc_df["Open"],
                high=ohlc_df["High"],
                low=ohlc_df["Low"],
                close=ohlc_df["Close"],
                name=name,
            )
        ]
    )

    # Style minimaliste pro
    fig.update_layout(
        title=f"{name} – Yahoo Finance OHLC ({ohlc_df.index.min().date()} → {ohlc_df.index.max().date()})",
        xaxis_title="Date",
        yaxis_title="Price",
        height=500,
        margin=dict(l=40, r=40, t=60, b=40),
        xaxis_rangeslider_visible=False,
        template="plotly_white",
    )

    return fig
