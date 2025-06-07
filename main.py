import os
import requests
import re
import base64
from bs4 import BeautifulSoup
from telegram import Update, Bot
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, Filters, CallbackContext
import logging
from flask import Flask, request

# Configuration
TOKEN = "7861502352:AAFcS7xZk2NvN7eJ3jcPm_HyYh74my8vRyU"
PORT = int(os.getenv('PORT', 10000))

# Flask app
app = Flask(__name__)

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize bot and dispatcher
bot = Bot(token=TOKEN)
dispatcher = Dispatcher(bot=bot, update_queue=None, workers=4, use_context=True)

@app.route('/')
def home():
    return "🎬 Movie Download Link Bot is Running!", 200

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        update = Update.de_json(request.get_json(force=True), bot)
        dispatcher.process_update(update)
    except Exception as e:
        logger.error(f"Webhook error: {e}")
    return 'ok', 200

def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('🎬 Send me a movie page URL to extract download links.')

# Decode techyboy4u
def decode_techyboy4u(url):
    try:
        html = requests.get(url, timeout=10).text
        match = re.search(r'reurl\s*=\s*"([^"]+)"', html)
        if not match:
            return None
        encoded = match.group(1).split("?r=")[1]
        decoded = base64.b64decode(encoded).decode("utf-8")
        return decoded.split("link=")[1] if "link=" in decoded else decoded
    except:
        return None

# Decode hubcdn
def decode_hubcdn(url):
    try:
        html = requests.get(url, timeout=10).text
        match = re.search(r'reurl\s*=\s*"([^"]+)"', html)
        if not match:
            return None
        encoded = match.group(1).split("?r=")[1]
        decoded = base64.b64decode(encoded).decode("utf-8")
        return decoded.split("link=")[1] if "link=" in decoded else decoded
    except:
        return None

# Extract links from hdhub4u pages
def scrape_movie_links(movie_url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(movie_url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        
        links_info = []

        for tag in soup.find_all(['h3', 'h4']):
            a = tag.find('a')
            if a and a.get("href") and a.get_text(strip=True):
                label = a.get_text(strip=True)
                link = a['href']
                
                # Decode if needed
                if "techyboy4u.com" in link:
                    final_link = decode_techyboy4u(link)
                elif "hubcdn.fans" in link:
                    final_link = decode_hubcdn(link)
                else:
                    final_link = link
                
                if final_link:
                    links_info.append(f"{label}: {final_link}")
        
        return links_info
    except Exception as e:
        return [f"❌ Error: {str(e)}"]

def handle_message(update: Update, context: CallbackContext) -> None:
    url = update.message.text.strip()
    if not url.startswith(('http://', 'https://')):
        update.message.reply_text("⚠️ Please send a valid URL.")
        return

    links = scrape_movie_links(url)
    if not links:
        update.message.reply_text("❌ No links found.")
        return

    for line in links[:10]:  # Limit to 10 messages
        update.message.reply_text(f"📥 {line}")

def error_handler(update: object, context: CallbackContext) -> None:
    logger.error(f"Update {update} caused error {context.error}")

# Register handlers
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
dispatcher.add_error_handler(error_handler)

@app.route('/')
def home():
    # Set webhook here instead
    try:
        webhook_url = "https://hdsp.onrender.com/webhook"
        bot.set_webhook(url=webhook_url)
        logger.info(f"✅ Webhook set to {webhook_url}")
    except Exception as e:
        logger.error(f"❌ Failed to set webhook: {e}")
    return "🎬 Movie Download Link Bot is Running!", 200

