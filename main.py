import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import logging
from fastapi import FastAPI, HTTPException
import uvicorn
from core import init_bot, stop_bot
from telegram import send_telegram_message, send_demo_signal
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
    bot_status.clear()
    bot_status.update({'running': False, 'first_run': True, 'signals_sent': 0})

@app.get("/")
def home():
    return {"status": "Bot is ready", "running": bot_status.get('running', False), "signals_sent": bot_status.get('signals_sent', 0)}

@app.get("/start")
async def start():
    if bot_status.get('running', False):
        return {"status": "already_running"}
    try:
        logger.info("Initiating bot startup...")
        await init_bot()
        logger.info("Bot initialized, sending Telegram messages...")
        success = await send_telegram_message("🟢 Подключение к Binance успешно! Анализ начат.")
        if not success:
            logger.error("Failed to send initial message to Telegram. Check token and network.")
        if bot_status.get('first_run', True):
            await send_demo_signal()
            success = await send_telegram_message("✅ <b>Статус анализа:</b> Подключение успешно, анализ проводится успешно, ожидается генерация сигнала при вероятности 90%+.")
            if not success:
                logger.error("Failed to send demo or status message to Telegram.")
            bot_status['first_run'] = False
        bot_status['running'] = True
        logger.info("Bot started successfully.")
        return {"status": "started", "signals_sent": bot_status.get('signals_sent', 0)}
    except Exception as e:
        logger.error(f"Error starting bot: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to start bot: {str(e)}")

@app.get("/stop")
async def stop():
    if not bot_status.get('running', False):
        return {"status": "already_stopped"}
    try:
        await stop_bot()
        success = await send_telegram_message("🔴 Бот остановлен!")
        if not success:
            logger.error("Failed to send stop message to Telegram.")
        bot_status['running'] = False
        return {"status": "stopped"}
    except Exception as e:
        logger.error(f"Error stopping bot: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to stop bot: {str(e)}")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False, access_log=False)
