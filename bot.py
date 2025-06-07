import os
import requests
from bs4 import BeautifulSoup
from telegram import Update, ParseMode
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import logging
from urllib.parse import unquote

# Configuration
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '7861502352:AAFcS7xZk2NvN7eJ3jcPm_HyYh74my8vRyU')
PORT = int(os.getenv('PORT', 8443))  # Default port 8443 for webhooks
WEBHOOK_URL = os.getenv('WEBHOOK_URL', 'https://yourdomain.com')  # Your webhook URL

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def start(update: Update, context: CallbackContext) -> None:
    """Send welcome message"""
    update.message.reply_text(
        "🎬 *Movie Download Link Extractor Bot*\n\n"
        "Send me a movie page URL to extract download links.",
        parse_mode=ParseMode.MARKDOWN
    )

def extract_links(url: str) -> list:
    """Extract download links from movie page"""
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        download_links = []

        # Extract movie title
        movie_title = "Unknown Movie"
        h2_tag = soup.find('h2', class_='kno-ecr-pt')
        if h2_tag:
            movie_title = h2_tag.get_text(strip=True)
            movie_title = movie_title.replace("Download", "").replace("Full Movie", "").strip(" :-")

        # Extract download links
        for heading in soup.find_all(['h3', 'h4']):
            link = heading.find('a')
            if link and link.has_attr('href'):
                text = link.get_text(strip=True)
                
                if '[' in text and ']' in text:
                    quality = text.split('[')[0].strip()
                    size = text.split('[')[1].split(']')[0].strip()
                elif '⚡' in text:
                    parts = text.split('⚡')
                    quality = parts[0].strip()
                    size = parts[1].strip('[]').strip()
                else:
                    quality = text
                    size = "Unknown"
                
                download_links.append({
                    'movie_title': movie_title,
                    'quality': quality,
                    'size': size,
                    'url': link['href']
                })

        return download_links

    except Exception as e:
        logger.error(f"Error extracting links: {str(e)}")
        return None

def handle_message(update: Update, context: CallbackContext) -> None:
    """Handle incoming messages"""
    url = update.message.text.strip()
    
    if not url.startswith(('http://', 'https://')):
        update.message.reply_text("⚠️ Please send a valid URL")
        return
    
    context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    links = extract_links(url)
    if not links:
        update.message.reply_text("❌ No download links found")
        return
    
    update.message.reply_text(f"🎬 *{links[0]['movie_title']}*", parse_mode=ParseMode.MARKDOWN)
    
    for item in links[:6]:  # Limit to 6 links
        update.message.reply_text(
            f"📺 *{item['quality']}*\n💾 Size: `{item['size']}`\n🔗 [Download]({item['url']})",
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True
        )

def error_handler(update: Update, context: CallbackContext) -> None:
    """Log errors"""
    logger.error(msg="Exception while handling update:", exc_info=context.error)

def main() -> None:
    """Start the bot with port configuration"""
    updater = Updater(TOKEN)
    dispatcher = updater.dispatcher

    # Register handlers
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    dispatcher.add_error_handler(error_handler)

    # Choose deployment method based on environment
    if os.getenv('DEPLOY_METHOD') == 'webhook':
        # Production with webhook
        updater.start_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path=TOKEN,
            webhook_url=f"{WEBHOOK_URL}/{TOKEN}",
            cert='cert.pem' if os.path.exists('cert.pem') else None
        )
        logger.info(f"Bot running in webhook mode on port {PORT}")
    else:
        # Local development with polling
        updater.start_polling()
        logger.info("Bot running in polling mode")

    updater.idle()

if __name__ == '__main__':
    main()
