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
# Load environment variables (set these in Render dashboard)
load_dotenv()

TOKEN = os.getenv("TOKEN")
NOTIFY_USER_ID = int(os.getenv("NOTIFY_USER_ID"))  # Your user ID for DMs

# Server & Channel IDs for public alerts
SERVER_ID = 1464772039427756076   # Your server (not strictly needed but useful for logging)
CHANNEL_ID = 1465574116185866261  # The text channel to post price alerts

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
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            await asyncio.sleep(random.uniform(0, 10))  # Small random delay

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

    # Startup DM to you
    try:
        user = await bot.fetch_user(NOTIFY_USER_ID)
        await user.send(f"**Bot awake!** Watching {ITEM_NAME} at {ITEM_URL}")
        print("Startup DM sent successfully")
    except Exception as e:
        print(f"Startup DM failed: {type(e).__name__}: {e}")

    # Startup message to the server channel
    try:
        channel = bot.get_channel(CHANNEL_ID)
        if channel is None:
            print(f"Channel {CHANNEL_ID} not found in cache.")
        else:
            await channel.send(
                f"**Bot online!** Monitoring **{ITEM_NAME}**\n"
                f"Current best price checking every {CHECK_INTERVAL_SECONDS}s → {ITEM_URL}"
            )
            print(f"Startup message sent to channel {CHANNEL_ID}")
    except Exception as e:
        print(f"Failed to send startup to channel {CHANNEL_ID}: {type(e).__name__}: {e}")

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
                change_text = "DROP!" if current < previous_best_price else "UP!"
                msg = (
                    f"**{change_text}** {ITEM_NAME} → **{current:,}** Robux "
                    f"(was {previous_best_price:,})\n{ITEM_URL}"
                )

                # Send DM (private alert to you)
                try:
                    user = await bot.fetch_user(NOTIFY_USER_ID)
                    await user.send(msg)
                    print(f"DM sent! Change: {previous_best_price:,} → {current:,}")
                except Exception as e:
                    print(f"DM failed: {type(e).__name__}: {e}")

                # Send to server channel (public alert)
                try:
                    channel = bot.get_channel(CHANNEL_ID)
                    if channel:
                        # Optional: add @everyone only on big drops (e.g. if current < some threshold)
                        # await channel.send(f"@everyone {msg}")
                        await channel.send(msg)  # normal message
                        print(f"Channel alert sent to {CHANNEL_ID}")
                    else:
                        print("Channel not found — skipping public alert")
                except Exception as e:
                    print(f"Channel alert failed: {type(e).__name__}: {e}")

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