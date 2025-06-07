from aiogram import Bot, Dispatcher, types, executor
import requests
from bs4 import BeautifulSoup
import asyncio
import os

API_TOKEN = os.getenv("BOT_TOKEN", "7861502352:AAFcS7xZk2NvN7eJ3jcPm_HyYh74my8vRyU")
CHAT_ID = os.getenv("CHAT_ID", "-1002204445436")
PORT = int(os.getenv("PORT", 8000))
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # Required for webhook mode

if not WEBHOOK_URL:
    raise ValueError("WEBHOOK_URL environment variable is required!")

bot = Bot(token=API_TOKEN, parse_mode="HTML")
dp = Dispatcher(bot)

VALID_DOMAINS = {
    "fastdl.icu": "FastDL",
    "vcloud.lol": "VCloud",
    "oxxfile.info": "OXXFile",
    "filepress.live": "Filepress",
    "gdtot.dad": "GDToT",
    "dgdrive.site": "DropGalaxy",
    "teraboxapp.com": "TeraBox",
    "linkbox.to": "LinkBox",
    "sharer.pw": "Sharer",
    "nexdrive.lol": "NexDrive"
}

sent_links = set()

def extract_nexdrive_links(post_url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(post_url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        nex_links = [a["href"] for a in soup.find_all("a", href=True) if "nexdrive.lol" in a["href"]]
        title_tag = soup.select_one("h5, h1, h2")
        title = title_tag.get_text(strip=True) if title_tag else "🎞 New Post"
        return title, nex_links
    except Exception as e:
        print(f"[ERROR: extract_nexdrive_links] {e}")
        return None, []

def extract_final_links(nexdrive_url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(nexdrive_url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        final_links = []
        for a in soup.find_all("a", href=True):
            href = a["href"]
            for domain, name in VALID_DOMAINS.items():
                if domain in href:
                    final_links.append((name, href))
        return final_links
    except Exception as e:
        print(f"[ERROR: extract_final_links] {e}")
        return []

async def auto_post_checker():
    while True:
        try:
            home = requests.get("https://xprimehub.lat/", timeout=10)
            soup = BeautifulSoup(home.text, "html.parser")
            posts = soup.select("h2.entry-title a")

            for post in posts:
                link = post["href"]
                if link in sent_links:
                    continue

                sent_links.add(link)
                title, nex_links = extract_nexdrive_links(link)
                final_links = []

                for nex in nex_links:
                    final_links += extract_final_links(nex)

                if final_links:
                    text = f"<b>{title}</b>\n\n"
                    for i, (name, url) in enumerate(final_links, 1):
                        text += f"🔗 <b>{name} Link {i}:</b> <code>{url}</code>\n"
                    await bot.send_message(CHAT_ID, text)

            await asyncio.sleep(300)  # check every 5 minutes

        except Exception as e:
            print(f"[ERROR: auto_post_checker] {e}")
            await asyncio.sleep(60)

@dp.message_handler(commands=["start"])
async def start(msg: types.Message):
    await msg.reply("👋 Send any xprimehub.lat post link and I will scrape download links!")

@dp.message_handler()
async def handle_post_link(msg: types.Message):
    text = msg.text.strip()
    if text.startswith("http") and "xprimehub.lat" in text:
        await msg.reply("🔍 Scraping download links...")
        title, nex_links = extract_nexdrive_links(text)
        final_links = []

        for nex in nex_links:
            final_links += extract_final_links(nex)

        if final_links:
            reply = f"<b>{title}</b>\n\n"
            for i, (name, url) in enumerate(final_links, 1):
                reply += f"🔗 <b>{name} Link {i}:</b> <code>{url}</code>\n"
            await msg.reply(reply)
        else:
            await msg.reply("⚠️ No final download links found.")
    else:
        await msg.reply("❌ Invalid link. Please send a valid xprimehub.lat post link.")

async def on_startup(dp):
    await bot.set_webhook(WEBHOOK_URL)
    asyncio.create_task(auto_post_checker())

async def on_shutdown(dp):
    await bot.delete_webhook()

if __name__ == "__main__":
    executor.start_webhook(
        dispatcher=dp,
        webhook_path="/webhook",
        on_startup=on_startup,
        on_shutdown=on_shutdown,
        skip_updates=True,
        host="0.0.0.0",
        port=PORT,
    )
