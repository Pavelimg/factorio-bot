import os

from dotenv import load_dotenv

load_dotenv()

tg_token = os.getenv("TELEGRAM_BOT_TOKEN", "")

if not tg_token:
    raise RuntimeError("TELEGRAM_BOT_TOKEN is not configured")

__all__ = ["tg_token"]

