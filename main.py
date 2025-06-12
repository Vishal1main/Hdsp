import os
import time
import asyncio
from datetime import datetime
from flask import Flask, request
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pymongo import MongoClient
from config import API_ID, API_HASH, BOT_TOKEN, CHANNEL_ID, MONGO_URI, WEBHOOK_URL

# Pyrogram app
app = Client("premium-bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# MongoDB
mongo = MongoClient(MONGO_URI)
db = mongo["premium_bot"]
users_col = db["users"]

# Flask server for webhook
web_app = Flask(__name__)
ADMIN_ID = 6987799874  # replace with your Telegram ID

# Register webhook with Telegram
@app.on_message(filters.command("start") & filters.private)
async def start_command(_, msg):
    await msg.reply("🤖 Webhook bot is live!")

# Premium command
@app.on_message(filters.command("addpremium") & filters.user(ADMIN_ID))
async def add_premium(_, msg: Message):
    parts = msg.text.split()
    if len(parts) != 3:
        return await msg.reply("❌ Usage: /addpremium @username|user_id days")

    user_input = parts[1]
    days = int(parts[2])

    try:
        user = await app.get_users(user_input)
    except Exception as e:
        return await msg.reply(f"User not found:\n{e}")

    try:
        invite = await app.create_chat_invite_link(
            chat_id=CHANNEL_ID,
            member_limit=1,
            expire_date=int(time.time()) + (days * 86400)
        )
    except Exception as e:
        return await msg.reply(f"Failed to create link:\n{e}")

    users_col.update_one(
        {"user_id": user.id},
        {"$set": {
            "user_id": user.id,
            "expires_at": time.time() + (days * 86400)
        }},
        upsert=True
    )

    await msg.reply(
        f"✅ Added {user.first_name} for {days} days\n"
        f"🔗 Invite: {invite.invite_link}",
        parse_mode="html"
    )

# Flask route to receive Telegram webhook updates
@web_app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    update = request.get_json()
    if update:
        asyncio.run(app.dispatch(update))
    return "OK", 200

# Background job: remove expired users
async def remove_expired_users():
    while True:
        now = time.time()
        expired_users = users_col.find({"expires_at": {"$lte": now}})
        for u in expired_users:
            try:
                await app.ban_chat_member(CHANNEL_ID, u["user_id"])
                await app.unban_chat_member(CHANNEL_ID, u["user_id"])
                users_col.delete_one({"user_id": u["user_id"]})
                print(f"Removed expired user: {u['user_id']}")
            except Exception as e:
                print(f"Failed to remove {u['user_id']}: {e}")
        await asyncio.sleep(3600)

# Start Flask + Bot
if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(app.start())
    loop.run_until_complete(app.set_webhook(WEBHOOK_URL + f"/{BOT_TOKEN}"))
    print("🚀 Webhook set. Flask app running.")
    loop.create_task(remove_expired_users())
    web_app.run(host="0.0.0.0", port=8080)
