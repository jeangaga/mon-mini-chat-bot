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

from plotly.subplots import make_subplots
import requests
import re
import json
from datetime import date, timedelta
import html
from functions.load_comments import load_stock_comment, load_index_comment, load_macro_note, load_eur_macro_comment,load_live_macro_block,render_live_macro_block
from functions.fred_tools import generate_labor_chart,generate_jobs_chart
from functions.yahoo_tools import load_indices_ohlc, generate_ohlc

listTickerEquity = [
    # --- Indices ---
    "SPX", "SX5E", "RUT", "NDX", "HSI", "CAC",

    # --- MAG7 + Tech ---
    "META", "AAPL", "AMZN", "GOOGL", "MSFT", "NVDA", "TSLA", "PLTR", "AVGO",

    # --- Consumer / Financials ---
    "WMT", "TGT", "HD", "JPM",
]

listIndexCodes = ["SPX", "SX5E", "RUT", "NDX", "HSI", "CAC"]
# === 2️⃣ Define your Yahoo Finance mapping ===
tickers = {
    # --- Indices ---
    "SPX": "^GSPC",
    "SX5E": "^STOXX50E",
    "RUT": "^RUT",
    "NDX": "^IXIC",
    "HSI": "^HSI",
    "CAC": "^FCHI",

    # --- Hyperscalers / Platforms ---
    "META": "META",
    "AAPL": "AAPL",
    "AMZN": "AMZN",
    "GOOGL": "GOOGL",
    "MSFT": "MSFT",
    "ORCL": "ORCL",

    # --- Core AI Compute / Silicon ---
    "NVDA": "NVDA",
    "AVGO": "AVGO",
    "AMD":  "AMD",
    "TSM":  "TSM",
    "ASML": "ASML",

    # --- Networking / Optics ---
    "ANET": "ANET",
    "CSCO": "CSCO",
    "MRVL": "MRVL",
    "LITE": "LITE",
    "COHR": "COHR",

    # --- AI Servers / Systems ---
    "SMCI": "SMCI",
    "CLS":  "CLS",

    # --- Consumer / Financials (AI Beneficiaries) ---
    "WMT": "WMT",
    "TGT": "TGT",
    "HD":  "HD",
    "JPM": "JPM",

    # --- Optional / Thematic ---
    "PLTR": "PLTR",
    "TSLA": "TSLA",
}

# ⚙️ Config de la page
st.set_page_config(
    page_title="JGM mini chat bot",
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
#@st.cache_data(ttl=3600)  # cache 1 heure par exemple


# 🧠 Logique du bot : renvoie (texte, fig)
def repondre(question: str):
    q = question.lower().strip()
    q_lower = q.lower()
    q_upper = q.upper()
    fig = None  # par défaut, pas de graphique

    if q == "":
        return "Tu n’as rien écrit 😅", fig

    if "bonjour" in q or "salut" in q or "hello" in q:
        return "Salut 👋 ! Comment ça va aujourd’hui ?", fig



    if "merci" in q:
        return "Avec plaisir 😄 !", fig
        


    # 🟣 Commande spéciale MACROUS → charge la dernière note US macro depuis GitHub
    #if q_upper == "MACROEUR":
    #    comment_text = load_eur_macro_comment()
     #   return comment_text, None

  # 🟣 Commandes spéciales MACRO<REGION>
    if q_upper.startswith("MACRO"):
        region = q_upper.replace("MACRO", "").lower()
        comment_text = load_macro_note(region)
        return comment_text, None  



    if q_upper.startswith("LIVE"):
        region = q_upper.replace("LIVE", "").lower()
        comment_text = load_live_macro_block(region)
        comment_text = render_live_macro_block(comment_text)
        return comment_text, None  
    
    # 🔎 Cherche un des tickers dans la question
    for code in listTickerEquity:
        if code in q_upper:
            try:
                all_ohlc = load_indices_ohlc()
                ohlc = all_ohlc[code]
                fig = generate_ohlc(ohlc, name=code)

                # 🔹 Charger le commentaire JSON correspondant
                if code in listIndexCodes:
                    comment_text = load_index_comment(code)
                else:
                    comment_text = load_stock_comment(code)

                # 👉 Retourne le texte et le graphique
                return comment_text, fig

            except Exception as e:
                return f"Erreur lors du chargement de {code} : {e}", None  
    # Labor Market chart
    if "nfp" in q_lower:
        fig = generate_labor_chart()
        return "U.S. Labor NFP update 📊", fig
    if "jobs" in q_lower:
        fig = generate_jobs_chart()
        return "U.S. Labor  update 📊", fig
        
# 📌 Historique des messages (texte + graph)
# On stocke des tuples (type, contenu) avec type ∈ {"user", "bot", "plot"}
if "messages" not in st.session_state:
    st.session_state.messages = []

st.markdown("<div class='chat-container'>", unsafe_allow_html=True)

st.title("💬 JGM Macro chat bot")
st.write("Enter ticker (SPX) or macro (NFP)")

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
        # Affichage simple en Streamlit, sans HTML custom
        # pour être sûr de voir tout le texte (notamment MACROUS)
        st.markdown("**Bot :**")
        st.markdown(str(content))

    elif msg_type == "plot":
        st.plotly_chart(content, use_container_width=True, key=f"plot_{i}")

    # 🔹 fine grey separator between conversation turns
    st.markdown("<hr style='margin:4px 0; border:0.5px solid #e0e0e0;'>", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

