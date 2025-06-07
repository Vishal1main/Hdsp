import os
import re
import base64
import requests
from bs4 import BeautifulSoup
from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, Filters, CallbackContext
import logging

# Configuration
TOKEN = "7454733028:AAEEGmZe1-wd2Y8DfriKwMe7px9mSP3vS_I"
PORT = int(os.getenv("PORT", 10000))

# Flask app
app = Flask(__name__)

# Logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Bot and Dispatcher
bot = Bot(token=TOKEN)
dispatcher = Dispatcher(bot=bot, update_queue=None, workers=4, use_context=True)

@app.route("/")
def home():
    return "🎬 Movie Download Link Bot is Running!", 200

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        update = Update.de_json(request.get_json(force=True), bot)
        dispatcher.process_update(update)
    except Exception as e:
        logger.error(f"Webhook error: {e}")
    return "ok", 200

@app.before_first_request
def set_webhook():
    webhook_url = "https://spbot-idtu.onrender.com/webhook"
    if bot.set_webhook(url=webhook_url):
        logger.info(f"✅ Webhook set to {webhook_url}")
    else:
        logger.error("❌ Failed to set webhook")

# /start command
def start(update: Update, context: CallbackContext):
    update.message.reply_text("🎬 Send me a movie page URL to extract download links.")

# HubCDN extractor
def extract_hubcdn_link(url: str) -> str:
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
    except Exception as e:
        logger.error(f"HubCDN decode error: {e}")
        return None

# Movie page link scraper
def extract_links(url: str) -> list:
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        return [
            {
                'title': h6.get_text(strip=True),
                'url': h6.find_next_sibling('a', class_='maxbutton-oxxfile')['href']
            }
            for h6 in soup.find_all('h6')
            if h6.find_next_sibling('a', class_='maxbutton-oxxfile')
        ]
    except Exception as e:
        logger.error(f"Error scraping links: {e}")
        return None

# Message handler
def handle_message(update: Update, context: CallbackContext):
    url = update.message.text.strip()
    if not url.startswith(("http://", "https://")):
        update.message.reply_text("⚠️ Please send a valid URL.")
        return

    if "hubcdn.fans" in url:
        final = extract_hubcdn_link(url)
        if final:
            update.message.reply_text(f"✅ Final Download Link:\n{final}")
        else:
            update.message.reply_text("❌ Couldn't extract final link from HubCDN.")
        return

    if "techyboy4u.com" in url:
        try:
            resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
            soup = BeautifulSoup(resp.text, "html.parser")

            # Find iframe or script with hubcdn
            hubcdn_link = None
            iframe = soup.find("iframe")
            if iframe and "hubcdn.fans" in iframe.get("src", ""):
                hubcdn_link = iframe["src"]

            if not hubcdn_link:
                all_links = soup.find_all(["a", "script", "iframe"])
                for tag in all_links:
                    src = tag.get("src") or tag.get("href") or ""
                    if "hubcdn.fans" in src:
                        hubcdn_link = src
                        break

            if not hubcdn_link:
                update.message.reply_text("❌ Couldn't find any hubcdn link in the page.")
                return

            final = extract_hubcdn_link(hubcdn_link)
            if final:
                update.message.reply_text(f"✅ Final Download Link:\n{final}")
            else:
                update.message.reply_text("❌ Couldn't decode the final link from hubcdn.")
        except Exception as e:
            logger.error(f"TechyBoy4u scrape error: {e}")
            update.message.reply_text("❌ Error while processing TechyBoy4u page.")
        return

    links = extract_links(url)
    if not links:
        update.message.reply_text("❌ No links found.")
        return

    for item in links[:5]:
        update.message.reply_text(f"📥 <b>{item['title']}</b>\n🔗 {item['url']}", parse_mode="HTML")

# Register handlers
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
