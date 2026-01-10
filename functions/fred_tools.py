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
from plotly.subplots import make_subplots
import plotly.graph_objects as go

from plotly.subplots import make_subplots
import plotly.graph_objects as go

def generate_labor_chart():
    """
    U.S. labor market dashboard (post-2023):
    Panels in this order:
      1) Total NFP
      2) Private
      3) Cyclical = NFP - Gov - Edu&Health
      4) Non-Cyclical = Gov + Edu&Health
      5) Goods-Producing
      6) Service-Providing
      7) Government
      8) Education & Health Services
      9) Temporary Help Services (TEMPHELPS)
     10) Manufacturing (MANEMP)
     11) Leisure & Hospitality (USLAH)

    Each panel: monthly change (Δ, bars) + 3m MA (line) + 0-line + last Δ annotation.
    Returns a Plotly figure.
    """

    def make_delta_df(series_id: str, level_name: str):
        # load_fred_series(series_id) must return a pd.Series with DatetimeIndex
        s = load_fred_series(series_id)
        df = s.to_frame(level_name)
        df["Date"] = df.index
        df["Δ"] = df[level_name].diff()
        df["3m MA"] = df["Δ"].rolling(3).mean()
        df = df[df.index > "2023-01-01"]
        return df

    def make_constructed_delta_df(level_series, level_name: str):
        df = level_series.to_frame(level_name).copy()
        df["Date"] = df.index
        df["Δ"] = df[level_name].diff()
        df["3m MA"] = df["Δ"].rolling(3).mean()
        df = df[df.index > "2023-01-01"]
        return df

    def add_panel(fig, df, row: int, bar_name: str, ma_name: str):
        # Bars: monthly change
        fig.add_trace(
            go.Bar(
                x=df["Date"],
                y=df["Δ"],
                name=bar_name,
            ),
            row=row, col=1
        )

        # Line: 3m MA
        fig.add_trace(
            go.Scatter(
                x=df["Date"],
                y=df["3m MA"],
                name=ma_name,
                mode="lines",
            ),
            row=row, col=1
        )

        # 0-line
        fig.add_hline(y=0, row=row, col=1, line_width=1)

        # Latest Δ annotation
        if len(df) > 0 and df["Δ"].notna().any():
            last = df.dropna(subset=["Δ"]).iloc[-1]
            fig.add_annotation(
                x=last["Date"],
                y=last["Δ"],
                text=f"{int(last['Δ']):,}k",
                showarrow=True,
                row=row, col=1
            )

    # --- Core series (levels -> Δ) ---
    nfp  = make_delta_df("PAYEMS", "Payrolls")
    priv = make_delta_df("USPRIV", "Private Payrolls")
    goods = make_delta_df("USGOOD", "Goods-Producing")
    serv  = make_delta_df("CES0800000001", "Service-Providing")
    govt  = make_delta_df("USGOVT", "Government")
    eduh  = make_delta_df("USEHS", "Education & Health Services")

    # --- Extras (levels -> Δ) ---
    temphelps = make_delta_df("TEMPHELPS", "Temporary Help Services")
    manemp    = make_delta_df("MANEMP", "Manufacturing")
    uslah     = make_delta_df("USLAH", "Leisure & Hospitality")

    # --- Construct cyclical vs non-cyclical from aligned LEVELS ---
    aligned = (
        nfp.set_index("Date")["Payrolls"].to_frame("Payrolls")
        .join(govt.set_index("Date")["Government"], how="inner")
        .join(eduh.set_index("Date")["Education & Health Services"], how="inner")
        .dropna()
    )

    cyclical_level = aligned["Payrolls"] - aligned["Government"] - aligned["Education & Health Services"]
    noncyc_level   = aligned["Government"] + aligned["Education & Health Services"]

    cyc    = make_constructed_delta_df(cyclical_level, "Cyclical Payrolls")
    noncyc = make_constructed_delta_df(noncyc_level,   "Non-Cyclical Payrolls")

    # --- Subplots: 11 stacked panels in requested order ---
    titles = (
        "Total Nonfarm Payrolls (Δ m/m)",
        "Private Payrolls (Δ m/m)",
        "Cyclical Payrolls = NFP − Gov − Edu&Health (Δ m/m)",
        "Non-Cyclical Payrolls = Gov + Edu&Health (Δ m/m)",
        "Goods-Producing Payrolls (Δ m/m)",
        "Service-Providing Payrolls (Δ m/m)",
        "Government Payrolls (Δ m/m)",
        "Education & Health Services Payrolls (Δ m/m)",
        "Temporary Help Services (Δ m/m)",
        "Manufacturing Payrolls (Δ m/m)",
        "Leisure & Hospitality Payrolls (Δ m/m)",
    )

    fig = make_subplots(
        rows=11,
        cols=1,
        shared_xaxes=True,
        subplot_titles=titles,
        vertical_spacing=0.03
    )

    add_panel(fig, nfp,       1, "NFP Δ", "NFP 3m MA")
    add_panel(fig, priv,      2, "Private Δ", "Private 3m MA")
    add_panel(fig, cyc,       3, "Cyclical Δ", "Cyclical 3m MA")
    add_panel(fig, noncyc,    4, "Non-Cyclical Δ", "Non-Cyclical 3m MA")
    add_panel(fig, goods,     5, "Goods Δ", "Goods 3m MA")
    add_panel(fig, serv,      6, "Services Δ", "Services 3m MA")
    add_panel(fig, govt,      7, "Government Δ", "Government 3m MA")
    add_panel(fig, eduh,      8, "Edu&Health Δ", "Edu&Health 3m MA")
    add_panel(fig, temphelps, 9, "Temp Help Δ", "Temp Help 3m MA")
    add_panel(fig, manemp,   10, "Manufacturing Δ", "Manufacturing 3m MA")
    add_panel(fig, uslah,    11, "Leisure & Hosp Δ", "Leisure & Hosp 3m MA")

    fig.update_layout(
        title="U.S. Payrolls — Headline, Cyclical vs Non-Cyclical, Sector Components, and Key Extras (Δ m/m + 3m MA)",
        template="plotly_white",
        height=2150,
        margin=dict(l=40, r=20, t=60, b=40),
        legend=dict(orientation="h", y=-0.05),
        barmode="overlay",
    )

    return fig


# -------------------------------------------------------------------
# Commentary to display BELOW the chart in Streamlit (e.g., st.markdown)
# -------------------------------------------------------------------
LABOR_EXTRAS_COMMENTARY = """
**TEMPHELPS (Temporary Help Services)**  
Best early-cycle / turning-point labor indicator. Often rolls over before headline NFP.

**MANEMP (Manufacturing) (optionally split Durable/Nondurable)**  
Cyclical + inventory/ISM linkage. Useful to confirm “hard-landing” risk vs softening.

**USLAH (Leisure & Hospitality)**  
Great read on services demand + immigration/participation dynamics; also where post-COVID normalization showed up.

**Add only if you have a specific question you’re trying to answer**

- **USCONS (Construction):** useful if your macro focus is housing / rates transmission.  
- **USTPU / Transportation & Warehousing:** useful if you care about goods cycle / logistics (Amazon, inventories).  
- **USPBS (Prof & Business Services):** often informative but can be “meh” unless you’re tracking white-collar softness.  
- **Wholesale / Retail trade:** usually redundant unless you’re doing a consumer-focused deep dive.  
- **Durable vs nondurable split:** nice-to-have, but I’d only add if you already watch manufacturing closely.

**Practical recommendation (keep it lean)**  
Keep the core 11 panels as your default “labor dashboard”. Add more sub-sectors only when you’re debugging a specific macro question.
"""


