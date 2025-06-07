import os
import re
import base64
import requests
from bs4 import BeautifulSoup
from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, Filters, CallbackContext
import logging

# Configuration
TOKEN = "7861502352:AAFcS7xZk2NvN7eJ3jcPm_HyYh74my8vRyU"
PORT = int(os.getenv('PORT', 10000))

# Flask app
app = Flask(__name__)

# Logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Telegram bot and dispatcher
bot = Bot(token=TOKEN)
dispatcher = Dispatcher(bot=bot, update_queue=None, workers=4, use_context=True)

@app.route('/')
def home():
    try:
        webhook_url = "https://hdsp.onrender.com/webhook"
        bot.set_webhook(url=webhook_url)
        logger.info(f"✅ Webhook set to {webhook_url}")
    except Exception as e:
        logger.error(f"❌ Webhook error: {e}")
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
    update.message.reply_text("🎬 Send me a movie page URL to extract download links.")

# Final link extractors
def extract_final_link_from_hubcdn(url):
    try:
        response = requests.get(url)
        html = response.text
        match = re.search(r'reurl\s*=\s*"([^"]+)"', html)
        if not match:
            return None
        encoded_url = match.group(1)
        if "?r=" not in encoded_url:
            return None
        base64_part = encoded_url.split("?r=")[1]
        decoded_url = base64.b64decode(base64_part).decode("utf-8")
        return decoded_url.split("link=")[1] if "link=" in decoded_url else decoded_url
    except:
        return None

def extract_final_link_from_techyboy(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        scripts = soup.find_all('script')
        for script in scripts:
            if script.string and 'atob' in script.string:
                match = re.search(r'atob\("([^"]+)"\)', script.string)
                if match:
                    encoded = match.group(1)
                    decoded = base64.b64decode(encoded).decode('utf-8')
                    return decoded.split("link=")[1] if "link=" in decoded else decoded
    except:
        return None

# Main link scraper
def extract_links(url: str) -> list:
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        links = []

        for a in soup.find_all('a', href=True):
            href = a['href']
            text = a.get_text(strip=True)
            if not href.startswith("http"):
                continue

            final_url = None
            if "hubcdn.fans" in href:
                final_url = extract_final_link_from_hubcdn(href)
            elif "techyboy4u.com" in href:
                final_url = extract_final_link_from_techyboy(href)

            if final_url:
                links.append({'title': text or "Download", 'url': final_url})

        return links
    except Exception as e:
        logger.error(f"Scrape error: {e}")
        return None

def handle_message(update: Update, context: CallbackContext) -> None:
    url = update.message.text.strip()
    if not url.startswith(('http://', 'https://')):
        update.message.reply_text("⚠️ Please send a valid URL.")
        return

    update.message.reply_text("🔍 Extracting download links...")
    links = extract_links(url)
    if not links:
        update.message.reply_text("❌ No final links found.")
        return

    for item in links[:5]:  # Show only top 5 links
        update.message.reply_text(f"🎬 {item['title']}\n🔗 {item['url']}")

def error_handler(update: object, context: CallbackContext) -> None:
    logger.error(f"Update {update} caused error {context.error}")

# Register handlers
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
dispatcher.add_error_handler(error_handler)
