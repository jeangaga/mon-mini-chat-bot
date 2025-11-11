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
    Récupère et trace NFP (PAYEMS) et Private Payrolls (USPRIV),
    en variations mensuelles (Δ) + moyenne mobile 3 mois.

    Retourne une figure Plotly (subplots 2 lignes).
    """

    # --- Nonfarm Payrolls ---
    nfp = load_fred_series("PAYEMS").to_frame("Payrolls")
    nfp["Date"] = nfp.index
    nfp["NFP Δ"] = nfp["Payrolls"].diff()
    nfp["3m MA"] = nfp["NFP Δ"].rolling(window=3).mean()
    nfp = nfp[nfp.index > "2022-01-01"]

    # --- Private Payrolls ---
    private = load_fred_series("USPRIV").to_frame("Private Payrolls")
    private["Date"] = private.index
    private["Private Δ"] = private["Private Payrolls"].diff()
    private["3m MA"] = private["Private Δ"].rolling(window=3).mean()
    private = private[private.index > "2022-01-01"]

    # --- Subplots (2 lignes, 1 colonne) ---
    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        subplot_titles=("Total Nonfarm Payrolls (Δ m/m)", "Private Payrolls (Δ m/m)")
    )

    # Ligne 1 – total NFP
    fig.add_trace(
        go.Scatter(
            x=nfp["Date"],
            y=nfp["NFP Δ"],
            name="NFP Δ (m/m)",
            mode="lines"
        ),
        row=1,
        col=1
    )
    fig.add_trace(
        go.Scatter(
            x=nfp["Date"],
            y=nfp["3m MA"],
            name="NFP Δ – 3m MA",
            mode="lines"
        ),
        row=1,
        col=1
    )

    # Ligne 2 – private payrolls
    fig.add_trace(
        go.Scatter(
            x=private["Date"],
            y=private["Private Δ"],
            name="Private Δ (m/m)",
            mode="lines"
        ),
        row=2,
        col=1
    )
    fig.add_trace(
        go.Scatter(
            x=private["Date"],
            y=private["3m MA"],
            name="Private Δ – 3m MA",
            mode="lines"
        ),
        row=2,
        col=1
    )

    # --- Layout ---
    fig.update_layout(
        title_text="U.S. Labor Market — Monthly Changes in Payrolls (k jobs)",
        template="plotly_white",
        height=600,
        margin=dict(l=40, r=10, t=40, b=40),
        legend=dict(orientation="h", y=-0.2),
    )

    return fig
