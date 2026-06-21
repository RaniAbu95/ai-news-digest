import feedparser
import httpx
from google import genai

RSS_FEEDS = [
    "https://hnrss.org/frontpage",
    "https://www.reddit.com/r/MachineLearning/.rss",
    "https://www.reddit.com/r/artificial/.rss",
    "https://www.reddit.com/r/programming/.rss",
]

def fetch_articles() -> list[dict]:
    import ssl
    import certifi
    articles = []
    for url in RSS_FEEDS:
        try:
            response = httpx.get(url, timeout=10, verify=certifi.where())
            feed = feedparser.parse(response.text)
            for entry in feed.entries[:8]:
                articles.append({
                    "title": entry.get("title", ""),
                    "summary": entry.get("summary", "")[:300],
                    "link": entry.get("link", "")
                })
        except Exception as e:
            print(f"שגיאה ב-{url}: {e}")
    return articles


def filter_and_summarize(articles: list[dict], gemini_api_key: str) -> str:
    client = genai.Client(api_key=gemini_api_key)
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

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    return response.text

def send_telegram(text: str, bot_token: str, chat_id: str):
    httpx.post(
        f"https://api.telegram.org/bot{bot_token}/sendMessage",
        json={
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "Markdown"
        }
    )

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
