import os
import requests
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import logging
from flask import Flask, request

# Configuration
TOKEN = os.getenv('TOKEN', '7861502352:AAFcS7xZk2NvN7eJ3jcPm_HyYh74my8vRyU')
PORT = int(os.getenv('PORT', 10000))

# Flask app
app = Flask(__name__)

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

@app.route('/')
def home():
    return "Movie Download Link Bot is running!", 200

# Main webhook route (must match token!)
@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    update = Update.de_json(request.get_json(force=True), updater.bot)
    dispatcher.process_update(update)
    return 'ok', 200

def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('🎬 Send me a movie page URL to extract download links')

def extract_links(url: str) -> list:
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')

        results = []

        for a_tag in soup.find_all('a', href=True):
            parent = a_tag.find_parent(['h3', 'h4'])
            if parent:
                title = parent.get_text(strip=True)
                link = a_tag['href']
                if link.startswith("http"):
                    results.append({
                        'title': title,
                        'url': link
                    })

        return results if results else None
    except Exception as e:
        logger.error(f"Error extracting links: {str(e)}")
        return None

def handle_message(update: Update, context: CallbackContext) -> None:
    url = update.message.text.strip()
    if not url.startswith(('http://', 'https://')):
        update.message.reply_text("⚠️ Please send a valid URL")
        return
    
    links = extract_links(url)
    if not links:
        update.message.reply_text("❌ No links found")
        return
    
    for item in links[:10]:  # limit to 10
        update.message.reply_text(f"<b>{item['title']}</b>\n🔗 {item['url']}", parse_mode="HTML")

def error_handler(update: object, context: CallbackContext) -> None:
    logger.error(f"Update {update} caused error {context.error}")

# Initialize bot
updater = Updater(TOKEN)
dispatcher = updater.dispatcher

# Register handlers
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
dispatcher.add_error_handler(error_handler)

if __name__ == '__main__':
    # Start webhook
    updater.start_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=TOKEN,
        webhook_url=f"https://hdsp.onrender.com/{TOKEN}"
    )
    updater.idle()
