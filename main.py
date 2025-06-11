import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
import requests
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Webhook Configuration
TOKEN = os.environ['TELEGRAM_BOT_TOKEN']
PORT = int(os.environ.get('PORT', 8443))
WEBHOOK_URL = os.environ['WEBHOOK_URL']

def scrape_download_links(html_content):
    """Extract download links from HTML"""
    soup = BeautifulSoup(html_content, 'html.parser')
    download_links = {}
    
    for heading in soup.find_all(['h3', 'h4']):
        if link := heading.find('a'):
            if url := link.get('href'):
                quality = heading.get_text(strip=True).replace('⚡', '').strip()
                if not ('WATCH' in quality or 'PLAYER' in quality):
                    download_links[quality] = url
    return download_links

async def start(update: Update, context: CallbackContext) -> None:
    """Start command handler"""
    await update.message.reply_text('Send me an HDHub4U post link to extract download links')

async def handle_hdhub4u_link(update: Update, context: CallbackContext) -> None:
    """Process HDHub4U links"""
    try:
        msg = await update.message.reply_text("⏳ Processing your link...")
        
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(update.message.text, headers=headers)
        response.raise_for_status()
        download_links = scrape_download_links(response.text)

        if not download_links:
            await msg.edit_text("❌ No download links found")
            return

        response_text = "🔗 Download Links:\n\n" + \
                       "\n".join(f"🏷 {q}\n🔗 {l}" for q,l in download_links.items()) + \
                       "\n\n⚠️ Use at your own risk"

        await msg.edit_text(response_text, disable_web_page_preview=True)

    except Exception as e:
        logger.error(f"Error: {e}")
        await update.message.reply_text("❌ Failed to process link")

def main() -> None:
    """Start the bot in webhook mode"""
    application = Application.builder().token(TOKEN).build()
    
    # Register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_hdhub4u_link))

    # Webhook configuration
    application.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        webhook_url=f"{WEBHOOK_URL}/{TOKEN}",
        secret_token=os.environ.get('WEBHOOK_SECRET', '')
    )

if __name__ == '__main__':
    main()
