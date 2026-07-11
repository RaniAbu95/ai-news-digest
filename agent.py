import os
import httpx
import feedparser
import certifi
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"

total_tokens = 0

def log_tool_call(name, args, result):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] TOOL: {name} | {str(result)[:80]}...")

def fetch_hacker_news(limit=10):
    feed = feedparser.parse(httpx.get("https://hnrss.org/frontpage", verify=certifi.where(), timeout=30).text)
    return "\n".join([f"{e.title} — {e.link}" for e in feed.entries[:limit]])

def fetch_reddit_posts(subreddit, limit=8):
    url = f"https://www.reddit.com/r/{subreddit}/.rss"
    feed = feedparser.parse(httpx.get(url, headers={"User-Agent": "Mozilla/5.0"}, verify=certifi.where(), timeout=30).text)
    return "\n".join([f"{e.title} — {e.link}" for e in feed.entries[:limit]])

def fetch_rss_feed(url):
    feed = feedparser.parse(httpx.get(url, verify=certifi.where(), timeout=30).text)
    return "\n".join([f"{e.title} — {e.link}" for e in feed.entries[:8]])

def get_current_date():
    return datetime.now().strftime("%d/%m/%Y")

def send_telegram_report(title, items, takeaway):
    cost = round(total_tokens * 0.000000075, 6)
    text = f"📊 {title}\n\nחדשות היום:\n{items}\n\nTakeaway:\n{takeaway}\n\nעלות: ${cost} | {total_tokens} tokens"
    response = httpx.post(
        f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
        json={"chat_id": TELEGRAM_CHAT_ID, "text": text}
    )
    print(f"Telegram response: {response.json()}")
    return "Report sent successfully"


TOOL_FUNCTIONS = {
    "fetch_hacker_news": fetch_hacker_news,
    "fetch_reddit_posts": fetch_reddit_posts,
    "fetch_rss_feed": fetch_rss_feed,
    "get_current_date": get_current_date,
    "send_telegram_report": send_telegram_report,
}

TOOLS = [{
    "function_declarations": [
        {"name": "fetch_hacker_news", "description": "מביא כתבות טרנדיות מ-Hacker News", "parameters": {"type": "object", "properties": {"limit": {"type": "integer"}}}},
        {"name": "fetch_reddit_posts", "description": "מביא פוסטים מ-subreddit ב-Reddit", "parameters": {"type": "object", "properties": {"subreddit": {"type": "string"}, "limit": {"type": "integer"}}, "required": ["subreddit"]}},
        {"name": "fetch_rss_feed", "description": "מביא כתבות מ-RSS Feed לפי URL", "parameters": {"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"]}},
        {"name": "get_current_date", "description": "מחזיר את התאריך הנוכחי", "parameters": {"type": "object", "properties": {}}},
        {"name": "send_telegram_report", "description": "שולח את הדוח הסופי ל-Telegram. קרא רק בסוף אחרי שאספת את כל המידע", "parameters": {"type": "object", "properties": {"title": {"type": "string"}, "items": {"type": "string"}, "takeaway": {"type": "string"}}, "required": ["title", "items", "takeaway"]}},
    ]
}]

def call_gemini(messages, retries=3):
    global total_tokens
    for attempt in range(retries):
        try:
            response = httpx.post(GEMINI_URL, json={"contents": messages, "tools": TOOLS}, timeout=120)
            break
        except httpx.TimeoutException:
            if attempt == retries - 1:
                raise
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Gemini timed out, retrying ({attempt + 1}/{retries})")
    data = response.json()
    if "error" in data:
        raise Exception(data["error"]["message"])
    total_tokens += data.get("usageMetadata", {}).get("totalTokenCount", 0)
    return data["candidates"][0]["content"]

def agent_loop(task, max_iterations=15):
    messages = [{"role": "user", "parts": [{"text": task}]}]
    for i in range(max_iterations):
        content = call_gemini(messages)
        messages.append(content)
        fn_calls = [p for p in content["parts"] if "functionCall" in p]
        if not fn_calls:
            return content["parts"][0].get("text", "Done")
        tool_results = []
        for part in fn_calls:
            fn = part["functionCall"]
            args = fn.get("args", {})
            func = TOOL_FUNCTIONS.get(fn["name"])
            try:
                result = func(**args) if func else f"Unknown tool: {fn['name']}"
            except Exception as e:
                result = f"Tool failed: {e}. Continue with other sources."
            log_tool_call(fn["name"], args, result)
            tool_results.append({"functionResponse": {"name": fn["name"], "response": {"result": result}}})
        messages.append({"role": "user", "parts": tool_results})
    raise RuntimeError(f"Agent exceeded {max_iterations} iterations")

def main():
    task = """אתה סוכן AI שמכין דוח חדשות יומי בנושא AI ופיתוח תוכנה.
1. קבל את התאריך הנוכחי
2. שלוף חדשות מ-Hacker News
3. שלוף פוסטים מ-Reddit r/MachineLearning 
4. שלוף פוסטים מ-Reddit r/artificial 
5. בחר 5-7 פריטים הכי מעניינים
6. שלח דוח מסודר ל-Telegram בעברית"""
    try:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Agent started")
        agent_loop(task)
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Done | tokens: {total_tokens}")
    except Exception as e:
        msg = f"⚠️ Agent failed: {e}"
        print(msg)
        httpx.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                   json={"chat_id": TELEGRAM_CHAT_ID, "text": msg})

if __name__ == "__main__":
    main()
