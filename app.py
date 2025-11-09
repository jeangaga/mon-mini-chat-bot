import streamlit as st

# ⚙️ Config de la page
st.set_page_config(page_title="Mon mini chat bot", page_icon="💬")

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

    # Réponse par défaut
    return "Je ne sais pas encore répondre à ça 🤔, mais tu peux modifier mon code pour m’apprendre !"

# 📌 Initialisation de l’historique
if "messages" not in st.session_state:
    st.session_state.messages = []

st.markdown("<div class='chat-container'>", unsafe_allow_html=True)

st.title("💬 Mon mini chat bot en Python")
st.write("Pose une question et je te réponds. Tu pourras modifier le code pour m’apprendre de nouvelles réponses 😉")

# 🧾 Affichage de l’historique
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

# 📝 Zone de saisie
user_input = st.text_input("Écris ta question ici :", key="input")

col1, col2 = st.columns([1, 4])
with col1:
    envoyer = st.button("Envoyer")

if envoyer and user_input.strip() != "":
    # Ajoute message utilisateur
    st.session_state.messages.append(("user", user_input))

    # Génère la réponse
    bot_reply = repondre(user_input)
    st.session_state.messages.append(("bot", bot_reply))

    # Vide la case texte
    st.session_state.input = ""

    # Force le rafraîchissement pour voir les bulles ajoutées
    st.experimental_rerun()

st.markdown("</div>", unsafe_allow_html=True)
