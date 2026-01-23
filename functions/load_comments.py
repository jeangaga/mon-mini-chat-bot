# functions/load_comments.py
import requests
import re
from datetime import date, timedelta

# === Fonction principale pour les actions ===

import requests
import re

def load_stock_comment(code: str) -> str:
    """
    Load the FIRST LIVE stock macro block for a given ticker from GitHub.

    File:
      notes/STOCKS_LIVE_NOTE.txt

    Block markers:
      <<LIVE_<TICKER>_MACRO_BEGIN>> ... <<LIVE_<TICKER>_MACRO_END>>
    """
    ticker = code.strip().upper()
    if not ticker:
        return "❌ Invalid ticker (empty)."

    base_url = "https://raw.githubusercontent.com/jeangaga/mon-mini-chat-bot/main/notes"
    filename = "STOCKS_LIVE_NOTE.txt"
    url = f"{base_url}/{filename}"

    begin_tag = f"<<LIVE_{ticker}_MACRO_BEGIN>>"
    end_tag   = f"<<LIVE_{ticker}_MACRO_END>>"

    try:
        r = requests.get(url, timeout=5)
        if r.status_code != 200:
            return f"❌ No STOCKS live note file (HTTP {r.status_code}): {filename}"
    except Exception as e:
        return f"❌ Error loading STOCKS live note: {e}"

    text = r.text
    pattern = re.escape(begin_tag) + r"(.*?)" + re.escape(end_tag)
    matches = re.findall(pattern, text, flags=re.S)

    if not matches:
        return (
            f"❌ LIVE stock markers not found for {ticker} in {filename}: "
            f"{begin_tag} ... {end_tag}"
        )

    return matches[0].strip()






def load_stock_comment_old(code: str):
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
SEP_EQ_RE = re.compile(r"^={3,}$")
SEP_DASH_RE = re.compile(r"^-{3,}$")
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

    File convention:
      notes/LIVE_<REGION>_MACRO.txt   (e.g., LIVE_USD_MACRO.txt)

    Block markers:
      <<LIVE_<REGION>_MACRO_BEGIN>> ... <<LIVE_<REGION>_MACRO_END>>
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
            return f"❌ No LIVE macro file for {reg} (HTTP {r.status_code}): {filename}"
    except Exception as e:
        return f"❌ Error loading LIVE macro for {reg}: {e}"

    text = r.text
    pattern = re.escape(begin_tag) + r"(.*?)" + re.escape(end_tag)
    matches = re.findall(pattern, text, flags=re.S)

    if not matches:
        return f"❌ LIVE markers not found in {filename}: {begin_tag} ... {end_tag}"

    return matches[0].strip()

def render_live_macro_block(text: str) -> str:
    """
    PURE formatter: takes the raw LIVE block (ASCII) and returns a nicer
    Streamlit-friendly Markdown string.

    v4 (structure-tight, no semantic hacks):
    - Title smaller (##)
    - STATUS line bold
    - Day headers smaller (bold, not heading)
    - ALL-CAPS short headers -> ### (kept)
    - Release title lines -> bold (tight heuristic)
      * short-ish (<= 60 chars)
      * NOT ALL CAPS
      * NOT data-prefix lines (Actual/Cons/Prior/etc)
      * MUST NOT contain ':' (prevents bolding commentary like "Sensitivity: ...")
    """
    if not text:
        return "❌ Empty LIVE macro block."
    if text.strip().startswith("❌"):
        return text

    lines = text.splitlines()

    # Remove LIVE markers if present
    cleaned = []
    for ln in lines:
        s = ln.strip()
        if s.startswith("<<LIVE_") and s.endswith(">>"):
            continue
        cleaned.append(ln.rstrip())

    out = []
    i = 0

    def add_blank():
        if out and out[-1] != "":
            out.append("")

    def add_line_keep_break(s: str):
        # In Markdown, a hard line break needs two spaces before newline
        out.append(s + "  ")

    DATA_PREFIXES = (
        "ACTUAL", "PRIOR", "CONS", "REVISED", "MIN", "MAX", "COUNT",
        "SURPRISE", "HF TAKE", "HF COMMENT"
    )

    while i < len(cleaned):
        line = cleaned[i].rstrip()
        s = line.strip()

        # blank line
        if s == "":
            add_blank()
            i += 1
            continue

        # separators -> horizontal rule
        if SEP_EQ_RE.match(s) or SEP_DASH_RE.match(s):
            add_blank()
            out.append("---")
            add_blank()
            i += 1
            continue

        upper = s.upper()

        # Title line — smaller
        if "LIVE WEEK VIEW" in upper and len(s) <= 160:
            add_blank()
            out.append(f"## {s}")
            add_blank()
            i += 1
            continue

        # Status line — bold
        if upper.startswith("STATUS:"):
            add_blank()
            out.append(f"**{s}**")
            add_blank()
            i += 1
            continue

        # Day headers (ALL CAPS + RELEASED/LIVE/PREVIEW) — smaller (bold)
        if ("RELEASED" in upper or "LIVE" in upper or "PREVIEW" in upper) and s == upper and len(s) <= 100:
            add_blank()
            out.append(f"**{s}**")
            add_blank()
            i += 1
            continue

        # ALL CAPS short headers -> ### (kept)
        if s == upper and 3 <= len(s) <= 90:
            add_blank()
            out.append(f"### {s}")
            add_blank()
            i += 1
            continue

        # Bullet lines: keep as-is
        if s.startswith("- ") or s.startswith("* ") or s.startswith("• "):
            add_line_keep_break(s)
            i += 1
            continue

        # Release title lines — bold (tight heuristic)
        if (
            3 <= len(s) <= 60
            and s != upper
            and ":" not in s
            and not upper.startswith(DATA_PREFIXES)
            and not upper.startswith("STATUS:")
        ):
            add_blank()
            out.append(f"**{s}**  ")
            i += 1
            continue

        # Normal text: keep line breaks
        add_line_keep_break(s)
        i += 1

    # cleanup: remove trailing blanks
    while out and out[-1] == "":
        out.pop()

    return "\n".join(out)


def load_liv2_macro_block(region: str) -> str:
    """
    Load the FIRST TWO LIVE macro blocks for a given region from GitHub
    and output them concatenated (separated by blank lines).

    File convention (same as your existing function):
      notes/<REGION>_MACRO_NOTE.txt   (e.g., USD_MACRO_NOTE.txt)

    Block markers (same as your existing function):
      <<LIVE_<REGION>_MACRO_BEGIN>> ... <<LIVE_<REGION>_MACRO_END>>
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
            return f"❌ No LIVE macro file for {reg} (HTTP {r.status_code}): {filename}"
    except Exception as e:
        return f"❌ Error loading LIVE macro for {reg}: {e}"

    text = r.text
    pattern = re.escape(begin_tag) + r"(.*?)" + re.escape(end_tag)
    matches = re.findall(pattern, text, flags=re.S)

    if not matches:
        return f"❌ LIVE markers not found in {filename}: {begin_tag} ... {end_tag}"

    # Take first two blocks if available
    first = matches[0].strip()
    if len(matches) >= 2:
        second = matches[1].strip()
        return first + "\n\n" + second

    # If only one block exists, return it with an explicit note
    return first + "\n\n" + "⚠️ Only one LIVE block found (no second block present)."

def load_liv3_macro_block(region: str) -> str:
    """
    Load the FIRST THREE LIVE macro blocks for a given region from GitHub
    and output them concatenated (separated by blank lines).

    File convention (same as existing functions):
      notes/<REGION>_MACRO_NOTE.txt   (e.g., USD_MACRO_NOTE.txt)

    Block markers:
      <<LIVE_<REGION>_MACRO_BEGIN>> ... <<LIVE_<REGION>_MACRO_END>>
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
            return f"❌ No LIVE macro file for {reg} (HTTP {r.status_code}): {filename}"
    except Exception as e:
        return f"❌ Error loading LIVE macro for {reg}: {e}"

    text = r.text
    pattern = re.escape(begin_tag) + r"(.*?)" + re.escape(end_tag)
    matches = re.findall(pattern, text, flags=re.S)

    if not matches:
        return f"❌ LIVE markers not found in {filename}: {begin_tag} ... {end_tag}"

    blocks = [m.strip() for m in matches[:3]]

    if len(blocks) < 3:
        blocks.append("⚠️ Only " + str(len(blocks)) + " LIVE block(s) found.")

    return "\n\n".join(blocks)


def render_liv2_macro_block(text: str, country: str) -> str:
    """
    Filter an already-extracted LIVE macro text to keep only the sections
    for `country`, then render via render_live_macro_block().

    Matches country section headers like:
      "<Country> — <Release title>"
    accepting dash variants: -, – , —
    """
    import re

    if not text:
        return "❌ Empty LIVE macro block."
    if str(text).strip().startswith("❌"):
        return text
    if not country:
        return "❌ Country not specified."

    country = country.strip()
    lines = str(text).splitlines()

    kept = []
    keep_mode = False

    # Accept hyphen/en-dash/em-dash after country
    DASH = r"[-–—]"

    # Country start: "Japan — ..."
    country_start = re.compile(rf"^{re.escape(country)}\s*{DASH}\s+")

    # Any country start: "United Kingdom — ..."
    any_country_start = re.compile(rf"^[A-Za-z][A-Za-z .()&/]*\s*{DASH}\s+")

    # Day header: "MONDAY 19 — RELEASED"
    day_header = re.compile(rf"^[A-Z]+(?:\s+\d{{1,2}})?\s*{DASH}\s+(RELEASED|LIVE|PREVIEW)$")

    for ln in lines:
        s = ln.strip()

        # Always keep global structure / wrappers
        if (
            (s.startswith("<<LIVE_") and s.endswith(">>"))
            or ("LIVE WEEK VIEW" in s.upper())
            or s.upper().startswith("STATUS:")
            or day_header.match(s)
            or s == ""
        ):
            kept.append(ln)
            keep_mode = False
            continue

        # Start of target country section
        if country_start.match(s):
            kept.append(ln)
            keep_mode = True
            continue

        # Start of another country section -> stop keeping
        if any_country_start.match(s):
            keep_mode = False
            continue

        # Inside target section
        if keep_mode:
            kept.append(ln)

    filtered_text = "\n".join(kept).strip()
    if not filtered_text:
        return f"⚠️ No releases found for {country} (check spelling vs headers)."

    return render_live_macro_block(filtered_text)
