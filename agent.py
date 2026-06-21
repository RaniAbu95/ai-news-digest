import json
import urllib.request
import xml.etree.ElementTree as ET

RSS_FEEDS = [
    "https://hnrss.org/frontpage",
    "https://www.reddit.com/r/MachineLearning/.rss",
    "https://www.reddit.com/r/artificial/.rss",
    "https://www.reddit.com/r/programming/.rss",
]

def fetch_articles() -> list[dict]:
    articles = []
    for url in RSS_FEEDS:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=10) as response:
                content = response.read().decode("utf-8")
            root = ET.fromstring(content)
            for item in root.findall(".//item")[:8]:
                title = item.findtext("title", "")
                summary = (item.findtext("description", "") or "")[:300]
                link = item.findtext("link", "")
                articles.append({"title": title, "summary": summary, "link": link})
        except Exception as e:
            print(f"שגיאה ב-{url}: {e}")
    return articles


def filter_and_summarize(articles: list[dict], gemini_api_key: str) -> str:
    articles_text = "\n\n".join([
        f"כותרת: {a['title']}\nתקציר: {a['summary']}\nקישור: {a['link']}"
        for a in articles
    ])

    prompt = f"""אתה עוזר שמסנן חדשות טכנולוגיה.

הנה רשימת כתבות מהיום:
{articles_text}

בחר 5-7 כתבות הכי רלוונטיות לתחום AI ופיתוח תוכנה.
כתוב דוח יומי בעברית בפורמט הבא:

📊 *Daily AI & Dev Digest*

*🔍 חדשות היום:*
• [כותרת] — [משפט תקציר] ([קישור])

*💡 Takeaway:*
[פסקה קצרה — מה המשמעות של החדשות האלה]

_⏱ {len(articles)} כתבות נסרקו_"""

    body = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}]
    }).encode("utf-8")

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_api_key}"
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as response:
        result = json.loads(response.read().decode("utf-8"))

    return result["candidates"][0]["content"]["parts"][0]["text"]


def send_telegram(text: str, bot_token: str, chat_id: str):
    body = json.dumps({
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown"
    }).encode("utf-8")
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{bot_token}/sendMessage",
        data=body,
        headers={"Content-Type": "application/json"}
    )
    urllib.request.urlopen(req)


def main():
    import os
    from dotenv import load_dotenv
    load_dotenv()
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    print("מאסף כתבות...")
    articles = fetch_articles()
    print(f"נמצאו {len(articles)} כתבות")

    print("מסנן ומסכם עם Gemini...")
    digest = filter_and_summarize(articles, gemini_api_key)

    print("שולח ל-Telegram...")
    send_telegram(digest, bot_token, chat_id)
    print("נשלח!")

if __name__ == "__main__":
    main()
