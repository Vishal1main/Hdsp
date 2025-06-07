from flask import Flask, request, abort
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, Dispatcher

import logging
import os

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")  # Set your bot token as env variable
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # e.g. https://yourdomain.com/YOUR_BOT_TOKEN

app = Flask(__name__)

bot = Bot(token=BOT_TOKEN)
application = ApplicationBuilder().token(BOT_TOKEN).build()

# Handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Welcome! Send me any message.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    await update.message.reply_text(f"You said: {text}")

# Add handlers to dispatcher
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

# Flask route for webhook
@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    if request.method == "POST":
        update = Update.de_json(request.get_json(force=True), bot)
        application.process_update(update)
        return "OK"
    else:
        abort(403)

# Set webhook on startup
@app.before_first_request
def set_webhook():
    bot.delete_webhook()
    success = bot.set_webhook(WEBHOOK_URL)
    if success:
        logger.info(f"Webhook set to {WEBHOOK_URL}")
    else:
        logger.error("Failed to set webhook")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8443"))
    app.run(host="0.0.0.0", port=port)
