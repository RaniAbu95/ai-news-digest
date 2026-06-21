from agent import fetch_articles, filter_and_summarize, send_telegram

async def on_scheduled(event, env, ctx):
    secrets = {
        "GEMINI_API_KEY": env.GEMINI_API_KEY,
        "TELEGRAM_BOT_TOKEN": env.TELEGRAM_BOT_TOKEN,
        "TELEGRAM_CHAT_ID": env.TELEGRAM_CHAT_ID,
    }
    try:
        articles = fetch_articles()
        digest = filter_and_summarize(articles, secrets["GEMINI_API_KEY"])
        send_telegram(digest, secrets["TELEGRAM_BOT_TOKEN"], secrets["TELEGRAM_CHAT_ID"])
    except Exception as e:
        send_telegram(f"⚠️ Agent failed: {e}", secrets["TELEGRAM_BOT_TOKEN"], secrets["TELEGRAM_CHAT_ID"])
