import requests
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import logging
import re
import base64
import os

# Configuration
TOKEN = os.getenv('TOKEN', 'YOUR_TELEGRAM_BOT_TOKEN')
PORT = int(os.getenv('PORT', 10000))

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

def extract_final_link(url):
    """Extract final download link from HubCDN URLs"""
    try:
        response = requests.get(url)
        html = response.text

        # Extract base64 encoded URL
        match = re.search(r'reurl\s*=\s*"([^"]+)"', html)
        if not match:
            raise Exception("Base64 URL not found in HTML")
            
        encoded_url = match.group(1)
        if "?r=" not in encoded_url:
            raise Exception("No '?r=' parameter found")
            
        base64_part = encoded_url.split("?r=")[1]
        decoded_url = base64.b64decode(base64_part).decode("utf-8")

        # Extract final link
        if "link=" in decoded_url:
            return decoded_url.split("link=")[1]
        return decoded_url

    except Exception as e:
        logger.error(f"HubCDN extraction error: {str(e)}")
        return None

def extract_movie_links(url):
    """Extract download links from movie sites"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        download_links = []

        for h6 in soup.find_all('h6'):
            title = h6.get_text(strip=True)
            next_a = h6.find_next_sibling('a', class_='maxbutton-oxxfile')
            
            if next_a and 'href' in next_a.attrs:
                # Check if this is a HubCDN link
                if 'hubcdn.fans' in next_a['href']:
                    final_url = extract_final_link(next_a['href'])
                    if final_url:
                        download_links.append({
                            'title': title,
                            'url': final_url,
                            'source': 'HubCDN'
                        })
                else:
                    download_links.append({
                        'title': title,
                        'url': next_a['href'],
                        'source': 'Direct'
                    })

        return download_links

    except Exception as e:
        logger.error(f"Movie site extraction error: {str(e)}")
        return None

def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(
        '🎬 Movie Download Link Extractor Bot\n\n'
        'Send me a movie page URL to extract download links'
    )

def handle_message(update: Update, context: CallbackContext) -> None:
    url = update.message.text.strip()
    
    if not url.startswith(('http://', 'https://')):
        update.message.reply_text("⚠️ Please send a valid URL starting with http:// or https://")
        return
    
    update.message.reply_text("🔍 Processing your link...")
    
    links = extract_movie_links(url)
    
    if not links:
        update.message.reply_text("❌ No download links found or error occurred")
        return
    
    # Send results
    update.message.reply_text(f"✅ Found {len(links)} download links:")
    
    for idx, item in enumerate(links[:5], 1):  # Limit to 5 links
        message = (
            f"{idx}. {item['title']}\n"
            f"🔗 {item['url']}\n"
            f"Source: {item['source']}"
        )
        update.message.reply_text(message)

def error_handler(update: Update, context: CallbackContext) -> None:
    logger.error(f"Update {update} caused error {context.error}")

def main():
    updater = Updater(TOKEN)
    dispatcher = updater.dispatcher

    # Register handlers
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    dispatcher.add_error_handler(error_handler)

    # Start the bot
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
