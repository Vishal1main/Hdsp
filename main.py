import os import requests from bs4 import BeautifulSoup from telegram import Update from telegram.ext import ( Updater, CommandHandler, MessageHandler, Filters, CallbackContext ) from flask import Flask, request, Response

BOT_TOKEN = os.environ.get("BOT_TOKEN") or "7861502352:AAFcS7xZk2NvN7eJ3jcPm_HyYh74my8vRyU" WEBHOOK_URL = f"https://hdsp.onrender.com/{BOT_TOKEN}" PORT = int(os.environ.get("PORT", 8443))

HDHUB4U_URL = "https://hdhub4u.gratis/"

app = Flask(name)

@app.route(f"/{BOT_TOKEN}", methods=["POST"]) def webhook(): from telegram.ext import Dispatcher import telegram bot = telegram.Bot(token=BOT_TOKEN) dp = Dispatcher(bot, None, workers=0, use_context=True) update = Update.de_json(request.get_json(force=True), bot) dp.add_handler(CommandHandler("start", start)) dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_link)) dp.process_update(update) return "OK", 200

@app.route("/rss.xml") def rss_feed(): try: response = requests.get(HDHUB4U_URL, timeout=10) soup = BeautifulSoup(response.text, 'html.parser') posts = soup.select(".post-title a")

items = ""
    for post in posts[:10]:
        title = post.get_text(strip=True)
        link = post['href']
        items += f"""
        <item>
            <title>{title}</title>
            <link>{link}</link>
        </item>
        """

    rss = f"""
    <rss version="2.0">
        <channel>
            <title>HDHub4u RSS Feed</title>
            <link>{HDHUB4U_URL}</link>
            <description>Latest HDHub4u Posts</description>
            {items}
        </channel>
    </rss>
    """
    return Response(rss, mimetype='application/rss+xml')
except Exception as e:
    return f"Error generating RSS: {e}", 500

def start(update: Update, context: CallbackContext): update.message.reply_text("✅ Send me an HDHub4u post URL and I'll fetch download links.")

def handle_link(update: Update, context: CallbackContext): url = update.message.text.strip() if not url.startswith("http"): update.message.reply_text("⚠️ Please send a valid URL.") return

try:
    res = requests.get(url, timeout=10)
    soup = BeautifulSoup(res.text, 'html.parser')
    links = soup.find_all("a", href=True)

    result = []
    for a in links:
        text = a.get_text(strip=True)
        href = a['href']
        if href.startswith("http") and any(kw in text.lower() for kw in ["480", "720", "1080", "4k"]):
            result.append(f"🔗 <b>{text}</b>\n{href}")

    if result:
        update.message.reply_text("\n\n".join(result), parse_mode='HTML')
    else:
        update.message.reply_text("❌ No download links found.")

except Exception as e:
    update.message.reply_text(f"🚫 Error: {str(e)}")

def main(): updater = Updater(token=BOT_TOKEN, use_context=True) dp = updater.dispatcher dp.add_handler(CommandHandler("start", start)) dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_link))

updater.start_webhook(
    listen="0.0.0.0",
    port=PORT,
    url_path=BOT_TOKEN,
    webhook_url=WEBHOOK_URL
)
updater.idle()

if name == "main": main()

