import os
import time
from datetime import datetime

import feedparser
import requests
import yfinance as yf
from google import genai
from groq import Groq


# ============================================================
# CONFIGURATION
# ============================================================

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
GEMINI_API_KEYS = [
    os.getenv("GEMINI_API_KEY_1"),
    os.getenv("GEMINI_API_KEY_2"),
    os.getenv("GEMINI_API_KEY_3"),
]
GEMINI_API_KEYS = [key.strip() for key in GEMINI_API_KEYS if key and key.strip()]

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Groq production fallback models.
GROQ_MODELS = [
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
]

CONTENT_TYPE = os.getenv("CONTENT_TYPE", "video").lower().strip()

# Gemini model
GEMINI_MODELS = [
    "gemini-3.6-flash",
    "gemini-3.1-pro-preview",
]

# Retry configuration
# MAX_GEMINI_RETRIES = 4
# RETRY_DELAYS = [30, 60, 120, 240]

# Output folders
POSTS_DIR = "posts"

os.makedirs(POSTS_DIR, exist_ok=True)


# ============================================================
# BASIC HELPERS
# ============================================================

def clean_text(text):
    """Clean basic whitespace."""
    if not text:
        return ""

    return " ".join(str(text).split())


def escape_html(text):
    """Escape HTML-sensitive characters."""
    if text is None:
        return ""

    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


# ============================================================
# MARKET DATA
# ============================================================

def get_market_data():
    print("Fetching market data...")

    market_data = {
        "nifty": None,
        "sensex": None,
    }

    try:
        print("Fetching Nifty data...")

        nifty = yf.Ticker("^NSEI")
        nifty_history = nifty.history(period="5d")

        if nifty_history.empty:
            raise RuntimeError("No Nifty data returned.")

        nifty_close = float(nifty_history["Close"].iloc[-1])
        market_data["nifty"] = nifty_close

        print(f"Nifty Close: {nifty_close}")

    except Exception as e:
        print(f"⚠️ Nifty error: {e}")

    try:
        print("Fetching Sensex data...")

        sensex = yf.Ticker("^BSESN")
        sensex_history = sensex.history(period="5d")

        if sensex_history.empty:
            raise RuntimeError("No Sensex data returned.")

        sensex_close = float(sensex_history["Close"].iloc[-1])
        market_data["sensex"] = sensex_close

        print(f"Sensex Close: {sensex_close}")

    except Exception as e:
        print(f"⚠️ Sensex error: {e}")

    return market_data


# ============================================================
# NEWS RSS
# ============================================================

RSS_FEEDS = [
    "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
    "https://www.moneycontrol.com/rss/marketreports.xml",
    "https://www.moneycontrol.com/rss/business.xml",
    "https://www.business-standard.com/rss/markets-106.rss",
    "https://www.business-standard.com/rss/latest.xml",
    "https://www.livemint.com/rss/markets",
    "https://www.livemint.com/rss/companies",
    "https://www.thehindubusinessline.com/markets/feeder/default.rss",
    "https://www.thehindubusinessline.com/economy/feeder/default.rss",
    "https://feeds.reuters.com/reuters/businessNews",
]


def fetch_news_headlines():
    print("Fetching news headlines...")

    headlines = []
    seen = set()

    for feed_url in RSS_FEEDS:

        try:
            feed = feedparser.parse(feed_url)

            for entry in feed.entries:

                title = clean_text(
                    entry.get("title", "")
                )

                if not title:
                    continue

                normalized = title.lower()

                if normalized in seen:
                    continue

                seen.add(normalized)

                headlines.append(title)

        except Exception as e:
            print(
                f"⚠️ RSS error for {feed_url}: {e}"
            )

    print(
        f"Collected {len(headlines)} unique headlines."
    )

    # Keep prompt size reasonable
    return headlines[:113]


# ============================================================
# AI GENERATION - GEMINI + GROQ FALLBACK
# ============================================================

def generate_with_gemini(prompt):
    """Try all configured Gemini API keys/models."""

    if not GEMINI_API_KEYS:
        print("⚠️ No Gemini API keys configured.")
        return None

    last_error = None

    for key_index, api_key in enumerate(GEMINI_API_KEYS, start=1):

        print("=" * 60)
        print(
            f"Trying Gemini API key "
            f"{key_index}/{len(GEMINI_API_KEYS)}"
        )
        print("=" * 60)

        try:
            client = genai.Client(api_key=api_key)
        except Exception as e:
            last_error = e
            print(f"❌ Could not initialize Gemini client: {e}")
            continue

        for model_name in GEMINI_MODELS:

            print("-" * 60)
            print(f"Trying Gemini model: {model_name}")

            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt
                )

                if response is None or not response.text:
                    raise RuntimeError(
                        "Gemini returned an empty response."
                    )

                print(
                    f"✅ Gemini success: "
                    f"key {key_index} / {model_name}"
                )

                return response.text

            except Exception as e:

                last_error = e
                error_text = str(e)

                print(
                    f"❌ Key {key_index} / {model_name} failed: "
                    f"{error_text}"
                )

                if (
                    "429" in error_text
                    or "RESOURCE_EXHAUSTED" in error_text
                    or "quota" in error_text.lower()
                    or "rate limit" in error_text.lower()
                ):
                    print(
                        "⚠️ Gemini quota/rate limit. "
                        "Trying next model/key."
                    )
                    continue

                if (
                    "503" in error_text
                    or "UNAVAILABLE" in error_text
                    or "high demand" in error_text.lower()
                ):
                    print(
                        "⚠️ Gemini temporarily unavailable. "
                        "Trying next model/key."
                    )
                    continue

                if (
                    "401" in error_text
                    or "403" in error_text
                    or "PERMISSION_DENIED" in error_text
                    or "UNAUTHENTICATED" in error_text
                ):
                    print(
                        f"⚠️ Gemini key {key_index} was rejected. "
                        "Trying next key."
                    )
                    break

                print(
                    "⚠️ Unknown Gemini error. "
                    "Trying next model/key."
                )

        if key_index < len(GEMINI_API_KEYS):
            print("=" * 60)
            print(
                f"Switching from Gemini key {key_index} "
                f"to key {key_index + 1}"
            )
            print("=" * 60)

    print("=" * 60)
    print("⚠️ ALL GEMINI ATTEMPTS FAILED")
    print("=" * 60)

    if last_error is not None:
        print(f"Last Gemini error: {last_error}")

    return None


def generate_with_groq(prompt):
    """Try configured Groq production models."""

    if not GROQ_API_KEY:
        print("⚠️ GROQ_API_KEY is not configured.")
        return None

    try:
        client = Groq(api_key=GROQ_API_KEY)
    except Exception as e:
        print(f"❌ Could not initialize Groq client: {e}")
        return None

    last_error = None

    for model_name in GROQ_MODELS:

        print("-" * 60)
        print(f"Trying Groq model: {model_name}")

        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an expert Indian stock market "
                            "researcher and Hindi YouTube financial "
                            "content writer. Follow the user's instructions "
                            "strictly. Use only supplied factual inputs "
                            "and never invent financial facts."
                        ),
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    },
                ],
                temperature=0.4,
                max_tokens=8192,
            )

            if (
                response is None
                or not response.choices
                or not response.choices[0].message
                or not response.choices[0].message.content
            ):
                raise RuntimeError(
                    "Groq returned an empty response."
                )

            result = response.choices[0].message.content.strip()

            if not result:
                raise RuntimeError(
                    "Groq returned an empty text response."
                )

            print(
                f"✅ Groq success: {model_name}"
            )

            return result

        except Exception as e:

            last_error = e
            error_text = str(e)

            print(
                f"❌ Groq model {model_name} failed: "
                f"{error_text}"
            )

            if (
                "429" in error_text
                or "rate limit" in error_text.lower()
                or "quota" in error_text.lower()
            ):
                print(
                    "⚠️ Groq rate limit/quota. "
                    "Trying next Groq model."
                )
                continue

            if (
                "401" in error_text
                or "403" in error_text
                or "authentication" in error_text.lower()
                or "invalid api key" in error_text.lower()
            ):
                print("❌ Groq API key appears invalid.")
                break

            if (
                "503" in error_text
                or "502" in error_text
                or "504" in error_text
                or "unavailable" in error_text.lower()
                or "timeout" in error_text.lower()
            ):
                print(
                    "⚠️ Temporary Groq service error. "
                    "Trying next Groq model."
                )
                continue

            print(
                "⚠️ Unknown Groq error. "
                "Trying next Groq model."
            )

    print("=" * 60)
    print("❌ ALL GROQ MODELS FAILED")
    print("=" * 60)

    if last_error is not None:
        print(f"Last Groq error: {last_error}")

    return None


def generate_ai_script(prompt):
    """
    Generate the script with provider failover.

    Order:
        1. Gemini keys/models
        2. Groq production models
    """

    print("=" * 60)
    print("GENERATING AI SCRIPT")
    print("=" * 60)

    # --------------------------------------------------------
    # 1. Gemini
    # --------------------------------------------------------

    print("🤖 Primary provider: Gemini")

    gemini_result = generate_with_gemini(prompt)

    if gemini_result:
        print("✅ Script generated using Gemini.")
        return gemini_result

    # --------------------------------------------------------
    # 2. Groq
    # --------------------------------------------------------

    print("=" * 60)
    print("🔄 Switching to Groq fallback...")
    print("=" * 60)

    groq_result = generate_with_groq(prompt)

    if groq_result:
        print("✅ Script generated using Groq.")
        return groq_result

    # --------------------------------------------------------
    # 3. All providers failed
    # --------------------------------------------------------

    raise RuntimeError(
        "ALL AI PROVIDERS FAILED: "
        "Gemini and Groq were both unavailable."
    )


# ============================================================
# TELEGRAM
# ============================================================

def send_to_telegram(message):

    if not BOT_TOKEN or not CHAT_ID:

        print(
            "Telegram credentials missing. "
            "Skipping Telegram."
        )

        return

    telegram_url = (
        f"https://api.telegram.org/bot"
        f"{BOT_TOKEN}/sendMessage"
    )

    # Telegram message limit
    chunk_size = 3500

    chunks = [
        message[i:i + chunk_size]
        for i in range(
            0,
            len(message),
            chunk_size
        )
    ]

    for index, chunk in enumerate(chunks, 1):

        try:

            response = requests.post(
                telegram_url,
                data={
                    "chat_id": CHAT_ID,
                    "text": chunk,
                },
                timeout=30,
            )

            response.raise_for_status()

            print(
                f"Telegram message "
                f"{index}/{len(chunks)} sent."
            )

        except Exception as e:

            print(
                f"⚠️ Telegram error: {e}"
            )


# ============================================================
# SAVE HTML REPORT
# ============================================================

def save_post(
    script_text,
    market_data,
    content_type
):

    today = datetime.now().strftime(
        "%Y-%m-%d"
    )

    filename = os.path.join(
        POSTS_DIR,
        f"{today}.html"
    )

    nifty = market_data.get("nifty")
    sensex = market_data.get("sensex")

    html = f"""<!DOCTYPE html>
<html lang="en">

<head>

<meta charset="UTF-8">

<meta
    name="viewport"
    content="width=device-width,
             initial-scale=1.0"
>

<title>
Stock Samvad AI - {today}
</title>

<style>

* {{
    box-sizing: border-box;
}}

body {{
    margin: 0;
    padding: 0;

    background:
        linear-gradient(
            135deg,
            #050505,
            #111111
        );

    color: #f5f5f5;

    font-family:
        Arial,
        Helvetica,
        sans-serif;

    line-height: 1.7;
}}

.container {{
    width: min(
        1100px,
        calc(100% - 30px)
    );

    margin: 30px auto;
}}

.header {{
    padding: 30px;

    border-radius: 20px;

    background:
        linear-gradient(
            135deg,
            #151515,
            #242424
        );

    border: 1px solid #333;

    margin-bottom: 25px;
}}

.header h1 {{
    margin: 0 0 10px;

    font-size: 32px;
}}

.date {{
    color: #aaa;
}}

.stats {{
    display: grid;

    grid-template-columns:
        repeat(
            auto-fit,
            minmax(
                200px,
                1fr
            )
        );

    gap: 15px;

    margin-bottom: 25px;
}}

.stat {{
    padding: 20px;

    border-radius: 15px;

    background: #181818;

    border: 1px solid #303030;
}}

.stat-title {{
    color: #999;

    font-size: 14px;
}}

.stat-value {{
    margin-top: 5px;

    font-size: 25px;

    font-weight: bold;
}}

.report {{
    background: #111;

    border: 1px solid #2b2b2b;

    border-radius: 20px;

    padding: 30px;

    white-space: pre-wrap;

    word-wrap: break-word;
}}

.copy-button {{
    position: fixed;

    right: 20px;
    bottom: 20px;

    padding: 13px 20px;

    border: none;

    border-radius: 30px;

    background: #ffffff;

    color: #000;

    font-weight: bold;

    cursor: pointer;

    box-shadow:
        0 5px 25px
        rgba(0,0,0,.4);
}}

@media(max-width:600px) {{

    .container {{
        width:
            calc(100% - 18px);

        margin: 10px auto;
    }}

    .header {{
        padding: 20px;
    }}

    .header h1 {{
        font-size: 25px;
    }}

    .report {{
        padding: 18px;

        font-size: 14px;
    }}

}}

</style>

</head>

<body>

<div class="container">

<div class="header">

<h1>
STOCK SAMVAD AI
</h1>

<div class="date">
Daily Market Report — {escape_html(today)}
</div>

<div class="date">
Content Type:
{escape_html(content_type)}
</div>

</div>


<div class="stats">

<div class="stat">

<div class="stat-title">
NIFTY 50
</div>

<div class="stat-value">
{escape_html(
    str(nifty)
    if nifty is not None
    else "N/A"
)}
</div>

</div>


<div class="stat">

<div class="stat-title">
SENSEX
</div>

<div class="stat-value">
{escape_html(
    str(sensex)
    if sensex is not None
    else "N/A"
)}
</div>

</div>

</div>


<div class="report" id="report">
{escape_html(script_text)}
</div>

</div>


<button
    class="copy-button"
    onclick="copyReport()"
>
Copy Report
</button>


<script>

function copyReport() {{

    const text =
        document.getElementById(
            "report"
        ).innerText;

    navigator.clipboard.writeText(text)
        .then(() => {{

            alert(
                "Report copied!"
            );

        }});

}}

</script>

</body>

</html>
"""

    with open(
        filename,
        "w",
        encoding="utf-8"
    ) as file:

        file.write(html)

    print(
        f"Saved report: {filename}"
    )

    return filename


# ============================================================
# INDEX GENERATOR
# ============================================================

def generate_index():

    print("Generating posts index...")

    files = []

    if os.path.exists(POSTS_DIR):

        for filename in os.listdir(
            POSTS_DIR
        ):

            if (
                filename.endswith(".html")
                and filename != "index.html"
            ):

                files.append(filename)

    files.sort(
        reverse=True
    )

    cards = ""

    for filename in files:

        date_text = filename.replace(
            ".html",
            ""
        )

        cards += f"""
<a
    href="{filename}"
    class="card"
>

<div class="card-title">
Daily Market Report
</div>

<div class="card-date">
{escape_html(date_text)}
</div>

</a>
"""

    index_html = f"""<!DOCTYPE html>

<html lang="en">

<head>

<meta charset="UTF-8">

<meta
    name="viewport"
    content="width=device-width,
             initial-scale=1.0"
>

<title>
Stock Samvad AI
</title>

<style>

* {{
    box-sizing: border-box;
}}

body {{
    margin: 0;

    background:
        linear-gradient(
            135deg,
            #050505,
            #111111
        );

    color: white;

    font-family:
        Arial,
        Helvetica,
        sans-serif;
}}

.container {{
    width:
        min(
            1000px,
            calc(100% - 30px)
        );

    margin:
        50px auto;
}}

.hero {{
    padding: 35px;

    border-radius: 25px;

    background:
        linear-gradient(
            135deg,
            #161616,
            #242424
        );

    border:
        1px solid #333;

    margin-bottom: 30px;
}}

.hero h1 {{
    margin: 0;

    font-size: 38px;
}}

.hero p {{
    color: #aaa;
}}

.automation {{
    display: inline-block;

    margin-top: 15px;

    padding: 12px 18px;

    border-radius: 25px;

    background: white;

    color: black;

    text-decoration: none;

    font-weight: bold;
}}

.archive {{
    display: grid;

    grid-template-columns:
        repeat(
            auto-fit,
            minmax(
                230px,
                1fr
            )
        );

    gap: 15px;
}}

.card {{
    display: block;

    padding: 22px;

    border-radius: 18px;

    background: #181818;

    border: 1px solid #303030;

    color: white;

    text-decoration: none;

    transition:
        transform .2s;
}}

.card:hover {{
    transform:
        translateY(-3px);
}}

.card-title {{
    font-size: 18px;

    font-weight: bold;
}}

.card-date {{
    margin-top: 7px;

    color: #999;
}}

</style>

</head>

<body>

<div class="container">

<div class="hero">

<h1>
STOCK SAMVAD AI
</h1>

<p>
Daily AI-generated Indian stock market reports.
</p>

<a
    class="automation"
    href="https://github.com/lalit-op/lalit-op/actions/workflows/market_news.yml"
>
Run Daily Market Bot
</a>

</div>


<h2>
Report Archive
</h2>

<div class="archive">

{cards}

</div>

</div>

</body>

</html>
"""

    index_path = os.path.join(
        POSTS_DIR,
        "index.html"
    )

    with open(
        index_path,
        "w",
        encoding="utf-8"
    ) as file:

        file.write(index_html)

    print(
        f"Index generated: {index_path}"
    )


# ============================================================
# PROMPT CREATION
# ============================================================

def build_prompt(
    market_data,
    headlines,
    content_type
):

    today = datetime.now().strftime(
        "%d %B %Y"
    )

    nifty = market_data.get(
        "nifty",
        "N/A"
    )

    sensex = market_data.get(
        "sensex",
        "N/A"
    )

    news_text = "\n".join(
        f"{i + 1}. {headline}"
        for i, headline
        in enumerate(headlines)
    )

    # --------------------------------------------------------
    # SHORT VIDEO
    # --------------------------------------------------------

    if content_type == "short":

        prompt = f"""
You are an expert Indian stock market
content creator.

Today is {today}.

Create a Hindi YouTube Shorts script
of approximately 45–60 seconds.

IMPORTANT:
Use only the supplied market data
and supplied headlines as factual inputs.

Do not invent prices, events,
companies, statistics or announcements.

MARKET DATA:

Nifty 50:
{nifty}

Sensex:
{sensex}

NEWS HEADLINES:

{news_text}

STRUCTURE:

1. Powerful opening hook.
2. Nifty update.
3. Sensex update.
4. Most important market news.
5. One useful investor takeaway.
6. Strong closing.

Use natural spoken Hindi.

Also provide:

TITLE:
THUMBNAIL TEXT:
DESCRIPTION:
HASHTAGS:
"""

        return prompt

    # --------------------------------------------------------
    # LONG VIDEO
    # --------------------------------------------------------

    prompt = f"""
You are an expert Indian stock market
researcher and YouTube financial content
writer.

Today is {today}.

Create a detailed Hindi YouTube video
script of approximately 3000–3500 words.

The script should be suitable for an
18–20 minute video.

IMPORTANT:

Use the supplied market data and
news headlines as the factual basis.

Do NOT invent market prices,
company announcements, economic data,
FII/DII numbers or events.

If a specific fact is not present
in the supplied data, clearly say that
the information was not available
instead of fabricating it.

MARKET DATA
============

Nifty 50:
{nifty}

Sensex:
{sensex}


NEWS HEADLINES
==============

{news_text}


SCRIPT STRUCTURE
================

1. Opening hook

2. Today's Indian stock market overview

3. Nifty 50 analysis

4. Sensex analysis

5. Top important market news

6. Sector-wise discussion

7. Important companies mentioned
   in the news

8. Global market impact

9. FII/DII discussion

10. Corporate developments

11. Important factors for the
    next trading session

12. What investors should monitor

13. Educational market lesson

14. Conclusion

15. Financial disclaimer


STYLE
=====

Write in natural conversational Hindi.

Use some English financial terms
where naturally appropriate.

Make the script engaging but factual.

Do not provide personalized
investment advice.

Do not guarantee profits.

Do not use sensational claims.


AT THE END ALSO PROVIDE:

SEO TITLE:

THUMBNAIL TEXT:

VIDEO DESCRIPTION:

HASHTAGS:

PINNED COMMENT:

CHAPTER TIMESTAMPS:


DISCLAIMER:

"This video is for educational and
informational purposes only and is not
financial advice. Please conduct your
own research or consult a qualified
financial professional before making
investment decisions."
"""

    return prompt


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)
    print(
        "STOCK SAMVAD AI - DAILY MARKET BOT"
    )
    print("=" * 60)

    # --------------------------------------------------------
    # Market data
    # --------------------------------------------------------

    market_data = get_market_data()

    # --------------------------------------------------------
    # News
    # --------------------------------------------------------

    headlines = fetch_news_headlines()

    if not headlines:

        print(
            "⚠️ No news headlines found."
        )

    # --------------------------------------------------------
    # Content type
    # --------------------------------------------------------

    print(
        f"Content type {CONTENT_TYPE}"
    )

    # --------------------------------------------------------
    # Prompt
    # --------------------------------------------------------

    prompt = build_prompt(
        market_data,
        headlines,
        CONTENT_TYPE
    )

    # --------------------------------------------------------
    # AI generation with Gemini + Groq fallback
    # --------------------------------------------------------

    print(
        "Generating AI Script with Gemini + Groq fallback..."
    )

    try:

        script_text = generate_ai_script(
            prompt
        )

        print(
            "✅ AI script generated successfully."
        )

    except Exception as e:

        error_msg = (
            f"❌ AI Generation Error\n\n"
            f"{e}"
        )

        print(error_msg)

        send_to_telegram(
            error_msg
        )

        # Keep GitHub Actions failed if every provider fails.
        raise

    # --------------------------------------------------------
    # Save report
    # --------------------------------------------------------

    save_post(
        script_text,
        market_data,
        CONTENT_TYPE
    )

    # --------------------------------------------------------
    # Generate archive index
    # --------------------------------------------------------

    generate_index()

    # --------------------------------------------------------
    # Telegram
    # --------------------------------------------------------

    telegram_message = (
        "📈 STOCK SAMVAD AI\n\n"
        f"Date: "
        f"{datetime.now().strftime('%d-%m-%Y')}\n"
        f"Type: {CONTENT_TYPE}\n\n"
        f"{script_text}"
    )

    send_to_telegram(
        telegram_message
    )

    print(
        "Market report processed "
        "for Telegram."
    )

    print("=" * 60)
    print("✅ DAILY MARKET BOT COMPLETED")
    print("=" * 60)


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()