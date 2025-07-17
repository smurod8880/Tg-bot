import sys
import os
import logging
from fastapi import FastAPI, HTTPException
import uvicorn
from core import init_bot, stop_bot
from telegram import send_telegram_message, send_demo_signal
from globals import bot_status

# Проверка критических переменных окружения
REQUIRED_ENV_VARS = ['TELEGRAM_BOT_TOKEN', 'TELEGRAM_CHAT_ID']
missing_vars = [var for var in REQUIRED_ENV_VARS if not os.environ.get(var)]

# Настройка логгера
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

if missing_vars:
    logger.error("Missing required environment variables: %s", ", ".join(missing_vars))
    if "RENDER" in os.environ:
        logger.error("Application will exit due to missing environment variables")
        sys.exit(1)

app = FastAPI(title="Crypto Trading Bot Pro", version="2.0")

@app.on_event("startup")
async def startup_event():
    logger.info("Bot API started")
    logger.info("Environment check:")
    logger.info(f"TELEGRAM_BOT_TOKEN: {'SET' if os.environ.get('TELEGRAM_BOT_TOKEN') else 'MISSING'}")
    logger.info(f"TELEGRAM_CHAT_ID: {'SET' if os.environ.get('TELEGRAM_CHAT_ID') else 'MISSING'}")
    
    bot_status.update({
        'running': False,
        'first_run': True,
        'signals_sent': 0,
        'profitable_signals': 0,
        'unprofitable_signals': 0
    })
    logger.info("Bot status initialized")

@app.get("/")
def home():
    return {
        "status": "Bot is ready",
        "running": bot_status.get('running', False),
        "signals_sent": bot_status.get('signals_sent', 0),
        "telegram_configured": bool(os.environ.get('TELEGRAM_BOT_TOKEN')) and bool(os.environ.get('TELEGRAM_CHAT_ID'))
    }

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
            logger.warning("Failed to send initial Telegram message")
        if bot_status.get('first_run', True):
            await send_demo_signal()
            success = await send_telegram_message("✅ <b>Статус анализа:</b> Подключение успешно, анализ проводится успешно, ожидается генерация сигнала при вероятности 90%+.")
            if not success:
                logger.warning("Failed to send status Telegram message")
            bot_status['first_run'] = False
        bot_status['running'] = True
        logger.info("Bot started successfully.")
        return {"status": "started", "signals_sent": bot_status.get('signals_sent', 0)}
    except Exception as e:
        logger.error("Error starting bot: %s", str(e))
        raise HTTPException(status_code=500, detail=f"Failed to start bot: {str(e)}")

@app.get("/stop")
async def stop():
    if not bot_status.get('running', False):
        return {"status": "already_stopped"}
    try:
        await stop_bot()
        success = await send_telegram_message("🔴 Бот остановлен!")
        if not success:
            logger.warning("Failed to send stop Telegram message")
        bot_status['running'] = False
        return {"status": "stopped"}
    except Exception as e:
        logger.error("Error stopping bot: %s", str(e))
        raise HTTPException(status_code=500, detail=f"Failed to stop bot: {str(e)}")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False, access_log=False)
