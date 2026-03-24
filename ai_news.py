import feedparser
import requests
import json
from datetime import datetime
from pathlib import Path

KEYWORDS = [
    "yapay zeka", "artificial intelligence", "AI", "LLM",
    "ajan", "agent", "ChatGPT", "Claude", "Gemini",
    "makine öğrenmesi", "derin öğrenme"
]

RSS_FEEDS = [
    "https://news.google.com/rss/search?q=yapay+zeka&hl=tr&gl=TR&ceid=TR:tr",
    "https://news.google.com/rss/search?q=artificial+intelligence&hl=tr&gl=TR&ceid=TR:tr",
    "https://news.google.com/rss/search?q=LLM+AI&hl=tr&gl=TR&ceid=TR:tr",
]

def fetch_news():
    results = []
    seen = set()
    for url in RSS_FEEDS:
        feed = feedparser.parse(url)
        for entry in feed.entries[:10]:
            title = entry.get("title", "")
            link = entry.get("link", "")
            if link in seen:
                continue
            seen.add(link)
            if any(kw.lower() in title.lower() for kw in KEYWORDS):
                results.append({
                    "title": title,
                    "link": link,
                    "published": entry.get("published", "")
                })
    return results

def send_to_telegram(news_list):
    env_path = Path(".env")
    token = ""
    chat_id = ""
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if line.startswith("TELEGRAM_BOT_TOKEN="):
                token = line.split("=", 1)[1].strip()
            elif line.startswith("TELEGRAM_CHAT_ID="):
                chat_id = line.split("=", 1)[1].strip()
    if not token or not chat_id:
        print("Telegram bilgileri bulunamadi!")
        return
    if not news_list:
        print("Haber bulunamadi.")
        return
    msg = "🤖 *Günün Yapay Zeka Haberleri*\n"
    msg += datetime.now().strftime("%d.%m.%Y") + "\n"
    msg += "─" * 30 + "\n\n"
    for i, item in enumerate(news_list[:10], 1):
        msg += f"{i}. [{item['title']}]({item['link']})\n\n"
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    requests.post(url, json={
        "chat_id": chat_id,
        "text": msg,
        "parse_mode": "Markdown",
        "disable_web_page_preview": False
    })
    print(f"{len(news_list)} haber gonderildi.")

if __name__ == "__main__":
    print("Haberler taranıyor...")
    news = fetch_news()
    print(f"{len(news)} haber bulundu.")
    send_to_telegram(news)
