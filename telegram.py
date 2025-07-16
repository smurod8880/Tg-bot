import aiohttp
import asyncio
import json
import logging
import time
from datetime import datetime
from globals import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, bot_status

logger = logging.getLogger(__name__)

async def validate_telegram_token():
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.error("Telegram credentials not set")
        return False
        
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getMe"
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
            async with session.get(url) as response:
                if response.status == 200:
                    return True
                data = await response.json()
                logger.error("Token validation failed: %s", data.get('description', 'Unknown error'))
    except Exception as e:
        logger.error("Error validating token: %s", str(e))
    return False

async def send_telegram_message(message: str, max_retries=5):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.error("Telegram credentials not set. Skipping message.")
        return False
        
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    
    for attempt in range(max_retries):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=15)) as response:
                    if response.status == 200:
                        bot_status['signals_sent'] = bot_status.get('signals_sent', 0) + 1
                        return True
                    elif response.status == 429:
                        retry_after = int(response.headers.get('Retry-After', 5))
                        logger.warning("Rate limited. Waiting %s seconds...", retry_after)
                        await asyncio.sleep(retry_after)
                        continue
                    else:
                        logger.error("Failed to send message. Status: %s", response.status)
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            logger.warning("Network error (attempt %s/%s): %s", attempt+1, max_retries, str(e))
            await asyncio.sleep(2 ** attempt)
        except Exception as e:
            logger.error("Unexpected error: %s", str(e))
            break
            
    logger.error("Failed to send message after %s attempts", max_retries)
    return False

async def send_signal(symbol, timeframe, signal_type, strength, accuracy, indicators, signal_id):
    try:
        message = f"""
🎯 <b>ТОРГОВЫЙ СИГНАЛ [{signal_id[:6]}]</b>

<b>Пара:</b> {symbol}
<b>Таймфрейм:</b> {timeframe}
<b>Сигнал:</b> {'📈 ПОКУПКА' if signal_type == 'BUY' else '📉 ПРОДАЖА'}
<b>Сила сигнала:</b> {strength:.2%}
<b>Точность:</b> {accuracy:.1f}%
<b>Активные индикаторы:</b> {', '.join(indicators)}

<b>Время:</b> {datetime.now().strftime('%H:%M:%S %d.%m.%Y')}
        """.strip()
        return await send_telegram_message(message)
    except Exception as e:
        logger.error("Error sending signal: %s", str(e))
        return False

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
    """.strip()
    return await send_telegram_message(message)
