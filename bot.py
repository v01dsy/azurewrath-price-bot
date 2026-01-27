import discord
import requests
from bs4 import BeautifulSoup
import re
import asyncio
import random
import time
import os
from dotenv import load_dotenv

# ────────────────────────────────────────────────
# Load environment variables (set these in your hosting platform dashboard)
load_dotenv()

TOKEN = os.getenv("TOKEN")
NOTIFY_USER_ID = int(os.getenv("NOTIFY_USER_ID"))  # Convert to int right away

if not TOKEN or not NOTIFY_USER_ID:
    raise ValueError("TOKEN or NOTIFY_USER_ID not set in environment variables!")

ITEM_NAME = "Azurewrath Fabergé Egg"
ITEM_URL = "https://www.rolimons.com/item/76692318"
CHECK_INTERVAL_SECONDS = 60  # 60 seconds = 1 minute
# ────────────────────────────────────────────────

intents = discord.Intents.default()
intents.message_content = True

bot = discord.Client(intents=intents)

previous_best_price = None

async def get_best_price():
    while True:
        try:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            await asyncio.sleep(random.uniform(0, 10))  # small random delay to look more human

            r = requests.get(ITEM_URL, headers=headers, timeout=15)
            r.raise_for_status()

            soup = BeautifulSoup(r.text, "html.parser")
            text = soup.get_text(" ", strip=True)

            match = re.search(r"Best Price\s*[:\-]?\s*([\d,]+)", text, re.IGNORECASE)
            if match:
                price_str = match.group(1).replace(",", "")
                return int(price_str)

            print("Price not found - retrying in 10s")
            await asyncio.sleep(10)
        except Exception as e:
            print(f"Price fetch error: {type(e).__name__}: {e} - retrying in 10s")
            await asyncio.sleep(10)

@bot.event
async def on_ready():
    global previous_best_price
    print(f"Logged in as {bot.user} — Monitoring {ITEM_NAME}")

    try:
        user = await bot.fetch_user(NOTIFY_USER_ID)
        await user.send(f"**Bot awake!** Watching {ITEM_NAME} at {ITEM_URL}")
        print("Startup DM sent successfully")
    except Exception as e:
        print(f"Startup DM failed: {type(e).__name__}: {e}")

    current = await get_best_price()
    previous_best_price = current
    print(f"Starting price: {current:,} Robux")

    asyncio.create_task(price_monitor_loop())

async def price_monitor_loop():
    global previous_best_price
    while True:
        try:
            current = await get_best_price()
            print(f"Checked: {current:,} Robux")

            if previous_best_price is not None and current != previous_best_price:
                try:
                    user = await bot.fetch_user(NOTIFY_USER_ID)
                    if current < previous_best_price:
                        msg = f"**DROP!** {ITEM_NAME} → **{current:,}** Robux (was {previous_best_price:,})\n{ITEM_URL}"
                    else:
                        msg = f"**UP!** {ITEM_NAME} → **{current:,}** Robux (was {previous_best_price:,})\n{ITEM_URL}"
                    await user.send(msg)
                    print(f"DM sent! Change: {previous_best_price:,} → {current:,}")
                except Exception as e:
                    print(f"DM failed: {type(e).__name__}: {e} - continuing anyway")

            previous_best_price = current

        except Exception as e:
            print(f"Monitor loop error: {type(e).__name__}: {e} - continuing")

        await asyncio.sleep(CHECK_INTERVAL_SECONDS)

async def run_bot():
    while True:
        try:
            print("Connecting to Discord...")
            await bot.start(TOKEN)
        except Exception as e:
            print(f"Connection failed: {type(e).__name__}: {e}")
            print("Reconnecting in 10 seconds...")
            await asyncio.sleep(10)

if __name__ == "__main__":
    print("Starting Azurewrath price monitoring bot...")
    asyncio.run(run_bot())