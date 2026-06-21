# AI News Digest Agent

## מה זה
סוכן Python שרץ אוטומטית כל בוקר — אוסף חדשות AI ופיתוח תוכנה, מנתח עם Gemini, ושולח דוח יומי ל-Telegram.

## Tech Stack
- **AI:** Gemini 2.5 Flash (Google AI Studio API — httpx ישיר)
- **Scheduling:** GitHub Actions Cron (07:00 ישראל = 05:00 UTC, ימים א'-ה')
- **Output:** Telegram Bot API

## מבנה הפרויקט
```
ai-news-digest/
├── agent.py                          ← Agent Loop + 5 Tools
├── .github/workflows/daily-digest.yml ← GitHub Actions Cron
└── CLAUDE.md
```

## Agent Loop
הסוכן מיושם ידנית (ללא LangChain/AutoGen):
1. שולח task ל-Gemini עם הגדרות ה-Tools
2. Gemini מחליט איזה Tool לקרוא
3. מריץ את ה-Tool ומחזיר תוצאה
4. חוזר עד שGemini קורא ל-`send_telegram_report`
5. max_iterations=15 — שגיאה נשלחת ל-Telegram

## Tools (5)
| Tool | תיאור |
|------|-------|
| `fetch_hacker_news` | חדשות מ-Hacker News |
| `fetch_reddit_posts` | פוסטים מ-subreddit |
| `fetch_rss_feed` | כתבות מ-RSS URL |
| `get_current_date` | תאריך נוכחי |
| `send_telegram_report` | שולח דוח סופי ל-Telegram |

## Environment Variables
```
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHAT_ID=...
GEMINI_API_KEY=...
```
מוגדרים ב-GitHub Secrets (Settings ← Secrets and variables ← Actions)

## עלויות
- Gemini 2.5 Flash: ~$0.007 לריצה (~$1/חודש)
- GitHub Actions: חינם
- Telegram Bot API: חינם
- **סה"כ: ~$1/חודש**

## הרצה מקומית
```bash
python3 -m venv venv
source venv/bin/activate
pip install httpx feedparser python-dotenv certifi
python3 agent.py
```
