import streamlit as st
import yfinance as yf
import plotly.express as px
import plotly.graph_objects as go
# ⚙️ Config de la page
st.set_page_config(page_title="Mon mini chat bot en Python", page_icon="💬")

# 🌈 Un peu de style pour faire des bulles de chat
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

# 🧠 Mini "IA" très simple
def repondre(question: str) -> str:
    q = question.lower().strip()

    if q == "":
        return "Tu n’as rien écrit 😅"

    if "bonjour" in q or "salut" in q or "hello" in q:
        return "Salut 👋 ! Comment ça va aujourd’hui ?"

    if "2+2" in q or "2 + 2" in q:
        return "Facile ! 2 + 2 = 4 🔢"

    if "comment tu t'appelles" in q or "comment tu t appelles" in q:
        return "Je suis ton petit bot en Python 🤖."

    if "merci" in q:
        return "Avec plaisir 😄 !"

    # 🟢 Nouveau cas : si l'utilisateur parle du SPX
    if "spx" in q:
        try:
            data = yf.download("^GSPC", period="1mo", interval="1d")
            if data.empty:
                return "Je n’ai pas réussi à récupérer les données du SPX 🤔."

            # On prend bien une série 1D
            close = data["Close"]["^GSPC"]

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
            st.plotly_chart(fig, use_container_width=True)
            return "Voici le graphique du SPX sur le dernier mois 📈"
        except Exception as e:
            return f"Erreur lors du téléchargement du SPX : {e}"

    # Réponse par défaut
    return "Je ne sais pas encore répondre à ça 🤔, mais tu peux modifier mon code pour m’apprendre !"

# 📌 Initialisation de l’historique
if "messages" not in st.session_state:
    st.session_state.messages = []

st.markdown("<div class='chat-container'>", unsafe_allow_html=True)

st.title("💬 Mon mini chat bot en Python")
st.write("Pose une question et je te réponds. Tu pourras modifier le code pour m’apprendre de nouvelles réponses 😉")

# 📝 Zone de saisie (avant l’affichage des messages)
user_input = st.text_input("Écris ta question ici :")
envoyer = st.button("Envoyer")

# 👉 Si on clique sur Envoyer, on ajoute direct aux messages
if envoyer and user_input.strip() != "":
    st.session_state.messages.append(("user", user_input))
    bot_reply = repondre(user_input)
    st.session_state.messages.append(("bot", bot_reply))

# 🧾 Affichage de l’historique (y compris le nouveau message)
for sender, text in st.session_state.messages:
    if sender == "user":
        st.markdown(
            f"""
            <div class="message">
                <div class="user-bubble">
                    <div class="username">Toi</div>
                    {text}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f"""
            <div class="message">
                <div class="bot-bubble">
                    <div class="username">Bot</div>
                    {text}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.markdown("</div>", unsafe_allow_html=True)
