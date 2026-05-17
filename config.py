import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN not set in .env")

ADMIN_ID = os.getenv("ADMIN_ID")
if not ADMIN_ID or not ADMIN_ID.isdigit():
    raise RuntimeError("ADMIN_ID must be a numeric Telegram ID in .env")
ADMIN_ID = int(ADMIN_ID)

CARD_NUMBER = os.getenv("CARD_NUMBER")
if not CARD_NUMBER:
    raise RuntimeError("CARD_NUMBER not set in .env")

DATABASE_PATH = os.getenv("DATABASE_PATH", "data/saint_bot.db")

PACKAGES = {
    "💎 86 алмазов":    {"diamonds": 86,   "price": 15_000},
    "💎 172 алмаза":   {"diamonds": 172,  "price": 29_000},
    "💎 257 алмазов":  {"diamonds": 257,  "price": 43_000},
    "💎 344 алмаза":   {"diamonds": 344,  "price": 57_000},
    "💎 429 алмазов":  {"diamonds": 429,  "price": 70_000},
    "💎 514 алмазов":  {"diamonds": 514,  "price": 84_000},
    "💎 706 алмазов":  {"diamonds": 706,  "price": 114_000},
    "💎 878 алмазов":  {"diamonds": 878,  "price": 141_000},
    "💎 963 алмаза":   {"diamonds": 963,  "price": 154_000},
    "💎 1412 алмазов": {"diamonds": 1412, "price": 225_000},
    "💎 2195 алмазов": {"diamonds": 2195, "price": 348_000},
    "💎 3688 алмазов": {"diamonds": 3688, "price": 582_000},
}


def format_price(amount: int) -> str:
    return f"{amount:,}".replace(",", " ") + " сум"
