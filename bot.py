from telegram.ext import Updater, MessageHandler, Filters, CommandHandler
from bs4 import BeautifulSoup
import requests
import logging
import os

# Configuration
BOT_TOKEN = os.getenv('BOT_TOKEN', '7861502352:AAFcS7xZk2NvN7eJ3jcPm_HyYh74my8vRyU')  # Get from environment variable or replace
PORT = int(os.getenv('PORT', 8443))  # Default port 8443 for webhooks
WEBHOOK_URL = os.getenv('WEBHOOK_URL', 'https://hdsp.onrender.com')  # Your webhook URL if using webhooks
MODE = os.getenv('MODE', 'webhook')  # 'polling' or 'webhook'

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def scrape_hdhub4u_post(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()
        soup = BeautifulSoup(r.content, 'html.parser')

        title_tag = soup.find("h1") or soup.find("h2", class_="kno-ecr-pt")
        title = title_tag.text.strip() if title_tag else "🎬 Movie Details"

        links = []
        for a in soup.find_all("a", href=True):
            href = a['href'].strip()
            text = a.get_text(strip=True)
            
            if not href or not text or "watch" in text.lower() or "player" in text.lower():
                continue
                
            if href.startswith(("http://", "https://")):
                file_size = ""
                if any(p in text.lower() for p in ['480p', '720p', '1080p', '4k', '2160p']):
                    file_size = f" ({text.split('[')[-1].split(']')[0]})" if '[' in text and ']' in text else ""
                    quality = text.split()[0]
                else:
                    quality = "Download"
                
                links.append(f"🔗 <b>{quality}{file_size}</b>\n<a href='{href}'>{href}</a>")

        if not links:
            return "❌ No download links found."

        return f"<b>{title}</b>\n\n" + "\n\n".join(links)

    except Exception as e:
        logger.error(f"Scraping error: {e}")
        return f"⚠️ Error scraping the page: {str(e)}"

def start(update, context):
    welcome_msg = """
    🎥 <b>HDHub4u Scraper Bot</b> 🎥

    Send me any HDHub4u post URL and I'll extract all download links!

    Example:
    https://hdhub4u.xyz/movies/the-batman-2022/
    """
    update.message.reply_text(welcome_msg, parse_mode="HTML")

def handle_message(update, context):
    text = update.message.text.strip()
    if text.startswith(("http://", "https://")) and "hdhub" in text.lower():
        update.message.reply_text("🔍 Scraping all download links...", quote=True)
        reply = scrape_hdhub4u_post(text)
        update.message.reply_text(reply, parse_mode="HTML", disable_web_page_preview=True)
    else:
        update.message.reply_text("❗ Send a valid HDHub4U URL starting with http/https")

def error_handler(update, context):
    logger.error(f"Update {update} caused error {context.error}")

def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    dp.add_error_handler(error_handler)

    if MODE == 'webhook' and WEBHOOK_URL:
        updater.start_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path=BOT_TOKEN,
            webhook_url=f"{WEBHOOK_URL}/{BOT_TOKEN}"
        )
        logger.info(f"Bot running in webhook mode on port {PORT}")
    else:
        updater.start_polling()
        logger.info("Bot running in polling mode")

    updater.idle()

if __name__ == "__main__":
    main()
