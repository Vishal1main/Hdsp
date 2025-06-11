from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Dispatcher, MessageHandler, Filters
from bs4 import BeautifulSoup
import requests
import os

# Bot setup
BOT_TOKEN = os.getenv("BOT_TOKEN") or "7861502352:AAFcS7xZk2NvN7eJ3jcPm_HyYh74my8vRyU"
bot = Bot(token=BOT_TOKEN)
app = Flask(__name__)

# Dispatcher for handling updates
dispatcher = Dispatcher(bot, None, workers=0, use_context=True)

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

    return f"<b>{title}</b>\n\n" + "\n\n".join(links)

def handle_message(update, context):
    text = update.message.text
    if text.startswith("http") and "hdhub4u" in text:
        context.bot.send_message(chat_id=update.effective_chat.id, text="🔍 Scraping the post...")
        try:
            reply = scrape_hdhub4u_post(text)
            context.bot.send_message(chat_id=update.effective_chat.id, text=reply, parse_mode="HTML", disable_web_page_preview=True)
        except Exception as e:
            context.bot.send_message(chat_id=update.effective_chat.id, text=f"⚠️ Error: {str(e)}")
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text="❗Please send a valid HDHub4U post URL.")

# Register message handler
dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

# Webhook route
@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return "OK"

# Root route (optional)
@app.route("/", methods=["GET"])
def index():
    return "Bot is running!"

if __name__ == "__main__":
    PORT = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=PORT)
