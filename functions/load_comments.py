# functions/load_comments.py
import requests
from datetime import date, timedelta

# === Fonction principale pour les actions ===
def load_stock_comment(code: str):
    base_url = "https://raw.githubusercontent.com/jeangaga/mon-mini-chat-bot/main/notes/"
    found_data = None
    used_date = None

    def clean(text):
        """Nettoyage minimal + escape des $ pour éviter le mode LaTeX de Streamlit."""
        if text is None:
            return ""
        if not isinstance(text, str):
            text = str(text)
        text = text.replace("\n", " ")
        text = " ".join(text.split())
        text = text.replace("$", r"\$")
        return text

    # 🔁 cherche jusqu’à 10 jours en arrière
    for i in range(10):
        check_date = (date.today() - timedelta(days=i)).strftime("%Y%m%d")
        url = f"{base_url}stocks_daily_fundamental_feed_{check_date}.json"
        try:
            r = requests.get(url, timeout=5)
            if r.status_code == 200:
                found_data = r.json()
                used_date = check_date
                break
        except Exception:
            continue

    if not found_data:
        return f"❌ Aucun fichier de feed trouvé sur les 10 derniers jours pour {code}."

    try:
        stocks = found_data.get("stocks", [])
        stock = next((s for s in stocks if s.get("ticker", "").upper() == code.upper()), None)
        if not stock:
            return f"❌ Aucun commentaire trouvé pour {code} dans le feed du {used_date}."

        ticker = stock.get("ticker", code)
        sentiment = stock.get("sentiment_tag", "n/a")

        news = stock.get("market_news_last_5d", {}) or {}
        last_earn = stock.get("last_earnings", {}) or {}
        summary_raw = stock.get("chat_summary", "n/a")

        # Nettoyage des champs
        last_period = clean(last_earn.get("period", "n/a"))
        last_report_date = clean(last_earn.get("report_date", "n/a"))
        last_comment = clean(last_earn.get("summary_comment", "n/a"))

        key_insights = last_earn.get("key_insights", {}) or {}
        ki_lines = [f"- **{clean(k)} :** {clean(v)}" for k, v in key_insights.items()]
        key_insights_text = "\n".join(ki_lines) if ki_lines else "_Pas de key insights disponibles._"

        outlook = last_earn.get("outlook", {}) or {}
        ol_lines = [f"- **{clean(k)} :** {clean(v)}" for k, v in outlook.items()]
        outlook_text = "\n".join(ol_lines) if ol_lines else "_Pas d’outlook disponible._"

        news_summary = clean(news.get("summary_overview", ""))
        market_reaction = clean(news.get("market_reaction", ""))
        summary = clean(summary_raw)

        # Format markdown
        text = (
            f"### 🧾 **{ticker} — Résumé fondamental ({used_date})**  \n"
            f"**Sentiment :** {sentiment}  \n\n"
            f"**Derniers développements (5 derniers jours)**  \n"
            f"{news_summary}\n\n"
            f"🪙 *Réaction de marché :* {market_reaction}\n\n"
            f"**Dernier trimestre reporté :** {last_period} *(publié le {last_report_date})*  \n"
            f"{last_comment}\n\n"
            f"**Key insights :**  \n"
            f"{key_insights_text}\n\n"
            f"**Outlook :**  \n"
            f"{outlook_text}\n\n"
            f"**Synthèse JGM Chatbox :**  \n"
            f"{summary}"
        )
        return text

    except Exception as e:
        return f"Erreur lors du chargement du commentaire {code} : {e}"


# === Fonction équivalente pour les indices ===
def load_index_comment(code: str):
    url = f"https://raw.githubusercontent.com/jeangaga/mon-mini-chat-bot/main/notes/{code}.json"
    try:
        r = requests.get(url)
        if r.status_code != 200:
            return f"❌ Aucun commentaire trouvé pour {code}."
        data = r.json()
        tag_date = data.get("date", "n/a")
        close_val = data.get("close", "n/a")
        sentiment = data.get("retail_sentiment", "n/a")
        topics = ", ".join(data.get("top_topics", []))
        comment = data.get("comment", "n/a")

        return (
            f"**Dernier tag {code} ({tag_date})**  \n"
            f"📈 **Clôture :** {close_val}  \n"
            f"🧠 **Sentiment retail :** {sentiment}  \n"
            f"🔥 **Top sujets :** {topics}  \n"
            f"💬 **Commentaire :** {comment}"
        )

    except Exception as e:
        return f"Erreur lors du chargement du commentaire {code} : {e}"



import requests

 
import re

def load_us_macro_comment() -> str:
    """
    Charge la dernière note US macro depuis GitHub (US_macro_latest.txt)
    et renvoie le DERNIER bloc entre
    <<<US_MACRO_NOTE_BEGIN>>> et <<<US_MACRO_NOTE_END>>>.
    """
    url = "https://raw.githubusercontent.com/jeangaga/mon-mini-chat-bot/main/notes/US_macro_latest.txt"
    try:
        r = requests.get(url, timeout=5)
        if r.status_code != 200:
            return f"❌ Aucun commentaire US macro trouvé (HTTP {r.status_code})."
    except Exception as e:
        return f"Erreur lors du chargement du commentaire US macro : {e}"

    text = r.text

    # Tous les blocs entre les balises
    pattern = r"<<<US_MACRO_NOTE_BEGIN>>>(.*?)<<<US_MACRO_NOTE_END>>>"
    matches = re.findall(pattern, text, flags=re.S)

    if not matches:
        return "❌ Aucune balise <<<US_MACRO_NOTE_BEGIN>>> ... <<<US_MACRO_NOTE_END>>> trouvée dans US_macro_latest.txt."

    # On prend simplement le DERNIER bloc, même s'il est vide
    last_block = matches[-1].strip()
    return last_block

def load_eur_macro_comment() -> str:
    """
    Charge la dernière note US macro depuis GitHub (US_macro_latest.txt)
    et renvoie le DERNIER bloc entre
    <<<US_MACRO_NOTE_BEGIN>>> et <<<US_MACRO_NOTE_END>>>.
    """
    url = "https://raw.githubusercontent.com/jeangaga/mon-mini-chat-bot/main/notes/EUR_MACRO_NOTE.txt"
    try:
        r = requests.get(url, timeout=5)
        if r.status_code != 200:
            return f"❌ Aucun commentaire US macro trouvé (HTTP {r.status_code})."
    except Exception as e:
        return f"Erreur lors du chargement du commentaire EUR macro : {e}"

    text = r.text

    # Tous les blocs entre les balises
    pattern = r"<<<EUR_MACRO_NOTE_BEGIN>>>(.*?)<<<EUR_MACRO_NOTE_END>>>"
    matches = re.findall(pattern, text, flags=re.S)

    if not matches:
        return "❌ Aucune balise <<<EUR_MACRO_NOTE_BEGIN>>> ... <<<EUR_MACRO_NOTE_END>>> trouvée dans US_macro_latest.txt."

    # On prend simplement le DERNIER bloc, même s'il est vide
    last_block = matches[-1].strip()
    return last_block

