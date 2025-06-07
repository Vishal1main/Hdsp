import os
import requests
from flask import Flask, request
from bs4 import BeautifulSoup

# Telegram Bot Token & Webhook Secret (set via env)
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "https://hdsp.onrender.com")
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

app = Flask(__name__)
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
}


@app.route(f"/{WEBHOOK_SECRET}", methods=["POST"])
def webhook():
    data = request.get_json()

    if "message" in data and "text" in data["message"]:
        chat_id = data["message"]["chat"]["id"]
        msg = data["message"]["text"].strip()

        if msg.startswith("https://joya9tv1.com/links/"):
            links = handle_full_scrape(msg)
            if links:
                for line in links:
                    send_message(chat_id, line)
            else:
                send_message(chat_id, "❌ Koi download link nahi mila.")
        else:
            send_message(chat_id, "🧩 Please send a valid Joya9TV link.")

    return {"ok": True}


def send_message(chat_id, text):
    requests.post(f"{API_URL}/sendMessage", json={
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    })


# STEP 1 → https://joya9tv1.com/links/... → extract joya9links.com/view/...
def get_view_link(intermediate_url):
    try:
        res = requests.get(intermediate_url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        a_tag = soup.select_one("table a[href*='joya9links.com/view/']")
        return a_tag["href"] if a_tag else None
    except Exception as e:
        print("Error getting view link:", e)
        return None


# STEP 2 → joya9links.com/view/... → extract list of hubcloud links
def get_hubcloud_links(view_url):
    try:
        res = requests.get(view_url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        links = []
        for li in soup.select("ul li a[href*='hubcloud.ink']"):
            links.append({
                "text": li.text.strip(),
                "url": li["href"]
            })
        return links
    except Exception as e:
        print("Error getting hubcloud links:", e)
        return []


# STEP 3 → hubcloud.ink/... → extract gamerxyt intermediate link
def get_gamerxyt_link(hubcloud_url):
    try:
        res = requests.get(hubcloud_url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        a_tag = soup.select_one("div.vd a[href*='gamerxyt.com/hubcloud.php']")
        return a_tag["href"] if a_tag else None
    except Exception as e:
        print("Error getting gamerxyt link:", e)
        return None


# STEP 4 → gamerxyt.com/... → extract final R2.dev download link
def get_final_download_link(gamerxyt_url):
    try:
        res = requests.get(gamerxyt_url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        a_tag = soup.select_one("a.btn-success[href*='r2.dev']")
        return a_tag["href"] if a_tag else None
    except Exception as e:
        print("Error getting final link:", e)
        return None


# Main function that handles the full scraping chain
def handle_full_scrape(main_link):
    view_link = get_view_link(main_link)
    if not view_link:
        return []

    hubclouds = get_hubcloud_links(view_link)
    results = []

    for entry in hubclouds:
        label = entry["text"]
        hub_url = entry["url"]
        gamerxyt = get_gamerxyt_link(hub_url)
        if not gamerxyt:
            results.append(f"<b>{label}</b>: ❌ GamerXYT link not found.")
            continue

        final = get_final_download_link(gamerxyt)
        if final:
            results.append(f"<b>{label}</b>:\n<code>{final}</code>")
        else:
            results.append(f"<b>{label}</b>: ❌ Final link not found.")

    return results


if __name__ == "__main__":
    app.run(debug=True)
