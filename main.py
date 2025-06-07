import os
import requests
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, CommandHandler, filters

BOT_TOKEN = os.getenv("BOT_TOKEN")

# 🔍 Scrape download links from provided page
def scrape_download_links(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        links = []
        for tag in soup.find_all(['h3', 'h4']):
            a_tag = tag.find('a', href=True)
            if a_tag:
                link = a_tag['href']
                text = a_tag.get_text(strip=True)
                links.append((text, link))

        return links
    except Exception as e:
        return f"Error: {e}"

# 📥 Handle any message as a possible URL
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    if not text.startswith("http"):
        await update.message.reply_text("❌ Send a valid URL to scrape download links.")
        return

    await update.message.reply_text("🔍 Scraping links... please wait...")

    links = scrape_download_links(text)

    if isinstance(links, str):  # Error occurred
        await update.message.reply_text(links)
        return

    if not links:
        await update.message.reply_text("❌ No download links found.")
        return

    reply = "🎬 <b>Download Links Found:</b>\n\n"
    for name, link in links:
        reply += f"<b>{name}</b>\n<code>{link}</code>\n\n"

    await update.message.reply_text(reply, parse_mode="HTML", disable_web_page_preview=True)

# 🚀 Start the bot
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Send me a movie page URL to scrape download links.")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_webhook(
        listen="0.0.0.0",
        port=int(os.getenv("PORT", 8080)),
        webhook_url=os.getenv("RENDER_EXTERNAL_URL") + "/webhook"
    )

if __name__ == "__main__":
    main()
