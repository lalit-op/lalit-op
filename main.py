import os
from datetime import datetime
import feedparser
import requests
import yfinance as yf
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
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# =========================
# HELPER FUNCTIONS
# =========================

def get_market_data():
    """Fetches Nifty and Sensex close prices."""
    try:
        nifty = yf.Ticker("^NSEI")
        nifty_close = round(float(nifty.history(period="5d")["Close"].iloc[-1]), 2)
    except Exception:
        nifty_close = "Unavailable"

    try:
        sensex = yf.Ticker("^BSESN")
        sensex_close = round(float(sensex.history(period="5d")["Close"].iloc[-1]), 2)
    except Exception:
        sensex_close = "Unavailable"
        
    return nifty_close, sensex_close

def fetch_news_headlines():
    """Fetches top 100 unique headlines from various RSS feeds."""
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

    return "\n".join(headlines[:100])

def generate_index():
    """Generates the Indian Market AI homepage."""

    os.makedirs("posts", exist_ok=True)

    files = [
        f for f in os.listdir("posts")
        if f.endswith(".html") and f != "index.html"
    ]

    files.sort(reverse=True)

    cards = ""

    for file in files:

        date_str = file.replace(".html", "")

        cards += f"""
        <article class="report-card">

            <div class="report-info">

                <a
                    href="{file}"
                    class="report-title"
                >
                    📄 Daily Market Script - {date_str}
                </a>

                <div class="report-date">
                    📅 Published on {date_str}
                </div>

            </div>

            <a
                href="{file}"
                class="open-button"
                aria-label="Open report"
            >
                →
            </a>

        </article>
        """

    html = f"""<!DOCTYPE html>

<html lang="en">

<head>

<meta charset="UTF-8">

<meta
    name="viewport"
    content="width=device-width, initial-scale=1.0"
>

<meta
    name="theme-color"
    content="#020617"
>

<title>
    Stock Samvad AI | Daily Market Reports
</title>


<style>

* {{
    box-sizing: border-box;
}}


html,
body {{

    margin: 0;

    padding: 0;

    width: 100%;

    min-height: 100%;

}}


body {{

    font-family:
        Inter,
        -apple-system,
        BlinkMacSystemFont,
        "Segoe UI",
        Arial,
        sans-serif;

    background:
        radial-gradient(
            circle at top left,
            #1e3a8a55,
            transparent 40%
        ),

        radial-gradient(
            circle at top right,
            #06b6d455,
            transparent 40%
        ),

        #020617;

    color: #e2e8f0;

    min-height: 100vh;

}}


.container {{

    width: 100%;

    max-width: 1100px;

    margin: auto;

    padding: 25px;

}}


/* ==============================
   HEADER
============================== */

.header {{

    text-align: center;

    padding: 45px 25px;

    margin-bottom: 25px;

    border-radius: 24px;

    background:
        rgba(255,255,255,0.05);

    border:
        1px solid
        rgba(255,255,255,0.08);

    backdrop-filter:
        blur(20px);

}}


.badge {{

    display: inline-block;

    padding: 9px 17px;

    border-radius: 999px;

    color: #38bdf8;

    background:
        rgba(14,165,233,0.10);

    border:
        1px solid
        rgba(56,189,248,0.25);

    font-size: 14px;

    margin-bottom: 15px;

}}


.header h1 {{

    margin: 10px 0;

    font-size:
        clamp(38px, 7vw, 64px);

    line-height: 1.1;

    background:
        linear-gradient(
            90deg,
            #38bdf8,
            #22c55e,
            #facc15
        );

    -webkit-background-clip: text;

    -webkit-text-fill-color: transparent;

}}


.subtitle {{

    color: #94a3b8;

    font-size:
        clamp(15px, 3vw, 19px);

}}


/* ==============================
   AUTOMATION
============================== */

.automation-box {{

    display: flex;

    align-items: center;

    justify-content: space-between;

    gap: 18px;

    margin-bottom: 25px;

    padding: 18px 20px;

    border-radius: 18px;

    background:
        rgba(15,23,42,0.85);

    border:
        1px solid
        rgba(56,189,248,0.18);

}}


.automation-title {{

    color: #f8fafc;

    font-size: 16px;

    font-weight: 700;

}}


.automation-text {{

    margin-top: 4px;

    color: #64748b;

    font-size: 12px;

}}


.run-button {{

    flex-shrink: 0;

    display: inline-flex;

    align-items: center;

    justify-content: center;

    padding: 10px 16px;

    border-radius: 10px;

    color: white;

    background: #238636;

    border: 1px solid #2ea043;

    text-decoration: none;

    font-size: 13px;

    font-weight: 700;

    transition: 0.2s ease;

}}


.run-button:hover {{

    background: #2ea043;

}}


/* ==============================
   ARCHIVE
============================== */

.section-label {{

    color: #38bdf8;

    font-size: 13px;

    font-weight: 800;

    letter-spacing: 0.15em;

    margin-bottom: 8px;

}}


.section-title {{

    margin: 0 0 20px;

    font-size:
        clamp(30px, 5vw, 44px);

    color: #f8fafc;

}}


/* ==============================
   REPORT CARD
============================== */

.report-card {{

    display: flex;

    align-items: center;

    justify-content: space-between;

    gap: 15px;

    margin-bottom: 15px;

    padding: 22px;

    border-radius: 20px;

    background:
        rgba(15,23,42,0.85);

    border:
        1px solid
        rgba(255,255,255,0.08);

    transition:
        transform 0.2s ease,
        border-color 0.2s ease;

}}


.report-card:hover {{

    transform:
        translateY(-3px);

    border-color:
        rgba(56,189,248,0.35);

}}


.report-info {{

    min-width: 0;

}}


.report-title {{

    color: #38bdf8;

    text-decoration: none;

    font-size:
        clamp(18px, 3vw, 25px);

    font-weight: 700;

}}


.report-date {{

    margin-top: 8px;

    color: #94a3b8;

    font-size: 14px;

}}


.open-button {{

    width: 52px;

    height: 52px;

    flex-shrink: 0;

    display: flex;

    align-items: center;

    justify-content: center;

    border-radius: 50%;

    color: #38bdf8;

    border:
        1px solid
        rgba(56,189,248,0.35);

    text-decoration: none;

    font-size: 28px;

}}


/* ==============================
   MOBILE
============================== */

@media (max-width: 600px) {{

    .container {{

        padding: 15px;

    }}


    .header {{

        padding: 30px 15px;

    }}


    .automation-box {{

        flex-direction: column;

        align-items: stretch;

        padding: 16px;

    }}


    .run-button {{

        width: 100%;

    }}


    .report-card {{

        padding: 17px;

    }}


    .open-button {{

        width: 44px;

        height: 44px;

        font-size: 23px;

    }}

}}

</style>

</head>


<body>


<div class="container">


    <!-- HEADER -->

    <div class="header">

        <div class="badge">

            🇮🇳 AI-Powered Indian Market Intelligence

        </div>

        <h1>

            Stock Samvad AI

        </h1>

        <div class="subtitle">

            Daily Nifty, Sensex & Indian Stock Market Reports

        </div>

    </div>


    <!-- AUTOMATION -->

    <div class="automation-box">

        <div>

            <div class="automation-title">

                ⚙️ Indian Market Automation

            </div>

            <div class="automation-text">

                Generate the latest Indian market script

            </div>

        </div>


        <a
            href="https://github.com/lalit-op/lalit-op/actions/workflows/market_news.yml"
            target="_blank"
            rel="noopener noreferrer"
            class="run-button"
        >

            ▶ Run Workflow

        </a>

    </div>


    <!-- ARCHIVE -->

    <div class="section-label">

        ARCHIVE

    </div>


    <h2 class="section-title">

        Daily Indian Market Reports

    </h2>


    {cards}


</div>


</body>

</html>
"""

    with open(
        "posts/index.html",
        "w",
        encoding="utf-8"
    ) as f:

        f.write(html)

    print("Updated posts/index.html")

def save_post(title, content):
    """Generates a mobile-optimized HTML page for the individual script."""
    os.makedirs("posts", exist_ok=True)
    filename = datetime.now().strftime("%Y-%m-%d") + ".html"
    filepath = os.path.join("posts", filename)

    # MOBILE OPTIMIZED HTML (Added @media queries)
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<style>
:root {{
    --bg:#020617; --card:#0f172a; --border:#1e293b; --text:#e2e8f0; --muted:#94a3b8;
}}
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{
    font-family:'Inter',sans-serif;
    background: radial-gradient(circle at top left,#1e3a8a33,transparent 40%),
                radial-gradient(circle at top right,#06b6d433,transparent 40%),
                #020617;
    color:var(--text); min-height:100vh;
}}
.container {{ max-width:1200px; margin:auto; padding:30px; }}
.header {{
    text-align:center; padding:40px; border-radius:24px; margin-bottom:25px;
    background:rgba(255,255,255,.05); backdrop-filter:blur(20px); border:1px solid rgba(255,255,255,.08);
}}
.badge {{
    display:inline-block; padding:8px 16px; border-radius:999px;
    background:#0ea5e920; border:1px solid #38bdf830; color:#38bdf8; margin-bottom:15px; font-size:14px;
}}
.header h1 {{
    font-size:48px; font-weight:700;
    background:linear-gradient(90deg, #38bdf8, #22c55e, #facc15);
    -webkit-background-clip:text; -webkit-text-fill-color:transparent; line-height: 1.2;
}}
.header p {{ margin-top:10px; color:#94a3b8; }}
.tagline {{ font-size:18px; color:#38bdf8; margin-top:10px; }}
.toolbar {{ display:flex; justify-content:flex-end; margin-bottom:20px; }}
.copy-btn {{
    background:linear-gradient(135deg, #2563eb, #06b6d4); color:white; border:none;
    padding:14px 24px; border-radius:14px; cursor:pointer; font-weight:600; transition: all 0.2s;
}}
.copy-btn:hover {{ transform:translateY(-2px); box-shadow:0 0 20px rgba(6,182,212,.5); }}
.card {{
    background:rgba(15,23,42,.85); border:1px solid rgba(255,255,255,.08);
    border-radius:24px; overflow:hidden; backdrop-filter:blur(20px); box-shadow:0 25px 60px rgba(0,0,0,.45);
}}
.card-top {{ display:flex; align-items:center; padding:15px 20px; border-bottom:1px solid rgba(255,255,255,.08); }}
.dots {{ display:flex; gap:8px; }}
.dot {{ width:14px; height:14px; border-radius:50%; }}
.red {{ background:#ff5f57; }} .yellow {{ background:#ffbd2e; }} .green {{ background:#28c840; }}
.file-name {{ margin-left:15px; color:#94a3b8; font-size:14px; }}
pre {{
    white-space:pre-wrap; word-wrap:break-word; padding:30px; line-height:1.8;
    font-size:16px; color:#e2e8f0; font-family:'Inter', sans-serif;
}}
.footer {{ text-align:center; margin-top:30px; color:#64748b; font-size: 14px; padding-bottom: 20px; }}
.toast {{
    position:fixed; bottom:25px; right:25px; background:#22c55e; color:white;
    padding:12px 20px; border-radius:12px; display:none; z-index: 50; box-shadow:0 10px 30px rgba(34,197,94,.3);
}}

/* ========================================= */
/* MOBILE OPTIMIZATION (@media query added)  */
/* ========================================= */
@media (max-width: 768px) {{
    .container {{ padding: 15px; }}
    .header {{ padding: 25px 15px; border-radius: 20px; }}
    .header h1 {{ font-size: 32px; }}
    .tagline {{ font-size: 15px; }}
    .toolbar {{ justify-content: center; }}
    .copy-btn {{ width: 100%; padding: 16px; font-size: 16px; }}
    .card {{ border-radius: 16px; }}
    .card-top {{ flex-direction: row; justify-content: space-between; }}
    .file-name {{ margin-left: 10px; font-size: 12px; }}
    pre {{ padding: 20px 15px; font-size: 15px; }}
    .toast {{ left: 50%; right: auto; transform: translateX(-50%); width: 90%; text-align: center; bottom: 20px; }}
}}
</style>
</head>
<body>
<div class="container">
    <div class="header">
        <div class="badge">🚀 AI Generated Market Report</div>
        <h1>📈 Stock Samvad AI</h1>
        <p class="tagline">Daily Market Intelligence Platform</p>
    </div>
    <div class="toolbar">
        <button class="copy-btn" onclick="copyScript()">📋 Copy Full Script</button>
    </div>
    <div class="card">
        <div class="card-top">
            <div class="dots">
                <span class="dot red"></span><span class="dot yellow"></span><span class="dot green"></span>
            </div>
            <div class="file-name">📊 Daily Market Analysis</div>
        </div>
        <pre id="script">{content}</pre>
    </div>
    <div class="footer">
        🚀 Stock Samvad AI | Daily Stock Market Reports | Powered by Gemini
    </div>
</div>
<div id="toast" class="toast">Script Copied Successfully ✅</div>
<script>
function copyScript(){{
    const text = document.getElementById("script").innerText;
    navigator.clipboard.writeText(text).then(() => {{
        const toast = document.getElementById("toast");
        toast.style.display = "block";
        setTimeout(() => {{ toast.style.display="none"; }}, 2500);
    }}).catch(err => {{
        console.error('Failed to copy: ', err);
    }});
}}
</script>
</body>
</html>"""

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html_content)
    print("Saved:", filepath)

def send_to_telegram(script):
    """Sends the generated script to Telegram in chunks to avoid length limits."""
    if not BOT_TOKEN or not CHAT_ID:
        print("Telegram BOT_TOKEN or CHAT_ID missing. Skipping Telegram notification.")
        return

    telegram_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    
    # Telegram max message length is 4096. Sending in chunks of 3500.
    for i in range(0, len(script), 3500):
        try:
            requests.post(
                telegram_url,
                data={
                    "chat_id": CHAT_ID,
                    "text": script[i:i + 3500]
                }
            )
        except Exception as e:
            print(f"Error sending to Telegram: {e}")
    print("Market report processed for Telegram.")


# =========================
# MAIN EXECUTION
# =========================

def main():
    print("Fetching market data...")
    nifty_close, sensex_close = get_market_data()
    
    print("Fetching news headlines...")
    news_text = fetch_news_headlines()

    # Dynamic Prompts based on Content Type
    if CONTENT_TYPE == "short":
        master_prompt = """
        आप भारत के सबसे भरोसेमंद शेयर बाजार न्यूज़ एंकर हैं।
        आज की खबरों और बाजार डेटा के आधार पर 45-60 सेकंड का वायरल YouTube Short बनाइए।
        Format:
        1. दमदार Hook
        2. मुख्य खबर
        3. निवेशकों पर प्रभाव
        4. Conclusion

        साथ में Generate करें: Shorts Title, Thumbnail Text, Description, 10 Hashtags. पूरी स्क्रिप्ट हिंदी में हो।
        """
    else:
        master_prompt = """
        आप भारत के सबसे भरोसेमंद शेयर बाजार विश्लेषक और यूट्यूब न्यूज एंकर हैं।
        आज के बाजार डेटा और खबरों के आधार पर 18-20 मिनट की विस्तृत हिंदी वीडियो स्क्रिप्ट तैयार करें।
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

        साथ में दें: SEO Title, Thumbnail Text, Description, 20 Hashtags, Pinned Comment, Chapter Timestamps.
        पूरी स्क्रिप्ट हिंदी में लिखें।
        लंबाई: 3000-3500 शब्द। केवल उपलब्ध बाजार डेटा और हेडलाइंस का उपयोग करें। कोई झूठी जानकारी न दें।
        """

    prompt = f"""
{master_prompt}

आज का बाजार डेटा
Nifty Close: {nifty_close}
Sensex Close: {sensex_close}

आज की प्रमुख खबरें:
{news_text}
"""

    today = datetime.now().strftime("%d-%m-%Y")
    
    # Gemini Generation
    if not GEMINI_API_KEY:
        print("GEMINI_API_KEY is missing. Aborting generation.")
        return

    print("Generating AI Script with Gemini...")
    model = genai.GenerativeModel("gemini-3.6-flash")
    
    try:
        response = model.generate_content(prompt)
        script = f"\n📅 दिनांक: {today}\n📊 Content Type: {CONTENT_TYPE.upper()}\n\n{response.text}\n"
        title = f"Daily Stock Market Script - {today}"
        
        save_post(title, script)
        generate_index()
        send_to_telegram(script)

    except Exception as e:
        error_msg = f"❌ Gemini Error\n{e}"
        print(error_msg)
        send_to_telegram(error_msg)

if __name__ == "__main__":
    main()
