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
    U.S. Job Market — stacked (single column), with LAST RELEASE labels.

    IMPORTANT (your logic):
    - Fetch FULL HISTORY
    - Compute rolling metrics on FULL HISTORY
    - THEN filter df after chosen start date (display window)

    DATE RULES:
    - UNRATE: display from 2005-01-01 (but computed on full history)
    - CIVPART: display from 2005-01-01 (but computed on full history)
    - Claims (ICSA, CCSA): display from 2022-01-01 (but computed on full history)
    - JOLTS (JTSJOL, JTSHIR, JTSQUR, JTSLDR): FULL HISTORY (no display filter)
    """

    UNRATE_START_DATE = "2005-01-01"
    CIVPART_START_DATE = "2005-01-01"
    CLAIMS_START_DATE = "2022-01-01"

    def make_level_df_full_then_filter(series_id: str, name: str, display_start: str | None = None):
        # 1) full history
        s = load_fred_series(series_id)  # pd.Series with DatetimeIndex
        df = s.to_frame(name)
        df["Date"] = df.index
        # 2) filter only for display
        if display_start is not None:
            df = df[df.index > display_start]
        return df

    def add_last_label(fig, df, ycol: str, row: int, col: int,
                       kind: str = "level", scale: str | None = None):
        if df.empty or not df[ycol].notna().any():
            return
        last = df.dropna(subset=[ycol]).iloc[-1]
        x = last["Date"]
        y = float(last[ycol])

        if kind == "pct":
            txt = f"{y:.1f}%"
        else:
            if scale == "k":
                txt = f"{y/1_000:,.0f}k"
            else:
                txt = f"{y:,.0f}"

        fig.add_annotation(
            x=x, y=y, text=txt,
            showarrow=True, arrowhead=2, ax=25, ay=-25,
            row=row, col=col
        )

    # ------------------------
    # Household survey (display since 2005; computed on full history)
    # ------------------------
    unrate = make_level_df_full_then_filter("UNRATE", "Unemployment Rate (%)", display_start=UNRATE_START_DATE)
    part   = make_level_df_full_then_filter("CIVPART", "Participation Rate (%)", display_start=CIVPART_START_DATE)

    # ------------------------
    # Claims: FULL history -> compute 12w MA -> THEN filter display since 2022
    # ------------------------
    ic_full = load_fred_series("ICSA").to_frame("Initial Claims")
    ic_full["Date"] = ic_full.index
    ic_full["12w MA"] = ic_full["Initial Claims"].rolling(window=12).mean()
    ic = ic_full[ic_full.index > CLAIMS_START_DATE]

    cc = make_level_df_full_then_filter("CCSA", "Continued Claims", display_start=CLAIMS_START_DATE)

    # ------------------------
    # JOLTS (full history, no filter)
    # ------------------------
    jol = make_level_df_full_then_filter("JTSJOL", "Job Openings (ths)", display_start=None)
    hir = make_level_df_full_then_filter("JTSHIR", "Hires rate (%)", display_start=None)
    qur = make_level_df_full_then_filter("JTSQUR", "Quits rate (%)", display_start=None)
    ldr = make_level_df_full_then_filter("JTSLDR", "Layoffs & discharges rate (%)", display_start=None)

    # ------------------------
    # Figure (stacked)
    # ------------------------
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
        rows=8, cols=1, shared_xaxes=False,
        subplot_titles=titles, vertical_spacing=0.05
    )

    # 1) UNRATE
    fig.add_trace(go.Scatter(x=unrate["Date"], y=unrate["Unemployment Rate (%)"], mode="lines"), row=1, col=1)
    fig.update_yaxes(ticksuffix="%", row=1, col=1)
    add_last_label(fig, unrate, "Unemployment Rate (%)", row=1, col=1, kind="pct")

    # 2) CIVPART
    fig.add_trace(go.Scatter(x=part["Date"], y=part["Participation Rate (%)"], mode="lines"), row=2, col=1)
    fig.update_yaxes(ticksuffix="%", row=2, col=1)
    add_last_label(fig, part, "Participation Rate (%)", row=2, col=1, kind="pct")

    # 3) Initial claims (level + 12w MA computed on full history)
    fig.add_trace(go.Scatter(x=ic["Date"], y=ic["Initial Claims"], mode="lines"), row=3, col=1)
    fig.add_trace(go.Scatter(x=ic["Date"], y=ic["12w MA"], mode="lines"), row=3, col=1)
    add_last_label(fig, ic, "Initial Claims", row=3, col=1, kind="level", scale="k")

    # 4) Continued claims
    fig.add_trace(go.Scatter(x=cc["Date"], y=cc["Continued Claims"], mode="lines"), row=4, col=1)
    add_last_label(fig, cc, "Continued Claims", row=4, col=1, kind="level", scale="k")

    # 5) Job openings (ths) — last label as X.XM
    fig.add_trace(go.Scatter(x=jol["Date"], y=jol["Job Openings (ths)"], mode="lines"), row=5, col=1)
    if not jol.empty and jol["Job Openings (ths)"].notna().any():
        last = jol.dropna(subset=["Job Openings (ths)"]).iloc[-1]
        fig.add_annotation(
            x=last["Date"],
            y=float(last["Job Openings (ths)"]),
            text=f"{float(last['Job Openings (ths)'])/1000:.1f}M",
            showarrow=True, arrowhead=2, ax=25, ay=-25,
            row=5, col=1
        )

    # 6) Hires rate
    fig.add_trace(go.Scatter(x=hir["Date"], y=hir["Hires rate (%)"], mode="lines"), row=6, col=1)
    fig.update_yaxes(ticksuffix="%", row=6, col=1)
    add_last_label(fig, hir, "Hires rate (%)", row=6, col=1, kind="pct")

    # 7) Quits rate
    fig.add_trace(go.Scatter(x=qur["Date"], y=qur["Quits rate (%)"], mode="lines"), row=7, col=1)
    fig.update_yaxes(ticksuffix="%", row=7, col=1)
    add_last_label(fig, qur, "Quits rate (%)", row=7, col=1, kind="pct")

    # 8) Layoffs rate
    fig.add_trace(go.Scatter(x=ldr["Date"], y=ldr["Layoffs & discharges rate (%)"], mode="lines"), row=8, col=1)
    fig.update_yaxes(ticksuffix="%", range=[0, 2.5], row=8, col=1)
    add_last_label(fig, ldr, "Layoffs & discharges rate (%)", row=8, col=1, kind="pct")

    # Layout
    fig.update_layout(
        title="U.S. Job Market — Household Survey (since 2005), Claims (post-2022), and JOLTS (full history)",
        template="plotly_white",
        height=1750,
        margin=dict(l=60, r=30, t=70, b=40),
        showlegend=False,
        # legend=dict(orientation="h", y=-0.05),  # enable later if needed
    )

    return fig


# ============================================================
# 3️⃣ Graphique du CPI US
# ============================================================
from plotly.subplots import make_subplots
import plotly.graph_objects as go

def generate_cpi_chart():
    """
    EXACTLY your logic:
    - Fetch FULL history
    - Compute YoY (12m % change) on FULL history
    - Compute 3m annualized on FULL history (headline + core)
    - THEN filter df after the chosen display date
    - Stacked, single-column panels
    - Last-release annotation on key series
    - Legend ON and placed BETWEEN panel 1 and panel 2 (global Plotly legend)
    """

    START_MAIN = "2015-08-01"

    # -------------------------
    # Helpers (your logic)
    # -------------------------
    def yoy_df(series_id: str, name: str):
        # 1) full history
        s = load_fred_series(series_id)  # pd.Series
        df = s.to_frame(name)
        # 2) compute YoY on full history
        df = df.pct_change(periods=12)
        # 3) drop first 12 NaNs (your tail(-12))
        df = df.iloc[12:]
        return df

    def ann3m_df(series_id: str, name: str):
        # 1) full history
        s = load_fred_series(series_id)
        df = s.to_frame(name)
        # 2) compute 3m annualized on full history
        df = df.pct_change(periods=3) * 4
        # 3) drop first 3 NaNs (your tail(-3))
        df = df.iloc[3:]
        return df

    def add_last_label_pct(fig, df, ycol, row, col, fmt="{:.1f}%"):
        """
        df contains rates as decimals (e.g., 0.027 for 2.7%)
        -> display as percent.
        """
        if df.empty or not df[ycol].notna().any():
            return
        last = df.dropna(subset=[ycol]).iloc[-1]
        x = last["Date"]
        y = float(last[ycol])
        fig.add_annotation(
            x=x, y=y,
            text=fmt.format(y * 100),
            showarrow=True,
            arrowhead=2,
            ax=25, ay=-25,
            row=row, col=col
        )

    # -------------------------
    # Build YoY components (full history -> YoY)
    # -------------------------
    CPI_yoy        = yoy_df("CPIAUCSL", "CPI")
    CoreCPI_yoy    = yoy_df("CPILFESL", "Core CPI")
    Services_yoy   = yoy_df("CUSR0000SASLE", "Services CPI")
    Goods_yoy      = yoy_df("CUUR0000SACL1E", "Goods CPI")
    Foods_yoy      = yoy_df("CPIUFDSL", "Foods CPI")
    Energy_yoy     = yoy_df("CPIENGSL", "Energy CPI")

    Shelter_yoy      = yoy_df("CUSR0000SAH1", "Shelter CPI")
    MedicalSvc_yoy   = yoy_df("CUSR0000SAM2", "Medical Svc CPI")
    TransportSvc_yoy = yoy_df("CUUR0000SAS4", "Transport Svc CPI")
    EduCommSvc_yoy   = yoy_df("CPIEDUSL", "Edu Comm Svc CPI")
    RecreationSvc_yoy = yoy_df("CPIRECSL", "Recreation Svc CPI")
    OtherSvc_yoy     = yoy_df("CPIOGSSL", "Other Svc CPI")

    # Merge all YoY into one DF (index-aligned like your code)
    df = CPI_yoy.copy()
    for d in [
        CoreCPI_yoy, Services_yoy, Goods_yoy, Foods_yoy, Energy_yoy,
        Shelter_yoy, MedicalSvc_yoy, TransportSvc_yoy, EduCommSvc_yoy,
        RecreationSvc_yoy, OtherSvc_yoy
    ]:
        df = df.merge(d, left_index=True, right_index=True)

    df["Date"] = df.index

    # -------------------------
    # 3m annualized (headline + core) (full history -> 3m ann)
    # -------------------------
    CPI_3m_ann  = ann3m_df("CPIAUCSL", "CPI 3m ann")
    Core_3m_ann = ann3m_df("CPILFESL", "Core CPI 3m ann")

    df3m = CPI_3m_ann.merge(Core_3m_ann, left_index=True, right_index=True)
    df3m["Date"] = df3m.index

    # -------------------------
    # Display filters (AFTER calc, per your logic)
    # -------------------------
    df_main = df[df.index > START_MAIN].copy()
    df_svc  = df[df.index > START_MAIN].copy()
    df_3m   = df3m[df3m.index > START_MAIN].copy()

    # -------------------------
    # Plot (stacked, single column)
    # -------------------------
    fig = make_subplots(
        rows=3,
        cols=1,
        shared_xaxes=False,
        subplot_titles=(
            "US CPI — YoY (headline/core + major buckets) [display since 2015-08-01]",
            "US Core Services CPI — YoY breakdown [display since 2015-08-01]",
            "US CPI — 3m annualized (headline vs core) [display since 2015-08-01]",
        ),
        vertical_spacing=0.08
    )

    # --- Panel 1: CPI buckets ---
    for col in ["CPI", "Core CPI", "Services CPI", "Goods CPI", "Foods CPI"]:
        fig.add_trace(
            go.Scatter(x=df_main["Date"], y=df_main[col], mode="lines", name=col),
            row=1, col=1
        )
    add_last_label_pct(fig, df_main, "CPI", row=1, col=1)

    # --- Panel 2: Core services breakdown ---
    for col in [
        "Services CPI", "Shelter CPI", "Medical Svc CPI", "Transport Svc CPI",
        "Edu Comm Svc CPI", "Recreation Svc CPI", "Other Svc CPI"
    ]:
        fig.add_trace(
            go.Scatter(x=df_svc["Date"], y=df_svc[col], mode="lines", name=col),
            row=2, col=1
        )
    add_last_label_pct(fig, df_svc, "Services CPI", row=2, col=1)

    # --- Panel 3: 3m annualized ---
    for col in ["CPI 3m ann", "Core CPI 3m ann"]:
        fig.add_trace(
            go.Scatter(x=df_3m["Date"], y=df_3m[col], mode="lines", name=col),
            row=3, col=1
        )
    add_last_label_pct(fig, df_3m, "CPI 3m ann", row=3, col=1)

    # y-axis formatting: show % on all panels
    for r in [1, 2, 3]:
        fig.update_yaxes(ticksuffix="%", row=r, col=1)

    # -------------------------
    # Layout: legend BETWEEN panel 1 and 2
    # -------------------------
    fig.update_layout(
        title="U.S. CPI Dashboard (YoY + 3m annualized) — rolling computed on full history, then filtered",
        template="plotly_white",
        height=1600,
        margin=dict(l=60, r=30, t=70, b=40),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="middle",
            y=0.50,          # ✅ between panel 1 and 2
            xanchor="center",
            x=0.5,
            font=dict(size=11)
        ),
    )

    return fig
