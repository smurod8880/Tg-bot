import aiohttp
import asyncio
import json
import logging
from datetime import datetime
from globals import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, bot_status
from database import store_signal as db_store_signal
from learning import LearningSystem

logger = logging.getLogger(__name__)

async def send_telegram_message(message: str, reply_markup=None):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.warning("Telegram credentials not set")
        return
        
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    
    if reply_markup:
        payload["reply_markup"] = json.dumps(reply_markup)
        
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                if response.status == 200:
                    bot_status['signals_sent'] += 1
                    return True
    except Exception as e:
        logger.error(f"Error sending to Telegram: {e}")
    return False

async def send_signal(symbol, timeframe, signal_type, strength, accuracy, indicators, signal_id):
    try:
        db_store_signal(signal_id, symbol, timeframe, signal_type, strength, accuracy, indicators)
        
        message = f"""
🎯 <b>ТОРГОВЫЙ СИГНАЛ [{signal_id[:6]}]</b>

<b>Пара:</b> {symbol}
<b>Таймфрейм:</b> {timeframe}
<b>Сигнал:</b> {'📈 ПОКУПКА' if signal_type == 'BUY' else '📉 ПРОДАЖА'}
<b>Сила сигнала:</b> {strength:.2%}
<b>Точность:</b> {accuracy:.1f}%
<b>Активные индикаторы:</b> {', '.join(indicators)}

<b>Время:</b> {datetime.now().strftime('%H:%M:%S %d.%m.%Y')}
        """
        
        await send_telegram_message(message.strip())
        
    except Exception as e:
        logger.error(f"Error sending signal: {e}")

async def send_demo_signals():
    """Отправка демонстрационного сообщения с сигналами для всех пар и таймфреймов"""
    from globals import TRADING_PAIRS, TIMEFRAMES
    message = "📊 <b>Демонстрационное сообщение с сигналами</b>\n\n"
    for symbol in TRADING_PAIRS:
        for timeframe in TIMEFRAMES:
            message += f"Пара: {symbol}, Таймфрейм: {timeframe}, Сигнал: Пример BUY, Сила: 90%, Индикаторы: EMA, MACD, RSI\n"
    await send_telegram_message(message.strip())

async def handle_telegram_updates():
    if not TELEGRAM_BOT_TOKEN:
        return
        
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
    offset = 0
    
    while bot_status['running']:
        try:
            params = {'offset': offset, 'timeout': 30}
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        for update in data.get('result', []):
                            offset = update['update_id'] + 1
                            if 'message' in update:
                                await process_message(update['message'])
        except Exception as e:
            logger.error(f"Telegram update error: {e}")
        await asyncio.sleep(1)

async def process_message(message):
    chat_id = str(message['chat']['id'])
    text = message.get('text', '').lower()
    
    if chat_id != TELEGRAM_CHAT_ID:
        return
        
    if text == '/start':
        if bot_status['running']:
            await send_telegram_message("🤖 Бот уже запущен!")
            return
        await send_start_message()
        from core import init_bot
        await init_bot()
        await send_telegram_message("🟢 Подключение к Binance успешно! Анализ начат.")
        if bot_status['first_run']:
            await send_demo_signals()
            bot_status['first_run'] = False

async def send_start_message():
    await send_telegram_message("🤖 <b>Crypto Trading Bot PRO</b>\n\nБот готов к запуску. Используйте /start для начала анализа.")
