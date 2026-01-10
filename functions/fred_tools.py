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
        legend=dict(orientation="h", y=-0.03),  # ← disabled for now (keep for later)
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
    # ------------------------------------------------
    # JOBS
    # ------------------------------------------------
from plotly.subplots import make_subplots
import plotly.graph_objects as go

from plotly.subplots import make_subplots
import plotly.graph_objects as go

def generate_jobs_chart():
    """
    U.S. Job Market — stacked (single column), PM-readable.

    DATE RULES (as requested):
    - Unemployment rate (household survey, UNRATE): from 2005-01-01
    - Participation rate (CIVPART): from 2005-01-01
    - Claims (ICSA, CCSA): from 2022-01-01
    - JOLTS (JTSJOL, JTSHIR, JTSQUR, JTSLDR): FULL HISTORY (no start-date filter)

    Panels (top to bottom):
    1) Unemployment Rate (UNRATE)
    2) Participation Rate (CIVPART)
    3) Initial Claims (ICSA) + 12w MA
    4) Continued Claims (CCSA)
    5) Job Openings (JTSJOL)
    6) Hires rate (JTSHIR)
    7) Quits rate (JTSQUR)
    8) Layoffs & discharges rate (JTSLDR)
    """

    UNRATE_START_DATE = "2005-01-01"
    CIVPART_START_DATE = "2005-01-01"
    CLAIMS_START_DATE = "2022-01-01"

    def make_level_df(series_id: str, name: str, start_date: str | None = None):
        s = load_fred_series(series_id)  # pd.Series with DatetimeIndex
        df = s.to_frame(name)
        df["Date"] = df.index
        if start_date is not None:
            df = df[df.index > start_date]
        return df

    # ------------------------------------------------
    # Household survey rates (from 2005-01-01)
    # ------------------------------------------------
    unrate = make_level_df("UNRATE", "Unemployment Rate (%)", start_date=UNRATE_START_DATE)
    part   = make_level_df("CIVPART", "Participation Rate (%)", start_date=CIVPART_START_DATE)

    # ------------------------------------------------
    # Claims (from 2022-01-01)
    # ------------------------------------------------
    ic = make_level_df("ICSA", "Initial Claims", start_date=CLAIMS_START_DATE)
    ic["12w MA"] = ic["Initial Claims"].rolling(window=12).mean()

    cc = make_level_df("CCSA", "Continued Claims", start_date=CLAIMS_START_DATE)

    # ------------------------------------------------
    # JOLTS (full history)
    # ------------------------------------------------
    jol = make_level_df("JTSJOL", "Job Openings (ths)", start_date=None)
    hir = make_level_df("JTSHIR", "Hires rate (%)", start_date=None)
    qur = make_level_df("JTSQUR", "Quits rate (%)", start_date=None)
    ldr = make_level_df("JTSLDR", "Layoffs & discharges rate (%)", start_date=None)

    # ------------------------------------------------
    # Subplots: single column, stacked
    # ------------------------------------------------
    titles = (
        "Unemployment Rate (UNRATE, household survey)",
        "Participation Rate (CIVPART)",
        "Initial Claims (ICSA)",
        "Continued Claims (CCSA)",
        "Job Openings (JTSJOL, level)",
        "Hires Rate (JTSHIR)",
        "Quits Rate (JTSQUR)",
        "Layoffs & Discharges Rate (JTSLDR)",
    )

    fig = make_subplots(
        rows=8,
        cols=1,
        shared_xaxes=False,
        subplot_titles=titles,
        vertical_spacing=0.05
    )

    # 1) Unemployment rate
    fig.add_trace(
        go.Scatter(x=unrate["Date"], y=unrate["Unemployment Rate (%)"], mode="lines"),
        row=1, col=1
    )
    fig.update_yaxes(ticksuffix="%", row=1, col=1)

    # 2) Participation rate
    fig.add_trace(
        go.Scatter(x=part["Date"], y=part["Participation Rate (%)"], mode="lines"),
        row=2, col=1
    )
    fig.update_yaxes(ticksuffix="%", row=2, col=1)

    # 3) Initial claims (level + 12w MA)
    fig.add_trace(
        go.Scatter(x=ic["Date"], y=ic["Initial Claims"], mode="lines"),
        row=3, col=1
    )
    fig.add_trace(
        go.Scatter(x=ic["Date"], y=ic["12w MA"], mode="lines"),
        row=3, col=1
    )

    # 4) Continued claims
    fig.add_trace(
        go.Scatter(x=cc["Date"], y=cc["Continued Claims"], mode="lines"),
        row=4, col=1
    )

    # 5) Job openings
    fig.add_trace(
        go.Scatter(x=jol["Date"], y=jol["Job Openings (ths)"], mode="lines"),
        row=5, col=1
    )

    # 6) Hires rate
    fig.add_trace(
        go.Scatter(x=hir["Date"], y=hir["Hires rate (%)"], mode="lines"),
        row=6, col=1
    )
    fig.update_yaxes(ticksuffix="%", row=6, col=1)

    # 7) Quits rate
    fig.add_trace(
        go.Scatter(x=qur["Date"], y=qur["Quits rate (%)"], mode="lines"),
        row=7, col=1
    )
    fig.update_yaxes(ticksuffix="%", row=7, col=1)

    # 8) Layoffs rate
    fig.add_trace(
        go.Scatter(x=ldr["Date"], y=ldr["Layoffs & discharges rate (%)"], mode="lines"),
        row=8, col=1
    )
    fig.update_yaxes(ticksuffix="%", range=[0, 2.5], row=8, col=1)

    # ------------------------------------------------
    # Layout: remove the right-side "trace 0/..." list
    # ------------------------------------------------
    fig.update_layout(
        title="U.S. Job Market — Household Survey (since 2005), Claims (post-2022), and JOLTS (full history)",
        template="plotly_white",
        height=1750,
        margin=dict(l=60, r=30, t=70, b=40),
        showlegend=False,  # ✅ kills the right-side trace list
        # legend=dict(orientation="h", y=-0.05),  # enable later if needed
    )

    return fig
