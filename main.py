import os
from datetime import datetime

import requests
import yfinance as yf
import feedparser
import google.generativeai as genai

# =========================
# ENV VARIABLES
# =========================

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
CONTENT_TYPE = os.getenv("CONTENT_TYPE", "video")

# =========================
# GEMINI CONFIG
# =========================

genai.configure(api_key=GEMINI_API_KEY)

# =========================
# MARKET DATA
# =========================

try:
    nifty = yf.Ticker("^NSEI")
    nifty_close = round(
        float(nifty.history(period="5d")["Close"].iloc[-1]),
        2
    )
except Exception:
    nifty_close = "Unavailable"

try:
    sensex = yf.Ticker("^BSESN")
    sensex_close = round(
        float(sensex.history(period="5d")["Close"].iloc[-1]),
        2
    )
except Exception:
    sensex_close = "Unavailable"

# =========================
# NEWS SOURCES
# =========================

sources = [
    "https://www.moneycontrol.com/rss/business.xml",
    "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
    "https://economictimes.indiatimes.com/rssfeedsdefault.cms",
    "https://www.business-standard.com/rss/markets-106.rss",
    "https://www.livemint.com/rss/markets",
    "https://www.financialexpress.com/market/feed/",
    "https://www.cnbctv18.com/commonfeeds/v1/eng/rss/business.xml",
    "https://www.zeebiz.com/india-markets/rss",
    "https://finance.yahoo.com/rss/",
    "https://feeds.content.dowjones.io/public/rss/mw_marketpulse",
    "https://www.investing.com/rss/news.rss",
    "https://www.sebi.gov.in/sebirss.xml"
]

# =========================
# FETCH NEWS
# =========================

headlines = []

for source in sources:
    try:
        feed = feedparser.parse(source)

        for item in feed.entries[:15]:
            title = item.title.strip()

            if title not in headlines:
                headlines.append(title)

    except Exception as e:
        print(f"Error reading {source}: {e}")

news_text = "\n".join(headlines[:100])

# =========================
# SAVE POST
# =========================

def save_post(title, content):
    os.makedirs("posts", exist_ok=True)

    filename = datetime.now().strftime("%Y-%m-%d") + ".md"

    filepath = os.path.join("posts", filename)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"# {title}\n\n")
        f.write(content)

    print(f"Saved: {filepath}")

# =========================
# CONTENT TYPE
# =========================

if CONTENT_TYPE == "short":

    master_prompt = """

    आप भारत के सबसे भरोसेमंद शेयर बाजार न्यूज़ एंकर हैं।

    आज की खबरों और बाजार डेटा के आधार पर
    45-60 सेकंड का वायरल YouTube Short बनाइए।

    Format:

    1. दमदार Hook


    2. मुख्य खबर


    3. निवेशकों पर प्रभाव


    4. Conclusion



    साथ में Generate करें:

    Shorts Title

    Thumbnail Text

    Description

    10 Hashtags

    पूरी स्क्रिप्ट हिंदी में हो।
    """

else:

    master_prompt = """

    आप भारत के सबसे भरोसेमंद शेयर बाजार विश्लेषक और यूट्यूब न्यूज एंकर हैं।

    आज के बाजार डेटा और खबरों के आधार पर
    18-20 मिनट की विस्तृत हिंदी वीडियो स्क्रिप्ट तैयार करें।

    शामिल करें:

    1. दमदार ओपनिंग हुक


    2. मार्केट ओवरव्यू


    3. निफ्टी और सेंसेक्स विश्लेषण


    4. टॉप 10 बड़ी खबरें


    5. सेक्टर विश्लेषण


    6. टॉप गेनर्स


    7. टॉप लूजर्स


    8. कॉर्पोरेट अपडेट


    9. ग्लोबल मार्केट प्रभाव


    10. FII और DII गतिविधि


    11. कल के ट्रिगर्स


    12. निवेशकों के लिए सीख


    13. निष्कर्ष


    14. डिस्क्लेमर



    साथ में दें:

    SEO Title

    Thumbnail Text

    Description

    20 Hashtags

    Pinned Comment

    Chapter Timestamps

    पूरी स्क्रिप्ट हिंदी में लिखें।

    लंबाई:
    3000-3500 शब्द।

    केवल उपलब्ध बाजार डेटा और हेडलाइंस का उपयोग करें।
    कोई झूठी जानकारी न दें।
    """

# =========================
# FINAL PROMPT
# =========================

prompt = f"""
{master_prompt}

आज का बाजार डेटा

Nifty Close: {nifty_close}

Sensex Close: {sensex_close}

आज की प्रमुख खबरें:

{news_text}
"""

# =========================
# GEMINI GENERATION
# =========================

model = genai.GenerativeModel("gemini-2.5-flash")

try:

    response = model.generate_content(prompt)

    today = datetime.now().strftime("%d-%m-%Y")

    script = f"""

    📅 दिनांक: {today}

    📊 Content Type: {CONTENT_TYPE.upper()}

    {response.text}
    """

    title = f"Daily Stock Market Script - {today}"

    save_post(
        title=title,
        content=script
    )

except Exception as e:

    script = f"""

    ❌ Gemini Error

    {e}
    """

# =========================
# SEND TO TELEGRAM
# =========================

telegram_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

for i in range(0, len(script), 3500):

    requests.post(
        telegram_url,
        data={
            "chat_id": CHAT_ID,
            "text": script[i:i + 3500]
        }
    )

print("Market report sent successfully.")
