import os
import re
import requests
from flask import Flask, request
from bs4 import BeautifulSoup
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

bot = Bot(token=BOT_TOKEN)
app = Flask(__name__)

# --- Scraper Function ---
def scrape_links_from_url(url):
    try:
        res = requests.get(url, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        links = soup.find_all("a", href=True)
        results = []

        for link in links:
            text = link.get_text(strip=True)
            href = link['href']
            if href.startswith("http") and "download" not in text.lower():
                results.append(f"{text}:\n{href}")

        return results if results else ["No valid download links found."]
    except Exception as e:
        return [f"Error scraping: {e}"]

# --- Telegram Handler ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send me a movie post link, and I'll fetch all download links.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    if not url.startswith("http"):
        await update.message.reply_text("Please send a valid movie post URL.")
        return

    await update.message.reply_text("🔍 Scraping links, please wait...")
    results = scrape_links_from_url(url)
    await update.message.reply_text("\n\n".join(results))

# --- Set up Webhook ---
def main():
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", start))
    application.add_handler(CommandHandler("scrape", handle_message))
    application.add_handler(CommandHandler("get", handle_message))
    application.add_handler(CommandHandler("go", handle_message))
    application.add_handler(CommandHandler("link", handle_message))
    application.add_handler(CommandHandler("url", handle_message))
    application.add_handler(CommandHandler("links", handle_message))
    application.add_handler(CommandHandler("post", handle_message))

    # message handler for any text
    application.add_handler(CommandHandler(None, handle_message))
    application.add_handler(CommandHandler("", handle_message))

    # Set webhook URL
    application.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 10000)),
        webhook_url=f"{WEBHOOK_URL}/webhook"
    )

@app.route("/webhook", methods=["POST"])
def webhook():
    if request.method == "POST":
        update = Update.de_json(request.get_json(force=True), bot)
        bot.initialize()
        bot._dispatcher.process_update(update)
        return "ok", 200

if __name__ == "__main__":
    main()
