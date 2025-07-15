import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import logging
from fastapi import FastAPI, HTTPException
import uvicorn
from core import init_bot, stop_bot
from telegram import send_telegram_message
from globals import bot_status

# Настройка логгера
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Crypto Trading Bot Pro", version="2.0")

@app.on_event("startup")
async def startup_event():
    logger.info("Bot API started")

@app.get("/")
def home():
    return {"status": "Bot is ready", "running": bot_status['running']}

@app.get("/start")
async def start():
    if bot_status['running']:
        return {"status": "already_running"}
    await init_bot()
    await send_telegram_message("🟢 Бот запущен!")
    return {"status": "started"}

@app.get("/stop")
async def stop():
    if not bot_status['running']:
        return {"status": "already_stopped"}
    await stop_bot()
    await send_telegram_message("🔴 Бот остановлен!")
    return {"status": "stopped"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False, access_log=False)
