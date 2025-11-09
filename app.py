import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd

# ⚙️ Config de la page
st.set_page_config(
    page_title="Mon mini chat bot en Python",
    page_icon="💬",
    layout="centered"
)

# 🌈 Style bulles de chat
st.markdown(
    """
    <style>
    .chat-container {
        max-width: 700px;
        margin: auto;
    }
    .message {
        padding: 0.5rem 0;
        display: flex;
    }
    .user-bubble {
        margin-left: auto;
        background-color: #0f766e;
        color: white;
        padding: 0.6rem 0.9rem;
        border-radius: 1rem 0 1rem 1rem;
        max-width: 80%;
        font-size: 0.95rem;
    }
    .bot-bubble {
        margin-right: auto;
        background-color: #e5e7eb;
        color: #111827;
        padding: 0.6rem 0.9rem;
        border-radius: 0 1rem 1rem 1rem;
        max-width: 80%;
        font-size: 0.95rem;
    }
    .username {
        font-size: 0.70rem;
        margin-bottom: 0.15rem;
        color: #6b7280;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# 🧊 Charge les données SPX une seule fois (cache Streamlit)
@st.cache_data(ttl=3600)  # cache 1 heure par exemple
def load_spx_close():
    data = yf.download("^GSPC", period="3mo", interval="1d")
    if data.empty:
        return None

    # Au cas où un jour tu passes plusieurs tickers
    if isinstance(data.columns, pd.MultiIndex):
        close = data["Close"]["^GSPC"]
    else:
        close = data["Close"]

    return close


# --------------------------------------------------
# 🧊 Load and cache SPX OHLC data (3 months)
# --------------------------------------------------
@st.cache_data(ttl=3600)
def load_spx_ohlc():
    """Download and prepare OHLC data for SPX (3 months)."""
    tickers = ['^GSPC', '^STOXX50E', '^RUT']
    data = yf.download(tickers, period="3mo", interval="1d", auto_adjust=False)

    # Extract SPX OHLC cleanly
    ohlc = data.xs('^GSPC', level=1, axis=1)[["Open", "High", "Low", "Close"]]
    return ohlc
def load_indices_ohlc():
    """Download and prepare OHLC data for SPX / SX5E / RUT (3 months)."""
    tickers = {
        "SPX": "^GSPC",
        "SX5E": "^STOXX50E",
        "RUT": "^RUT",
        "NDX" : "^IXIC",
        "HSI" :"^HSI",
        "CAC" : "^FCHI"
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

# --------------------------------------------------
# 📈 Generate Plotly OHLC figure (self-contained)
# --------------------------------------------------

def generate_ohlc(ohlc_df: pd.DataFrame, name: str = "SPX"):
    """Generate an interactive OHLC Plotly figure from an OHLC DataFrame."""
    # Détection des jours ouvrés manquants (fériés)
    full_index = pd.date_range(start=ohlc_df.index.min(), end=ohlc_df.index.max(), freq="B")
    missing = full_index.difference(ohlc_df.index)
    # --- Compute performance ---
    last_close = ohlc_df["Close"].iloc[-1]
    prev_close = ohlc_df["Close"].iloc[-2] if len(ohlc_df) > 1 else last_close
    start_close = ohlc_df["Close"].iloc[0]

    perf_1d = (last_close / prev_close - 1) * 100
    perf_3m = (last_close / start_close - 1) * 100

    perf_1d_str = f"{perf_1d:+.1f}%"
    perf_3m_str = f"{perf_3m:+.1f}%"
    
    fig = go.Figure(
        data=go.Ohlc(
            x=ohlc_df.index,
            open=ohlc_df["Open"],
            high=ohlc_df["High"],
            low=ohlc_df["Low"],
            close=ohlc_df["Close"],
            name=name
        )
    )

    fig.update_xaxes(
        rangebreaks=[
            dict(bounds=["sat", "mon"]),
            dict(values=missing)
        ],
        tickformat="%b %d",   # ex: Sep 05
        tickangle=-45,        # penché pour gagner de la place
        nticks=8              # plus de repères de date
    )

    fig.update_layout(
        title=f"{name} – 1d: {perf_1d_str} • 3m: {perf_3m_str}",
        xaxis_title="Date",
        yaxis_title="Index level",
        xaxis_rangeslider_visible=False,
        template="plotly_white",
        height=350,                       # plus compact pour mobile
        margin=dict(l=40, r=10, t=40, b=60)
        # ❌ pas de width ici → use_container_width=True fera le job
    )

    return fig


# 🧠 Logique du bot : renvoie (texte, fig)
def repondre(question: str):
    q = question.lower().strip()
    q_upper = q.upper()
    fig = None  # par défaut, pas de graphique

    if q == "":
        return "Tu n’as rien écrit 😅", fig

    if "bonjour" in q or "salut" in q or "hello" in q:
        return "Salut 👋 ! Comment ça va aujourd’hui ?", fig

    if "2+2" in q or "2 + 2" in q:
        return "Facile ! 2 + 2 = 4 🔢", fig

    if "comment tu t'appelles" in q or "comment tu t appelles" in q:
        return "Je suis ton petit bot en Python 🤖.", fig

    if "merci" in q:
        return "Avec plaisir 😄 !", fig


    # 🟢 SPX case → load cached OHLC data
    
    # 🔎 Cherche un des tickers dans la question
    for code in ["SPX", "SX5E", "RUT","NDX","CAC","HSI"]:
        if code in q_upper:
            try:
                all_ohlc = load_indices_ohlc()
                ohlc = all_ohlc[code]
                fig = generate_ohlc(ohlc, name=code)
                #st.plotly_chart(fig, use_container_width=True)
                return f"last 3m {code} chart 📈", fig
            except Exception as e:
                return f"Erreur lors du chargement de {code} : {e}", None

# 📌 Historique des messages (texte + graph)
# On stocke des tuples (type, contenu) avec type ∈ {"user", "bot", "plot"}
if "messages" not in st.session_state:
    st.session_state.messages = []

st.markdown("<div class='chat-container'>", unsafe_allow_html=True)

st.title("💬 Mon mini chat bot en Python")
st.write("Pose une question et je te réponds. Tape « SPX » pour voir un graphique sur 1 mois 📈")

# 📝 Saisie utilisateur
user_input = st.text_input("Écris ta question ici :")
envoyer = st.button("Envoyer")

# 👉 Quand on envoie un message
if envoyer and user_input.strip() != "":
    # 1. message utilisateur
    st.session_state.messages.append(("user", user_input))

    # 2. réponse + éventuel graphique
    reply_text, fig = repondre(user_input)

    # 3. texte bot
    st.session_state.messages.append(("bot", reply_text))

    # 4. graphique dans l’historique si présent
    if fig is not None:
        st.session_state.messages.append(("plot", fig))

# 🧾 Affichage de tout l'historique (texte + graph)
# 🧾 Affichage de tout l'historique (texte + graph)
for i, (msg_type, content) in enumerate(st.session_state.messages):  # 👈 ajoute un index
    if msg_type == "user":
        st.markdown(
            f"""
            <div class="message">
                <div class="user-bubble">
                    <div class="username">Toi</div>
                    {content}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    elif msg_type == "bot":
        st.markdown(
            f"""
            <div class="message">
                <div class="bot-bubble">
                    <div class="username">Bot</div>
                    {content}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    elif msg_type == "plot":
        # 🔑 Ajoute une clé unique pour chaque graphique
        st.plotly_chart(content, use_container_width=True, key=f"plot_{i}")

st.markdown("</div>", unsafe_allow_html=True)
