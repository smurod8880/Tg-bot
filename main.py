import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import logging
from fastapi import FastAPI, HTTPException
import uvicorn
from core import init_bot, stop_bot
from telegram import send_telegram_message, send_demo_signal, start_telegram_listener
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
    # Запускаем слушатель Telegram обновлений в фоновом режиме
    asyncio.create_task(start_telegram_listener())

@app.get("/")
def home():
    return {"status": "Bot is ready", "running": bot_status['running']}

@app.get("/start")
async def start():
    if bot_status['running']:
        return {"status": "already_running"}
    try:
        await init_bot()
        await send_telegram_message("🟢 Подключение к Binance успешно! Анализ начат.")
        if bot_status.get('first_run', True):  # Используем get с значением по умолчанию True
            await send_demo_signal()
            await send_telegram_message("✅ <b>Статус анализа:</b> Подключение успешно, анализ проводится успешно, ожидается генерация сигнала при вероятности 90%+.")
            bot_status['first_run'] = False
        return {"status": "started"}
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start bot: {e}")

@app.get("/stop")
async def stop():
    if not bot_status['running']:
        return {"status": "already_stopped"}
    try:
        await stop_bot()
        await send_telegram_message("🔴 Бот остановлен!")
        return {"status": "stopped"}
    except Exception as e:
        logger.error(f"Error stopping bot: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to stop bot: {e}")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False, access_log=False)
