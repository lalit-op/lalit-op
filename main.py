import os

from datetime import datetime

import requests

import yfinance as yf

import feedparser

import google.generativeai as genai

# ==================================================

# ENV VARIABLES

# ==================================================

BOT_TOKEN = os.getenv("BOT_TOKEN")

CHAT_ID = os.getenv("CHAT_ID")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

CONTENT_TYPE = os.getenv("CONTENT_TYPE", "video")

BLOG_ID = os.getenv("BLOG_ID")

CLIENT_ID = os.getenv("CLIENT_ID")

CLIENT_SECRET = os.getenv("CLIENT_SECRET")

REFRESH_TOKEN = os.getenv("REFRESH_TOKEN")

# ==================================================

# GEMINI CONFIG

# ==================================================

genai.configure(api_key=GEMINI_API_KEY)

# ==================================================

# MARKET DATA

# ==================================================

def get_market_data():

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



    return nifty_close, sensex_close

# ==================================================

# NEWS SOURCES

# ==================================================

SOURCES = [

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

# ==================================================

# FETCH NEWS

# ==================================================

def fetch_news():

    headlines = []



    for source in SOURCES:

        try:

            feed = feedparser.parse(source)



            for item in feed.entries[:15]:

                title = item.title.strip()



                if title not in headlines:

                    headlines.append(title)



        except Exception as e:

            print(f"Error reading {source}: {e}")



    return "\n".join(headlines[:100])

# ==================================================

# CONTENT PROMPT

# ==================================================

def build_prompt(nifty_close, sensex_close, news_text):

    if CONTENT_TYPE.lower() == "short":



        master_prompt = """

आप भारत के सबसे भरोसेमंद शेयर बाजार न्यूज़ एंकर हैं।

आज की खबरों और बाजार डेटा के आधार पर

45-60 सेकंड का वायरल YouTube Short बनाइए।

Format:

1. दमदार Hook


2. मुख्य खबर


3. निवेशकों पर प्रभाव


4. Conclusion



Generate:

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

3000-3500 शब्द।

केवल उपलब्ध बाजार डेटा और हेडलाइंस का उपयोग करें।

कोई झूठी जानकारी न दें।

"""

    return f"""

{master_prompt}

आज का बाजार डेटा

Nifty Close: {nifty_close}

Sensex Close: {sensex_close}

आज की प्रमुख खबरें:

{news_text}

"""

# ==================================================

# BLOGGER PUBLISH

# ==================================================

def publish_to_blogger(title, content):

    try:

        # Get fresh access token

        token_response = requests.post(

            "https://oauth2.googleapis.com/token",

            data={

                "client_id": CLIENT_ID,

                "client_secret": CLIENT_SECRET,

                "refresh_token": REFRESH_TOKEN,

                "grant_type": "refresh_token"

            },

            timeout=30

        )



        token_response.raise_for_status()



        token_data = token_response.json()



        if "access_token" not in token_data:

            print("Token Error:", token_data)

            return



        access_token = token_data["access_token"]



        # Blogger post payload

        post_data = {

            "kind": "blogger#post",

            "title": title,

            "content": content.replace("\n", "<br>")

        }



        # Publish post to Blogger

        response = requests.post(

            f"https://www.googleapis.com/blogger/v3/blogs/{BLOG_ID}/posts",

            headers={

                "Authorization": f"Bearer {access_token}",

                "Content-Type": "application/json"

            },

            json=post_data,

            timeout=30

        )



        print("Blogger Status:", response.status_code)

        print("Blogger Response:", response.text)

        response.raise_for_status()



        if response.status_code not in [200, 201]:

            print("❌ Blogger Post Failed")

            print("Response:", response.text)

        else:

            print("✅ Blogger Post Published")

            print("Post URL:", response.json().get("url", "Not Available"))



    except Exception as e:

        print("Blogger Publish Error:", e)

# ==================================================

# TELEGRAM SEND

# ==================================================

def send_to_telegram(message):

    telegram_url = (

        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    )



    for i in range(0, len(message), 3500):

        requests.post(

            telegram_url,

            data={

                "chat_id": CHAT_ID,

                "text": message[i:i + 3500]

            },

            timeout=30

        )

# ==================================================

# MAIN

# ==================================================

def main():

    required_vars = [

        BOT_TOKEN,

        CHAT_ID,

        GEMINI_API_KEY,

        BLOG_ID,

        CLIENT_ID,

        CLIENT_SECRET,

        REFRESH_TOKEN

    ]



    if not all(required_vars):

        print("❌ One or more environment variables are missing.")

        return



    nifty_close, sensex_close = get_market_data()



    news_text = fetch_news()



    prompt = build_prompt(

        nifty_close,

        sensex_close,

        news_text

    )



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



        publish_to_blogger(

            title=title,

            content=script

        )



        send_to_telegram(script)



    except Exception as e:



        script = f"""

❌ Gemini Error

{e}

"""

        send_to_telegram(script)



    print("Market report sent successfully.")

# ==================================================

# RUN SCRIPT

# ==================================================

if __name__ == "__main__":
    main()
