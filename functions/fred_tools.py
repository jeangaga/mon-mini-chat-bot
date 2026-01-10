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
    U.S. labor market dashboard (post-2023).
    16 stacked panels, each with:
      - Monthly change (Δ, bars)
      - 3m moving average (line)
      - Zero reference line
      - Latest Δ annotation
    """

    def make_delta_df(series_id: str, level_name: str):
        s = load_fred_series(series_id)   # pd.Series with DatetimeIndex
        df = s.to_frame(level_name)
        df["Date"] = df.index
        df["Δ"] = df[level_name].diff()
        df["3m MA"] = df["Δ"].rolling(3).mean()
        return df[df.index > "2023-01-01"]

    def make_constructed_delta_df(level_series, name: str):
        df = level_series.to_frame(name)
        df["Date"] = df.index
        df["Δ"] = df[name].diff()
        df["3m MA"] = df["Δ"].rolling(3).mean()
        return df[df.index > "2023-01-01"]

    def add_panel(fig, df, row, label):
        fig.add_bar(
            x=df["Date"],
            y=df["Δ"],
            name=f"{label} Δ",
            row=row,
            col=1
        )

        fig.add_trace(
            go.Scatter(
                x=df["Date"],
                y=df["3m MA"],
                name=f"{label} 3m MA",
                mode="lines"
            ),
            row=row,
            col=1
        )

        fig.add_hline(y=0, row=row, col=1, line_width=1)

        if df["Δ"].notna().any():
            last = df.dropna(subset=["Δ"]).iloc[-1]
            fig.add_annotation(
                x=last["Date"],
                y=last["Δ"],
                text=f"{int(last['Δ']):,}k",
                showarrow=True,
                row=row,
                col=1
            )

    # --- Core series ---
    nfp   = make_delta_df("PAYEMS", "Payrolls")
    priv  = make_delta_df("USPRIV", "Private Payrolls")
    goods = make_delta_df("USGOOD", "Goods-Producing")
    serv  = make_delta_df("CES0800000001", "Service-Providing")
    govt  = make_delta_df("USGOVT", "Government")
    eduh  = make_delta_df("USEHS", "Education & Health Services")

    # --- Extras ---
    temp  = make_delta_df("TEMPHELPS", "Temporary Help Services")
    man   = make_delta_df("MANEMP", "Manufacturing")
    lah   = make_delta_df("USLAH", "Leisure & Hospitality")

    cons  = make_delta_df("USCONS", "Construction")
    dman  = make_delta_df("DMANEMP", "Durable Goods")
    ndman = make_delta_df("NDMANEMP", "Nondurable Goods")
    tpu   = make_delta_df("USTPU", "Trade, Transportation & Utilities")
    pbs   = make_delta_df("USPBS", "Professional & Business Services")

    # --- Cyclical vs Non-cyclical ---
    aligned = (
        nfp.set_index("Date")["Payrolls"]
        .to_frame("Payrolls")
        .join(govt.set_index("Date")["Government"])
        .join(eduh.set_index("Date")["Education & Health Services"])
        .dropna()
    )

    cyc  = make_constructed_delta_df(
        aligned["Payrolls"] - aligned["Government"] - aligned["Education & Health Services"],
        "Cyclical Payrolls"
    )
    nonc = make_constructed_delta_df(
        aligned["Government"] + aligned["Education & Health Services"],
        "Non-Cyclical Payrolls"
    )

    titles = [
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
        "Construction Payrolls (Δ m/m)",
        "Durable Goods Payrolls (Δ m/m)",
        "Nondurable Goods Payrolls (Δ m/m)",
        "Trade, Transportation & Utilities Payrolls (Δ m/m)",
        "Professional & Business Services Payrolls (Δ m/m)",
    ]

    fig = make_subplots(
        rows=16,
        cols=1,
        shared_xaxes=True,
        subplot_titles=titles,
        vertical_spacing=0.025
    )

    panels = [
        nfp, priv, cyc, nonc, goods, serv, govt, eduh,
        temp, man, lah, cons, dman, ndman, tpu, pbs
    ]

    labels = [
        "NFP", "Private", "Cyclical", "Non-Cyclical",
        "Goods", "Services", "Government", "Edu & Health",
        "Temp Help", "Manufacturing", "Leisure & Hosp",
        "Construction", "Durable", "Nondurable", "TTU", "PBS"
    ]

    for i, (df, lab) in enumerate(zip(panels, labels), start=1):
        add_panel(fig, df, i, lab)

    fig.update_layout(
        title="U.S. Payrolls — Full Decomposition (Δ m/m + 3m MA)",
        template="plotly_white",
        height=3000,
        margin=dict(l=40, r=20, t=60, b=40),
        # legend=dict(orientation="h", y=-0.03),  # ← disabled for now (keep for later)
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


