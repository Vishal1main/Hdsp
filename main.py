import os
import requests
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import logging
from flask import Flask, request

# Configuration
TOKEN = os.getenv('TOKEN', '7454733028:AAEEGmZe1-wd2Y8DfriKwMe7px9mSP3vS_I')
PORT = int(os.getenv('PORT', 10000))
WEBHOOK_URL = f"https://hdsp.onrender.com/{TOKEN}"

# Flask app
app = Flask(__name__)

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

@app.route('/')
def home():
    return "🎬 Movie Download Link Bot is running!", 200

@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    update = Update.de_json(request.get_json(force=True), updater.bot)
    dispatcher.process_update(update)
    return 'ok', 200

# Command: /start
def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('🎬 Send me a movie page URL to extract download links')

# Extract download links from HTML
def extract_all_download_links(html):
    soup = BeautifulSoup(html, 'html.parser')
    links = []

    for a in soup.find_all('a', href=True):
        title = a.get_text(strip=True)
        url = a['href'].strip()
        if url and title and url not in ['#', 'javascript:void(0)', '']:
            links.append({'title': title, 'url': url})

    return links

# Extract from URL
def extract_links_from_url(url: str):
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            return extract_all_download_links(response.text)
    except Exception as e:
        logger.error(f"Scraping Error: {e}")
    return None

# Handle incoming message
def handle_message(update: Update, context: CallbackContext) -> None:
    url = update.message.text.strip()
    if not url.startswith(('http://', 'https://')):
        update.message.reply_text("⚠️ Please send a valid URL")
        return

    links = extract_links_from_url(url)
    if not links:
        update.message.reply_text("❌ No download links found")
        return

    for item in links[:10]:  # Limit to 10 links to avoid spam
        update.message.reply_text(f"🎬 <b>{item['title']}</b>\n🔗 {item['url']}", parse_mode="HTML")

# Error handler
def error_handler(update: object, context: CallbackContext) -> None:
    logger.error(f"Update {update} caused error {context.error}")

# Initialize bot
updater = Updater(TOKEN, use_context=True)
dispatcher = updater.dispatcher

# Register handlers
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
dispatcher.add_error_handler(error_handler)

if __name__ == '__main__':
    updater.start_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=TOKEN,
        webhook_url=WEBHOOK_URL
    )
    updater.idle()
