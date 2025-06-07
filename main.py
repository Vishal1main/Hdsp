import requests
from bs4 import BeautifulSoup
import re
import base64
from urllib.parse import unquote, urlparse, parse_qs
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import telegram
import logging
from functools import partial

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
TOKEN = '7861502352:AAFcS7xZk2NvN7eJ3jcPm_HyYh74my8vRyU'
PORT = 8443  # Change this to your desired port
WEBHOOK_URL = 'https://hdsp.onrender.com'  # Change to your domain

# Initialize bot
bot = telegram.Bot(token=TOKEN)

# Session with custom timeout and retries
session = requests.Session()
session.mount('http://', requests.adapters.HTTPAdapter(
    max_retries=3,
    pool_connections=10,
    pool_maxsize=10
))
session.mount('https://', requests.adapters.HTTPAdapter(
    max_retries=3,
    pool_connections=10,
    pool_maxsize=10
))

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

PROXY = {
    'http': 'http://localhost:8080',  # Change if you need proxy
    'https': 'http://localhost:8080'
}

def make_request(url, use_proxy=False):
    try:
        kwargs = {
            'headers': HEADERS,
            'timeout': 30,
            'allow_redirects': False
        }
        if use_proxy:
            kwargs['proxies'] = PROXY
        return session.get(url, **kwargs)
    except Exception as e:
        logger.error(f"Request failed: {e}")
        raise

# [Keep all the extractor functions from previous code...]
# extract_hubcdn_final_url, extract_hubcloud_final_urls, etc.

def start(update, context):
    """Send a message when the command /start is issued."""
    update.message.reply_text(
        'Hi! Send me a movie post URL and I will extract all download links for you.\n'
        'Supported sites: hubcdn.fans, hubdrive.space, hubcloud.one, techyboy4u.com'
    )

def extract_links(update, context):
    """Handle incoming messages with URLs"""
    url = update.message.text.strip()
    
    try:
        if not url.startswith(('http://', 'https://')):
            update.message.reply_text("Please provide a valid URL starting with http:// or https://")
            return
            
        processing_msg = update.message.reply_text("🔍 Processing your request...")
        
        download_links = []
        
        # [Keep the existing extraction logic...]
        
        # Format the response
        if download_links:
            response_text = "🔗 Download Links Found:\n\n"
            for link in download_links:
                response_text += f"➡️ {link}\n\n"
            
            context.bot.edit_message_text(
                chat_id=update.message.chat_id,
                message_id=processing_msg.message_id,
                text=response_text
            )
        else:
            context.bot.edit_message_text(
                chat_id=update.message.chat_id,
                message_id=processing_msg.message_id,
                text="❌ No download links found on this page."
            )
            
    except Exception as e:
        logger.error(f"Error processing URL: {e}")
        update.message.reply_text(f"❌ An error occurred: {str(e)}")

def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)

def main():
    """Start the bot."""
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    # Command handlers
    dp.add_handler(CommandHandler("start", start))

    # Message handler
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, extract_links))

    # Error handler
    dp.add_error_handler(error)

    # Start the Bot with webhook
    updater.start_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=TOKEN,
        webhook_url=f"{WEBHOOK_URL}/{TOKEN}"
    )
    updater.bot.set_webhook(f"{WEBHOOK_URL}/{TOKEN}")
    
    logger.info(f"Bot started on port {PORT} with webhook URL {WEBHOOK_URL}")
    updater.idle()

if __name__ == '__main__':
    main()
