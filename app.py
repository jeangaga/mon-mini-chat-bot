"""
=====================================================================
💬 MON MINI CHAT BOT STREAMLIT — VERSION INDICES BOURSIERS (SPX, SX5E, RUT, etc.)
=====================================================================

📌 OBJECTIF
-----------
Ce programme crée une application Streamlit interactive où l'utilisateur
peut dialoguer avec un "bot" capable de répondre à des messages simples
et d’afficher des graphiques de marchés boursiers (indices) à la demande.

Exemple :
    - "SPX"   → affiche le graphique OHLC du S&P 500 sur 3 mois
    - "SX5E"  → affiche le graphique EuroStoxx 50 sur 3 mois
    - "RUT"   → affiche le graphique Russell 2000
    - "NDX"   → Nasdaq 100
    - "HSI"   → Hang Seng
    - "CAC"   → CAC 40

L’interface est présentée comme une conversation :
les messages récents apparaissent **en haut**, l’historique **en bas**,
et chaque échange est séparé par une fine ligne grise.

---------------------------------------------------------------------
🏗️ STRUCTURE GÉNÉRALE DU CODE
---------------------------------------------------------------------

1️⃣  IMPORTS ET CONFIGURATION STREAMLIT
    - streamlit, yfinance, pandas, plotly.graph_objects
    - configuration de la page Streamlit (titre, icône, layout centré)

2️⃣  CHARGEMENT DES DONNÉES — `load_indices_ohlc()`
    - télécharge les données OHLC de plusieurs indices via Yahoo Finance
    - période : 3 derniers mois, intervalle : 1 jour
    - renvoie un dictionnaire :
        {
            "SPX": DataFrame OHLC du S&P 500,
            "SX5E": DataFrame OHLC de l’EuroStoxx 50,
            ...
        }
    - cette fonction est **mise en cache** via `@st.cache_data(ttl=3600)`
      → téléchargement limité à une fois par heure

3️⃣  GÉNÉRATION DU GRAPHIQUE — `generate_ohlc(ohlc_df, name)`
    - prend un DataFrame OHLC (issu du dictionnaire précédent)
    - calcule :
        • performance 1 jour (%)
        • performance 3 mois (%)
    - crée un graphique Plotly OHLC interactif :
        • sans week-ends ni jours fériés (via rangebreaks)
        • axe des dates propre (tickformat + angle)
    - ajoute un titre dynamique :
        ex. "SPX – 1d: +0.8% • 3m: +4.9%"

4️⃣  LOGIQUE DE RÉPONSE — `repondre(question)`
    - analyse la question saisie par l'utilisateur
    - réponses textuelles de base :
        • "bonjour", "merci", "hello" → réponse amicale
    - détection d’un ticker dans ["SPX", "SX5E", "RUT", "NDX", "HSI", "CAC"]
        → appelle `load_indices_ohlc()`
        → sélectionne le bon DataFrame
        → appelle `generate_ohlc()` pour produire le graphique
        → renvoie le texte et la figure à afficher
    - renvoie par défaut "Je ne sais pas encore répondre à ça 🤔"

5️⃣  GESTION DE L’HISTORIQUE — `st.session_state.messages`
    - stocke les messages dans une liste de tuples :
        ("user", texte) | ("bot", texte) | ("plot", fig)
    - permet de conserver l’historique après chaque interaction
    - les figures Plotly ont une clé unique (`key=f"plot_{i}"`)
      pour éviter l’erreur StreamlitDuplicateElementId

6️⃣  AFFICHAGE (BOUCLE DE CHAT)
    - les messages sont affichés **en ordre inverse** (plus récents en haut)
    - format HTML léger (bulles vertes pour l’utilisateur, grises pour le bot)
    - une fine ligne grise `<hr>` sépare chaque échange
    - les graphiques s’affichent en dessous de chaque réponse du bot

---------------------------------------------------------------------
📈 POINTS TECHNIQUES IMPORTANTS
---------------------------------------------------------------------

✅ `rangebreaks` sur l’axe X
   → supprime les week-ends et jours fériés
   → timeline continue de trading

✅ `@st.cache_data(ttl=3600)`
   → évite de recharger les données à chaque interaction
   → rafraîchit automatiquement après 1h

✅ Clé unique dans `st.plotly_chart()`
   → `key=f"plot_{i}"` pour éviter les doublons d’éléments Streamlit

✅ Design responsive
   → `use_container_width=True` permet une adaptation mobile fluide
   → graphique plus compact (`height=350`) pour téléphone

---------------------------------------------------------------------
🔧 EXTENSIONS POSSIBLES
---------------------------------------------------------------------
- Ajouter des actions individuelles (AAPL, TSLA, etc.)
- Ajouter un menu déroulant de tickers
- Ajouter une mini-carte des performances globales
- Ajouter le dernier prix "spot" ou la variation journalière en annotation
- Ajouter la détection automatique de phrases du type “montre-moi le CAC”

---------------------------------------------------------------------
🧠 AUTEUR -- JGM
---------------------------------------------------------------------
Code rédigé et documenté avec l’aide de ChatGPT (GPT-5)
pour un usage éducatif, analytique et personnel.

=====================================================================
"""



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
    """Generate an interactive OHLC Plotly figure from a single-index OHLC DataFrame."""

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
st.write("Pose une question et je te réponds. Tape « SPX » pour voir un graphique sur 3 mois 📈")

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
# 💬 Affichage inversé : les nouveaux messages en haut
st.markdown("<div class='chat-container' style='display:flex; flex-direction:column-reverse;'>", unsafe_allow_html=True)

for i, (msg_type, content) in enumerate(reversed(st.session_state.messages)):
    if msg_type == "user":
        st.markdown(
            f"""
            <div class="message" style="margin-top:8px; margin-bottom:8px;">
                <div class="user-bubble" style="background-color:#DCF8C6; border-radius:12px; padding:8px;">
                    <strong>Toi :</strong> {content}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    elif msg_type == "bot":
        st.markdown(
            f"""
            <div class="message" style="margin-top:8px; margin-bottom:8px;">
                <div class="bot-bubble" style="background-color:#F1F0F0; border-radius:12px; padding:8px;">
                    <strong>Bot :</strong> {content}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    elif msg_type == "plot":
        st.plotly_chart(content, use_container_width=True, key=f"plot_{i}")

    # 🔹 fine grey separator between conversation turns
    st.markdown("<hr style='margin:4px 0; border:0.5px solid #e0e0e0;'>", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

