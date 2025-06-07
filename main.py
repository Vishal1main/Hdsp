import os
import re
import base64
import requests
from bs4 import BeautifulSoup
from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, Filters, CallbackContext
import logging
from urllib.parse import urlparse, parse_qs, unquote

TOKEN = "7861502352:AAFcS7xZk2NvN7eJ3jcPm_HyYh74my8vRyU"
PORT = int(os.environ.get("PORT", 10000))

app = Flask(__name__)

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

# Base64 decode helper with padding fix
def b64decode_fix(data: str) -> str:
    data += '=' * ((4 - len(data) % 4) % 4)
    return base64.urlsafe_b64decode(data).decode('utf-8')

# Decode inventoryidea.com/?r= link to get final URL
def decode_inventoryidea_link(url: str) -> str:
    try:
        parsed = urlparse(url)
        qs = parse_qs(parsed.query)
        if 'r' not in qs:
            return url
        encoded = qs['r'][0]
        decoded = b64decode_fix(encoded)
        # decoded might contain another encoded URL after "link="
        # example: ...?link=some_encoded_url
        # so parse again:
        if 'link=' in decoded:
            after_link = decoded.split('link=')[1]
            # If after_link is also base64 encoded url, decode it:
            try:
                after_link_decoded = b64decode_fix(after_link)
                return after_link_decoded
            except:
                return after_link
        return decoded
    except Exception as e:
        logger.error(f"Error decoding inventoryidea link: {e}")
        return url

# Decode techyboy4u.com/?id= link to get final download URL
def decode_techyboy_link(url: str) -> str:
    try:
        parsed = urlparse(url)
        qs = parse_qs(parsed.query)
        if 'id' not in qs:
            return url
        encoded = qs['id'][0]
        decoded = b64decode_fix(encoded)
        # decoded might also contain base64 again or direct link
        if 'link=' in decoded:
            after_link = decoded.split('link=')[1]
            try:
                after_link_decoded = b64decode_fix(after_link)
                return after_link_decoded
            except:
                return after_link
        return decoded
    except Exception as e:
        logger.error(f"Error decoding techyboy link: {e}")
        return url

# Given hubcdn.fans/file/... link, get the intermediate link (inventoryidea link)
def extract_from_hubcdn(url: str) -> str:
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(url, headers=headers)
        html = res.text
        # hubcdn pages contain somewhere: reurl = "base64string"
        m = re.search(r'reurl\s*=\s*"([^"]+)"', html)
        if not m:
            return None
        encoded_part = m.group(1)
        # The encoded_part itself is a url with ?r=base64encoded
        # So decode it fully
        intermediate_link = decode_inventoryidea_link(encoded_part)
        return intermediate_link
    except Exception as e:
        logger.error(f"Error extracting from hubcdn: {e}")
        return None

# Main function to extract all final download links from movie post url
def extract_links(url: str):
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        res = requests.get(url, headers=headers)
        soup = BeautifulSoup(res.text, 'html.parser')
        links = []
        for a in soup.find_all('a', href=True):
            href = a['href']
            text = a.get_text(strip=True) or "Download"
            if not href.startswith("http"):
                continue

            final_url = None

            # Case 1: If link is hubcdn.fans/file/...
            if 'hubcdn.fans/file/' in href:
                # extract intermediate link from hubcdn page
                intermediate = extract_from_hubcdn(href)
                if intermediate:
                    # intermediate is inventoryidea link, decode to final
                    final_url = decode_inventoryidea_link(intermediate)
                    # Now check if final_url is techyboy4u link? If yes decode further
                    if final_url and "techyboy4u.com" in final_url:
                        final_url = decode_techyboy_link(final_url)
            # Case 2: direct inventoryidea.com/?r=... link on post
            elif "inventoryidea.com" in href:
                final_url = decode_inventoryidea_link(href)
                # Also decode if it's techyboy4u link inside
                if final_url and "techyboy4u.com" in final_url:
                    final_url = decode_techyboy_link(final_url)
            # Case 3: direct techyboy4u.com/?id=... link on post
            elif "techyboy4u.com" in href:
                final_url = decode_techyboy_link(href)
            else:
                # If normal direct link, keep as is
                final_url = href

            if final_url:
                links.append({'title': text, 'url': final_url})

        return links

    except Exception as e:
        logger.error(f"Error extracting links: {e}")
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

dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
dispatcher.add_error_handler(error_handler)

if __name__ == "__main__":
    try:
        bot.set_webhook("https://hdsp.onrender.com/webhook")
        logger.info("Webhook set successfully.")
    except Exception as e:
        logger.error(f"Webhook error: {e}")

    app.run(host="0.0.0.0", port=PORT)
