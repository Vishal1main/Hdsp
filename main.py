import os
import re
import base64
import requests
from bs4 import BeautifulSoup
from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, Filters, CallbackContext
import logging

TOKEN = "7861502352:AAFcS7xZk2NvN7eJ3jcPm_HyYh74my8vRyU"
PORT = int(os.environ.get("PORT", 10000))

app = Flask(__name__)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=TOKEN)
dispatcher = Dispatcher(bot=bot, update_queue=None, workers=4, use_context=True)

@app.route('/')
def home():
    return "🎬 Movie Bot is Live", 200

@app.route('/webhook', methods=['POST'])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return "ok", 200

def start(update: Update, context: CallbackContext):
    update.message.reply_text("🎬 Send a movie page URL to extract download links.")

def extract_final_link_from_hubcdn(url):
    try:
        response = requests.get(url)
        html = response.text
        match = re.search(r'reurl\s*=\s*"([^"]+)"', html)
        if not match:
            return None
        base64_part = match.group(1).split("?r=")[1]
        decoded_url = base64.b64decode(base64_part).decode("utf-8")
        return decoded_url.split("link=")[1] if "link=" in decoded_url else decoded_url
    except:
        return None

def extract_final_link_from_techyboy(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        for script in soup.find_all("script"):
            if script.string and 'atob' in script.string:
                encoded = re.search(r'atob\("([^"]+)"\)', script.string).group(1)
                decoded = base64.b64decode(encoded).decode("utf-8")
                return decoded.split("link=")[1] if "link=" in decoded else decoded
    except:
        return None

def extract_links(url):
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
            final = None
            if "hubcdn.fans" in href:
                final = extract_final_link_from_hubcdn(href)
            elif "techyboy4u.com" in href:
                final = extract_final_link_from_techyboy(href)
            if final:
                links.append({'title': text or "Download", 'url': final})
        return links
    except Exception as e:
        logger.error(f"Link extraction error: {e}")
        return []

def handle_message(update: Update, context: CallbackContext):
    url = update.message.text.strip()
    if not url.startswith(('http://', 'https://')):
        update.message.reply_text("❌ Invalid URL.")
        return

    update.message.reply_text("🔍 Scraping...")
    links = extract_links(url)
    if not links:
        update.message.reply_text("No links found.")
    else:
        for link in links[:5]:
            update.message.reply_text(f"🎬 {link['title']}\n🔗 {link['url']}")

def error_handler(update, context):
    logger.error(msg="Exception while handling an update:", exc_info=context.error)

# Handlers
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
dispatcher.add_error_handler(error_handler)

# Don't use webhook set inside route!
if __name__ == "__main__":
    # Set webhook manually when run locally or for logs
    try:
        bot.set_webhook("https://hdsp.onrender.com/webhook")
        logger.info("Webhook set successfully.")
    except Exception as e:
        logger.error(f"Webhook error: {e}")
    
    app.run(host="0.0.0.0", port=PORT)
