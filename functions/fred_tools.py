# functions/fred_tools.py
"""
=========================================
📊 FRED Tools — U.S. Macro Data & Charts
=========================================

Fonctions utilitaires pour :
- Charger des séries FRED (PAYEMS, USPRIV, etc.)
- Générer un graphique Plotly sur le marché du travail US

Dépendances :
    pip install fredapi plotly pandas
"""

import os
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import fredapi as fa
# Initialize FRED API (use Streamlit secrets in production)
fred = fa.Fred(api_key='6e079bc3e1ab2b8280b94e05ff432f30')




# ============================================================
# 2️⃣ Chargement d'une série FRED
# ============================================================
def load_fred_series(series_id: str) -> pd.Series:
    """
    Fetch une série FRED et renvoie une pandas Series (index = dates).
    Exemple: load_fred_series("PAYEMS"), load_fred_series("USPRIV").
    """
    if fred is None:
        raise RuntimeError("FRED_API_KEY manquante (variable d'environnement non définie).")
    return fred.get_series(series_id)


# ============================================================
# 3️⃣ Graphique du marché du travail US
# ============================================================
def generate_labor_chart():
    """
    U.S. labor market:
    - NFP (PAYEMS) & Private Payrolls (USPRIV)
    - Monthly change (bars)
    - 3m moving average (line)
    """

    # --- Nonfarm Payrolls ---
    nfp = load_fred_series("PAYEMS").to_frame("Payrolls")
    nfp["Date"] = nfp.index
    nfp["Δ"] = nfp["Payrolls"].diff()
    nfp["3m MA"] = nfp["Δ"].rolling(3).mean()
    nfp = nfp[nfp.index > "2022-01-01"]

    # --- Private Payrolls ---
    private = load_fred_series("USPRIV").to_frame("Private")
    private["Date"] = private.index
    private["Δ"] = private["Private"].diff()
    private["3m MA"] = private["Δ"].rolling(3).mean()
    private = private[private.index > "2022-01-01"]

    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        subplot_titles=(
            "Total Nonfarm Payrolls — Monthly Change",
            "Private Payrolls — Monthly Change"
        )
    )

    # --- NFP ---
    fig.add_bar(
        x=nfp["Date"],
        y=nfp["Δ"],
        name="NFP Δ (m/m)",
        row=1,
        col=1
    )
    fig.add_trace(
        go.Scatter(
            x=nfp["Date"],
            y=nfp["3m MA"],
            name="NFP 3m MA",
            mode="lines"
        ),
        row=1,
        col=1
    )

    # --- Private ---
    fig.add_bar(
        x=private["Date"],
        y=private["Δ"],
        name="Private Δ (m/m)",
        row=2,
        col=1
    )
    fig.add_trace(
        go.Scatter(
            x=private["Date"],
            y=private["3m MA"],
            name="Private 3m MA",
            mode="lines"
        ),
        row=2,
        col=1
    )

    # --- Zero lines ---
    fig.add_hline(y=0, row=1, col=1, line_width=1)
    fig.add_hline(y=0, row=2, col=1, line_width=1)

    # --- Latest annotations ---
    fig.add_annotation(
        x=nfp["Date"].iloc[-1],
        y=nfp["Δ"].iloc[-1],
        text=f"{int(nfp['Δ'].iloc[-1]):,}k",
        showarrow=True,
        row=1,
        col=1
    )

    fig.add_annotation(
        x=private["Date"].iloc[-1],
        y=private["Δ"].iloc[-1],
        text=f"{int(private['Δ'].iloc[-1]):,}k",
        showarrow=True,
        row=2,
        col=1
    )

    fig.update_layout(
        title="U.S. Labor Market — Payroll Momentum",
        template="plotly_white",
        height=650,
        legend=dict(orientation="h", y=-0.25),
        margin=dict(l=40, r=20, t=50, b=40)
    )

    return fig

