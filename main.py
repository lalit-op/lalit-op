import os
import requests
import yfinance as yf
import feedparser
import google.generativeai as genai

=========================

ENV VARIABLES

=========================

BOT_TOKEN = os.getenv("8664984432:AAHIEFLtjVYGVLK5FxXA7Z7COE7QXoiUli0")
CHAT_ID = os.getenv("5814384574")
GEMINI_API_KEY = os.getenv("AQ.Ab8RN6I2DfIBg3N2elIv6OooYTvAZ-6o5BPvrZ336peRegoY8A")

=========================

GEMINI CONFIG

=========================

genai.configure(api_key=GEMINI_API_KEY)

=========================

MARKET DATA

=========================

nifty = yf.Ticker("^NSEI")
sensex = yf.Ticker("^BSESN")

try:
nifty_close = round(
float(nifty.history(period="1d")["Close"].iloc[-1]),
2
)
except:
nifty_close = "Unavailable"

try:
sensex_close = round(
float(sensex.history(period="1d")["Close"].iloc[-1]),
2
)
except:
sensex_close = "Unavailable"

=========================

NEWS SOURCES

=========================

sources = [
"https://www.moneycontrol.com/rss/business.xml",
"https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
"https://economictimes.indiatimes.com/rssfeedsdefault.cms",
"https://www.business-standard.com/rss/markets-106.rss",
"https://www.livemint.com/rss/markets",
"https://www.financialexpress.com/market/feed/",
"https://www.cnbctv18.com/commonfeeds/v1/eng/rss/business.xml",
"https://www.zeebiz.com/india-markets/rss",
"https://www.reutersagency.com/feed/?best-topics=business-finance",
"https://finance.yahoo.com/rss/",
"https://feeds.content.dowjones.io/public/rss/mw_marketpulse",
"https://www.investing.com/rss/news.rss",
"https://www.sebi.gov.in/sebirss.xml"
]

=========================

FETCH HEADLINES

=========================

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

=========================

MASTER PROMPT

=========================

master_prompt = """
You are India's most trusted stock market analyst, financial journalist, and YouTube news anchor.

Create a complete 18-20 minute stock market news video.

Requirements:

1. Opening Hook
2. Market Wrap-Up
3. Nifty Analysis
4. Sensex Analysis
5. Top 10 Market Headlines
6. Sector Analysis
7. Top Gainers Analysis
8. Top Losers Analysis
9. Corporate News
10. Global Market Impact
11. FII DII Analysis
12. Technical Market View
13. Tomorrow Market Triggers
14. Investor Takeaways
15. Conclusion
16. Disclaimer

Generate:

- 3000 to 3500 word script
- SEO Title
- Thumbnail Text
- 300+ word Description
- 20 SEO Hashtags
- Pinned Comment
- Chapter Timestamps
- Top Search Keywords

Rules:

- Use only supplied market data
- Do not invent facts
- Professional financial anchor tone
- Beginner friendly
  """

prompt = f"""
{master_prompt}

TODAY'S MARKET DATA

Nifty Close: {nifty_close}

Sensex Close: {sensex_close}

LATEST MARKET HEADLINES

{news_text}
"""

=========================

GEMINI GENERATION

=========================

model = genai.GenerativeModel("gemini-2.5-flash")

response = model.generate_content(prompt)

script = response.text

=========================

SEND TO TELEGRAM

=========================

for i in range(0, len(script), 3500):
requests.post(
f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
data={
"chat_id": CHAT_ID,
"text": script[i:i + 3500]
}
)

print("Market report sent successfully.")
