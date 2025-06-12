import asyncio
import time
from datetime import datetime
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pymongo import MongoClient
from config import API_ID, API_HASH, BOT_TOKEN, CHANNEL_ID, MONGO_URI

# Initialize Pyrogram bot and MongoDB
bot = Client("premium-bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
mongo = MongoClient(MONGO_URI)
db = mongo["premium_bot"]
users_col = db["users"]

ADMIN_ID = 6987799874  # 🔁 Replace with your Telegram user ID

# Add Premium User Command
@bot.on_message(filters.command("addpremium") & filters.user(ADMIN_ID))
async def add_premium(_, msg: Message):
    parts = msg.text.split()
    if len(parts) != 3:
        return await msg.reply("❌ Usage: /addpremium @username|user_id days")

    user_input = parts[1]
    days = int(parts[2])

    # Get user object
    try:
        if user_input.startswith("@"):
            user = await bot.get_users(user_input)
        else:
            user = await bot.get_users(int(user_input))
    except Exception as e:
        return await msg.reply(f"⚠️ Error: User not found\n\n{e}")

    # Create invite link
    try:
        invite = await bot.create_chat_invite_link(
            chat_id=CHANNEL_ID,
            member_limit=1,
            expire_date=int(time.time()) + (days * 86400)
        )
    except Exception as e:
        return await msg.reply(f"⚠️ Failed to create invite link:\n{e}")

    # Save to DB
    users_col.update_one(
        {"user_id": user.id},
        {"$set": {
            "user_id": user.id,
            "expires_at": time.time() + (days * 86400)
        }},
        upsert=True
    )

    await msg.reply(
        f"✅ Premium access added for <b>{user.first_name}</b>\n"
        f"📅 Duration: <code>{days}</code> days\n"
        f"🔗 Invite: {invite.invite_link}",
        parse_mode="HTML"
    )

# Admin Panel
@bot.on_message(filters.command("admin") & filters.user(ADMIN_ID))
async def admin_panel(_, msg: Message):
    total = users_col.count_documents({})
    now = time.time()
    expiring = users_col.count_documents({"expires_at": {"$lte": now + 3 * 86400}})

    text = (
        f"🔧 <b>Admin Panel</b>\n\n"
        f"👥 Total Premium Users: <code>{total}</code>\n"
        f"📆 Expiring Soon (3 days): <code>{expiring}</code>"
    )

    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("📤 Export CSV", callback_data="export_csv")],
        [InlineKeyboardButton("📆 Expiring Soon", callback_data="expiring_list")]
    ])

    await msg.reply(text, reply_markup=buttons, parse_mode="HTML")

# Handle admin panel buttons
@bot.on_callback_query()
async def handle_cb(bot, cb):
    if cb.data == "export_csv":
        users = users_col.find()
        csv_data = "user_id,expires_at\n"
        for u in users:
            expiry = datetime.utcfromtimestamp(u["expires_at"]).strftime("%Y-%m-%d %H:%M")
            csv_data += f"{u['user_id']},{expiry}\n"
        await cb.message.reply_document(
            document=("users.csv", csv_data.encode()),
            caption="📤 Exported Premium Users"
        )
        await cb.answer("Exported ✅")

    elif cb.data == "expiring_list":
        now = time.time()
        users = users_col.find({"expires_at": {"$lte": now + 3 * 86400}})
        text = "📆 <b>Users Expiring Soon:</b>\n"
        found = False
        for u in users:
            found = True
            exp = datetime.utcfromtimestamp(u["expires_at"]).strftime("%Y-%m-%d")
            text += f"• <code>{u['user_id']}</code> - {exp}\n"
        if not found:
            text = "✅ No users expiring in the next 3 days."
        await cb.message.reply(text, parse_mode="HTML")
        await cb.answer("Listed ✅")

# Start Command
@bot.on_message(filters.command("start"))
async def start(_, msg):
    await msg.reply("🤖 Bot is running!\nUse /addpremium @user 30 to add premium users.")

# Background: Check for expiry and remove users
async def check_expiry():
    while True:
        now = time.time()
        expired = users_col.find({"expires_at": {"$lte": now}})
        for user in expired:
            try:
                await bot.ban_chat_member(CHANNEL_ID, user["user_id"])
                await bot.unban_chat_member(CHANNEL_ID, user["user_id"])
                users_col.delete_one({"user_id": user["user_id"]})
                print(f"❌ Removed expired user: {user['user_id']}")
            except Exception as e:
                print(f"⚠️ Error removing {user['user_id']}: {e}")
        await asyncio.sleep(3600)

# Start Bot + Expiry Loop
async def main():
    await bot.start()
    print("✅ Bot started")
    await check_expiry()

if __name__ == "__main__":
    asyncio.run(main())
