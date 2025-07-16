import aiohttp
import asyncio
import json
import logging
from datetime import datetime
from globals import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, bot_status
from database import store_signal as db_store_signal
from learning import LearningSystem

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

async def validate_telegram_token():
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.error("Telegram credentials not set. Check TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID.")
        return False
    if len(TELEGRAM_BOT_TOKEN) < 20 or ':' not in TELEGRAM_BOT_TOKEN:
        logger.error("Invalid TELEGRAM_BOT_TOKEN format. Obtain a new token from @BotFather.")
        return False
    # Тестовый запрос для проверки токена
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getMe"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    logger.info("Telegram token validated successfully.")
                    return True
                else:
                    logger.error(f"Token validation failed. Status: {response.status}, Response: {await response.text()}")
                    return False
    except Exception as e:
        logger.error(f"Error validating token: {str(e)}")
        return False

async def send_telegram_message(message: str, reply_markup=None, max_retries=5):
    if not await validate_telegram_token():
        return False
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    if reply_markup:
        payload["reply_markup"] = json.dumps(reply_markup)
    for attempt in range(max_retries):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=15)) as response:
                    response_text = await response.text()
                    logger.info(f"API Response (Attempt {attempt + 1}/{max_retries}): Status {response.status}, Text: {response_text[:200]}")
                    if response.status == 200:
                        logger.info(f"Message sent successfully: {message[:50]}...")
                        bot_status['signals_sent'] = bot_status.get('signals_sent', 0) + 1
                        return True
                    else:
                        if response.status == 405:
                            logger.error("405 Method Not Allowed: Possible network restriction or Telegram API issue.")
                        elif response.status == 429:
                            retry_after = int(response.headers.get('Retry-After', 5))
                            logger.info(f"Rate limited. Waiting {retry_after} seconds...")
                            await asyncio.sleep(retry_after)
                            continue
                        elif "Unauthorized" in response_text:
                            logger.error("Unauthorized: TELEGRAM_BOT_TOKEN is invalid or expired.")
                            return False
                        if attempt == max_retries - 1:
                            logger.error(f"Max retries reached. Last response: {response_text}")
                            return False
                        await asyncio.sleep(2 ** attempt + 1)
        except aiohttp.ClientConnectorError as e:
            logger.error(f"Network error (attempt {attempt + 1}/{max_retries}): {str(e)}. Retrying...")
            if attempt == max_retries - 1:
                return False
            await asyncio.sleep(2 ** attempt + 1)
        except Exception as e:
            logger.error(f"Error sending to Telegram (attempt {attempt + 1}/{max_retries}): {str(e)}")
            if attempt == max_retries - 1:
                return False
            await asyncio.sleep(2 ** attempt + 1)
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
        logger.error(f"Error sending signal: {str(e)}")

async def send_demo_signal():
    demo_signal_id = f"DEMO-{int(time.time())}"
    message = f"""
🎯 <b>ПРИМЕР ТОРГОВОГО СИГНАЛА [{demo_signal_id[:6]}]</b>

<b>Пара:</b> BTCUSDT
<b>Таймфрейм:</b> 1h
<b>Сигнал:</b> 📈 ПОКУПКА
<b>Сила сигнала:</b> 92.50%
<b>Точность:</b> 91.0%
<b>Активные индикаторы:</b> EMA, MACD, RSI, Bollinger_Bands

<b>Время:</b> {datetime.now().strftime('%H:%M:%S %d.%m.%Y')}
<b>Примечание:</b> Это демонстрационный сигнал. Реальные сигналы будут следовать после анализа.
        """
    await send_telegram_message(message.strip())
