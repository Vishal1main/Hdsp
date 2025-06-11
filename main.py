from telegram.ext import Updater, MessageHandler, Filters
from bs4 import BeautifulSoup
import requests
import os

BOT_TOKEN = os.getenv("BOT_TOKEN") or "7861502352:AAFcS7xZk2NvN7eJ3jcPm_HyYh74my8vRyU"
PORT = int(os.environ.get("PORT", 8443))
WEBHOOK_URL = os.getenv("WEBHOOK_URL") or f"https://hdsp.onrender.com"  # Your deployed domain

def scrape_hdhub4u_post(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.content, 'html.parser')

    title_tag = soup.find("h1")
    title = title_tag.text.strip() if title_tag else "🎬 Movie Details"

    links = []
    for a in soup.find_all("a", href=True):
        text = a.get_text(strip=True)
        href = a['href']
        if any(p in text.lower() for p in ['480p', '720p', '1080p', 'download']) and href.startswith("http"):
            links.append(f"🔗 <b>{text}</b>\n<a href='{href}'>{href}</a>")

    if not links:
        return "❌ No download links found."

    message = f"<b>{title}</b>\n\n" + "\n\n".join(links)
    return message

def handle_message(update, context):
    text = update.message.text
    if text.startswith("http") and "hdhub4u" in text:
        update.message.reply_text("🔍 Scraping the post...", quote=True)
        try:
            reply = scrape_hdhub4u_post(text)
            update.message.reply_text(reply, parse_mode="HTML", disable_web_page_preview=True)
        except Exception as e:
            update.message.reply_text(f"⚠️ Error: {str(e)}")
    else:
        update.message.reply_text("❗Please send a valid HDHub4U post URL.")

def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    # Webhook mode
    updater.start_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=BOT_TOKEN,
        webhook_url=f"{WEBHOOK_URL}/{BOT_TOKEN}"
    )
    updater.idle()

if __name__ == "__main__":
    main()
