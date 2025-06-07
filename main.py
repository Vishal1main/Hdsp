import os
import logging
from flask import Flask, request
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler
from bs4 import BeautifulSoup
import requests

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Flask app for webhook
app = Flask(__name__)

# Environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # Example: https://yourbot.onrender.com

# Telegram application
application = ApplicationBuilder().token(BOT_TOKEN).build()

# Command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send me a movie post URL to extract download links.")

# Scraper function
def scrape_links(url):
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.content, "html.parser")
        links = soup.find_all("a", href=True)

        download_links = []
        for link in links:
            href = link['href']
            text = link.get_text(strip=True)
            if href.startswith("http") and any(x in text.lower() for x in ["480p", "720p", "1080p", "4k", "web", "watch"]):
                download_links.append(f"<b>{text}</b>\n{href}")

        return "\n\n".join(download_links) if download_links else "No download links found."
    except Exception as e:
        return f"Error: {e}"

# Message handler
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    if url.startswith("http"):
        await update.message.reply_text("Scraping links, please wait...")
        result = scrape_links(url)
        await update.message.reply_text(result, parse_mode="HTML", disable_web_page_preview=True)
    else:
        await update.message.reply_text("Please send a valid URL.")

# Add handlers
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("help", start))
application.add_handler(CommandHandler("scrape", handle_message))
application.add_handler(CommandHandler("link", handle_message))
application.add_handler(CommandHandler("links", handle_message))
application.add_handler(CommandHandler("dl", handle_message))
application.add_handler(CommandHandler("download", handle_message))

from telegram.ext import MessageHandler, filters
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# Flask route for webhook
@app.route(f"/{BOT_TOKEN}", methods=["POST"])
async def webhook():
    if request.method == "POST":
        await application.update_queue.put(Update.de_json(request.get_json(force=True), application.bot))
        return "ok"

# Set webhook on startup
@app.before_first_request
def set_webhook():
    from telegram import Bot
    bot = Bot(BOT_TOKEN)
    bot.delete_webhook()
    bot.set_webhook(f"{WEBHOOK_URL}/{BOT_TOKEN}")

# Run Flask app
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
