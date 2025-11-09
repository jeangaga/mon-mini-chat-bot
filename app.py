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

def load_spx_ohlc():
    """Download and prepare OHLC data for SPX (3 months)"""
    tickers = ['^GSPC', '^STOXX50E', '^RUT']
    data = yf.download(tickers, period="3mo", interval="1d", auto_adjust=False)

    # Extract SPX OHLC cleanly
    ohlc = data.xs('^GSPC', level=1, axis=1)[["Open", "High", "Low", "Close"]]

    # Build business-day index and compute missing (holidays etc.)
    full_index = pd.date_range(start=ohlc.index.min(), end=ohlc.index.max(), freq="B")
    missing = full_index.difference(ohlc.index)

    # Create OHLC chart
    fig = go.Figure(
        data=go.Ohlc(
            x=ohlc.index,
            open=ohlc["Open"],
            high=ohlc["High"],
            low=ohlc["Low"],
            close=ohlc["Close"],
            name="SPX"
        )
    )

    fig.update_xaxes(
        rangebreaks=[
            dict(bounds=["sat", "mon"]),
            dict(values=missing)  # remove holidays
        ]
    )

    fig.update_layout(
        title="S&P 500 (SPX) – OHLC over the last 3 months (no gaps)",
        xaxis_title="Date",
        yaxis_title="Index level",
        xaxis_rangeslider_visible=False,
        template="plotly_white",
        height=500,
        width=900
    )

    return ohlc, fig


# 🧠 Logique du bot : renvoie (texte, fig)
def repondre(question: str):
    q = question.lower().strip()
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

    # 🟢 Cas spécial SPX : on utilise les données cachées
    if "spxold" in q:
        close = load_spx_close()
        if close is None:
            return "Je n’ai pas réussi à récupérer les données du SPX 🤔.", fig

        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=close.index,
                y=close.values,   # vecteur 1D
                mode="lines",
                name="SPX"
            )
        )
        fig.update_layout(
            title="SPX – Dernier mois (clôture quotidienne)",
            xaxis_title="Date",
            yaxis_title="Close"
        )

        return "Voici le graphique du SPX sur le dernier mois 📈", fig
    # 🟢 SPX case → load cached OHLC data
    if "spx" in q:
        try:
            ohlc, fig = load_spx_ohlc()
            return "last 3m SPX chart 📈", fig
        except Exception as e:
            return f"Erreur lors du chargement du SPX : {e}", fig
    # Réponse par défaut
    return "Je ne sais pas encore répondre à ça 🤔, mais tu peux modifier mon code pour m’apprendre !", fig


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
for msg_type, content in st.session_state.messages:
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
        st.plotly_chart(content, use_container_width=True)

st.markdown("</div>", unsafe_allow_html=True)
