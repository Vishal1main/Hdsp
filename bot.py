import os
import requests
import re
import base64
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import logging

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration
TOKEN = os.getenv('TELEGRAM_TOKEN')  # Set in environment variables
PORT = int(os.getenv('PORT', 8443))

def extract_final_link(url):
    """Extract final download link from HubCDN URLs"""
    try:
        response = requests.get(url)
        html = response.text
        match = re.search(r'reurl\s*=\s*"([^"]+)"', html)
        if not match:
            return None
            
        encoded_url = match.group(1)
        base64_part = encoded_url.split("?r=")[1] if "?r=" in encoded_url else encoded_url
        decoded_url = base64.b64decode(base64_part).decode("utf-8")
        return decoded_url.split("link=")[1] if "link=" in decoded_url else decoded_url

    except Exception as e:
        logger.error(f"HubCDN extraction error: {e}")
        return None

def extract_movie_links(url):
    """Main function to extract all download links"""
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        results = []

        for h6 in soup.find_all('h6'):
            title = h6.get_text(strip=True)
            button = h6.find_next_sibling('a', class_='maxbutton-oxxfile')
            
            if button and 'href' in button.attrs:
                url = button['href']
                if 'hubcdn.fans' in url:
                    final_url = extract_final_link(url)
                    if final_url:
                        results.append({'title': title, 'url': final_url})
                else:
                    results.append({'title': title, 'url': url})

        return results if results else None

    except Exception as e:
        logger.error(f"Error extracting links: {e}")
        return None

def start(update: Update, context: CallbackContext):
    update.message.reply_text(
        '🎬 Movie Link Extractor Bot\n\n'
        'Send me any movie page URL to extract download links'
    )

def handle_message(update: Update, context: CallbackContext):
    url = update.message.text.strip()
    if not url.startswith(('http://', 'https://')):
        update.message.reply_text("⚠️ Please send a valid URL")
        return

    update.message.reply_text("⏳ Processing your link...")
    links = extract_movie_links(url)
    
    if not links:
        update.message.reply_text("❌ No download links found")
        return
    
    for idx, item in enumerate(links[:5], 1):  # Limit to 5 links
        update.message.reply_text(f"{idx}. {item['title']}\n🔗 {item['url']}")

def main():
    if not TOKEN:
        logger.error("❌ Telegram token missing! Set TELEGRAM_TOKEN environment variable.")
        return

    updater = Updater(TOKEN)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    # Use this for production with webhook
    # updater.start_webhook(listen="0.0.0.0", port=PORT, url_path=TOKEN)
    # updater.bot.set_webhook(f"https://yourdomain.com/{TOKEN}")

    # Use this for local testing
    updater.start_polling()
    logger.info("🤖 Bot is now running...")
    updater.idle()

if __name__ == '__main__':
    main()
