# functions/load_comments.py
import requests
import re
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
    Charge la note EUR macro depuis GitHub (EUR_MACRO_NOTE.txt)
    et renvoie le PREMIER bloc entre
    <<<EUR_MACRO_NOTE_BEGIN>>> et <<<EUR_MACRO_NOTE_END>>>.
    """
    url = "https://raw.githubusercontent.com/jeangaga/mon-mini-chat-bot/main/notes/EUR_MACRO_NOTE.txt"

    try:
        r = requests.get(url, timeout=5)
        if r.status_code != 200:
            return f"❌ Aucun commentaire EUR macro trouvé (HTTP {r.status_code})."
    except Exception as e:
        return f"Erreur lors du chargement du commentaire EUR macro : {e}"

    text = r.text

    pattern = r"<<<EUR_MACRO_NOTE_BEGIN>>>(.*?)<<<EUR_MACRO_NOTE_END>>>"
    matches = re.findall(pattern, text, flags=re.S)

    if not matches:
        return (
            "❌ Aucune balise <<<EUR_MACRO_NOTE_BEGIN>>> ... "
            "<<<EUR_MACRO_NOTE_END>>> trouvée dans le fichier EUR macro."
        )

    first_block = matches[0].strip()
    return first_block

import re
import requests

def load_macro_note(region: str) -> str:
    """
    Load the FIRST macro note block for a given region from GitHub.

    - region examples: "eur", "jpy", "usd", "mxn", "zar" (case-insensitive)
    - file: <REGION>_MACRO_NOTE.txt (e.g., EUR_MACRO_NOTE.txt)
    - block markers:
        <<<EUR_MACRO_NOTE_BEGIN>>> ... <<<EUR_MACRO_NOTE_END>>>
        <<<JPY_MACRO_NOTE_BEGIN>>> ... <<<JPY_MACRO_NOTE_END>>>
    Returns: the first matched block (stripped), or an error message.
    """

    reg = region.strip().upper()
    if not reg:
        return "❌ Région invalide (vide)."

    base_url = "https://raw.githubusercontent.com/jeangaga/mon-mini-chat-bot/main/notes"
    filename = f"{reg}_MACRO_NOTE.txt"
    url = f"{base_url}/{filename}"

    begin_tag = f"<<<{reg}_MACRO_NOTE_BEGIN>>>"
    end_tag = f"<<<{reg}_MACRO_NOTE_END>>>"

    try:
        r = requests.get(url, timeout=5)
        if r.status_code != 200:
            return f"❌ Aucun fichier macro trouvé pour {reg} (HTTP {r.status_code}) : {filename}"
    except Exception as e:
        return f"Erreur lors du chargement de la note macro {reg} : {e}"

    text = r.text

    # Escape tags in case they ever contain regex-significant chars
    pattern = re.escape(begin_tag) + r"(.*?)" + re.escape(end_tag)
    matches = re.findall(pattern, text, flags=re.S)

    if not matches:
        return (
            f"❌ Balises introuvables dans {filename} : "
            f"{begin_tag} ... {end_tag}"
        )

    # FIRST block in file order
    return matches[0].strip()

def load_live_macro_block(region: str) -> str:
    """
    Load the FIRST LIVE macro block for a given region from GitHub.

    - region examples: "eur", "jpy", "usd", "mxn", "zar" (case-insensitive)
    - file: <REGION>_MACRO_NOTE.txt (e.g., EUR_MACRO_NOTE.txt)
    - block markers:
        <<LIVE_EUR_MACRO_BEGIN>> ... <<LIVE_EUR_MACRO_END>>
        <<LIVE_JPY_MACRO_BEGIN>> ... <<LIVE_JPY_MACRO_END>>

    Returns:
        - first matched LIVE block (stripped)
        - or a clear error message
    """

    reg = region.strip().upper()
    if not reg:
        return "❌ Invalid region (empty)."

    base_url = "https://raw.githubusercontent.com/jeangaga/mon-mini-chat-bot/main/notes"
    filename = f"{reg}_MACRO_NOTE.txt"
    url = f"{base_url}/{filename}"

    begin_tag = f"<<LIVE_{reg}_MACRO_BEGIN>>"
    end_tag = f"<<LIVE_{reg}_MACRO_END>>"

    try:
        r = requests.get(url, timeout=5)
        if r.status_code != 200:
            return f"❌ Macro file not found for {reg} (HTTP {r.status_code}): {filename}"
    except Exception as e:
        return f"❌ Error loading LIVE macro note for {reg}: {e}"

    text = r.text

    pattern = re.escape(begin_tag) + r"(.*?)" + re.escape(end_tag)
    matches = re.findall(pattern, text, flags=re.S)

    if not matches:
        return (
            f"❌ LIVE macro block not found in {filename}: "
            f"{begin_tag} ... {end_tag}"
        )

    # FIRST block in file order
    return matches[0].strip()

SEP_EQ_RE = re.compile(r"^=+$")
SEP_DASH_RE = re.compile(r"^-+$")

def render_live_macro_block(text: str) -> None:
    """
    Render a LIVE macro block nicely in Streamlit WITHOUT changing the source text.
    Designed for your ASCII HF notebook format:
      - top title lines (e.g., 'US MACRO — LIVE WEEK VIEW ...')
      - STATUS line
      - day headers like 'MONDAY 05 JAN — RELEASED' / '... — LIVE (PREVIEW)'
      - indicator headers in ALL CAPS
      - separator lines made of ==== or ----
    """
    if not text or text.strip().startswith("❌"):
        st.error(text if text else "❌ Empty LIVE macro block.")
        return

    lines = text.splitlines()

    # 1) Strip block markers if present
    filtered = []
    for ln in lines:
        if ln.strip().startswith("<<LIVE_") and ln.strip().endswith(">>"):
            continue
        filtered.append(ln.rstrip("\n"))

    # 2) Render line-by-line with simple rules
    pending_paragraph = []

    def flush_paragraph():
        nonlocal pending_paragraph
        if pending_paragraph:
            # keep manual line breaks
            st.markdown("<br>".join(pending_paragraph), unsafe_allow_html=True)
            pending_paragraph = []

    for raw in filtered:
        line = raw.rstrip()

        # blank line => paragraph break
        if line.strip() == "":
            flush_paragraph()
            continue

        # visual separators
        if SEP_EQ_RE.match(line.strip()):
            flush_paragraph()
            st.divider()
            continue

        if SEP_DASH_RE.match(line.strip()):
            flush_paragraph()
            st.divider()
            continue

        # STATUS line
        if line.upper().startswith("STATUS:"):
            flush_paragraph()
            st.caption(line)
            continue

        # Big title line (first big header)
        if "LIVE WEEK VIEW" in line.upper() and len(line) < 120:
            flush_paragraph()
            st.title(line)
            continue

        # Day header
        # e.g. "MONDAY 05 JAN — RELEASED"
        if ("—" in line or "-" in line) and ("RELEASED" in line.upper() or "LIVE" in line.upper()):
            # safeguard: typical day headers are mostly uppercase
            if line == line.upper() and len(line) <= 60:
                flush_paragraph()
                st.header(line)
                continue

        # Indicator header: all caps and short-ish
        # e.g. "WARDS TOTAL VEHICLE SALES (DEC)"
        if line == line.upper() and 3 <= len(line) <= 70:
            flush_paragraph()
            st.subheader(line)
            continue

        # Otherwise: accumulate as paragraph (preserve manual line breaks)
        pending_paragraph.append(line)

    flush_paragraph()

