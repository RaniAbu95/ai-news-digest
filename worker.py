from agent import fetch_articles, filter_and_summarize, send_telegram
import os

async def on_scheduled(event, env, ctx):
    try:
        articles = fetch_articles()
        digest = filter_and_summarize(articles)
        send_telegram(digest)
    except Exception as e:
        send_telegram(f"⚠️ Agent failed: {e}")
