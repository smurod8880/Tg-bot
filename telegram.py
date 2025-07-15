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
        
        keyboard = {
            "inline_keyboard": [
                [
                    {"text": "✅ Успех", "callback_data": f"signal_success:{signal_id}"},
                    {"text": "❌ Неудача", "callback_data": f"signal_fail:{signal_id}"}
                ],
                [{"text": "📊 Отчет", "callback_data": "performance_report"}]
            ]
        }
        
        await send_telegram_message(message.strip(), keyboard)
        
    except Exception as e:
        logger.error(f"Error sending signal: {e}")

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
                            elif 'callback_query' in update:
                                await process_callback_query(update['callback_query'])
        except Exception as e:
            logger.error(f"Telegram update error: {e}")
        await asyncio.sleep(1)

async def process_message(message):
    chat_id = str(message['chat']['id'])
    text = message.get('text', '').lower()
    
    if chat_id != TELEGRAM_CHAT_ID:
        return
        
    if text == '/start':
        await send_start_message()
    elif text == '/status':
        await send_status_message()
    elif text == '/performance':
        await send_performance_report()
    elif text == '/start_bot':
        from core import init_bot
        await init_bot()
    elif text == '/stop_bot':
        from core import stop_bot
        await stop_bot()

async def process_callback_query(callback_query):
    try:
        data = callback_query['data']
        chat_id = str(callback_query['message']['chat']['id'])
        callback_id = callback_query['id']

        # 🟢 Telegram требует подтверждение callback-запроса
        async with aiohttp.ClientSession() as session:
            await session.post(
                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/answerCallbackQuery",
                json={"callback_query_id": callback_id}
            )

        if chat_id != TELEGRAM_CHAT_ID:
            return

        if data.startswith('signal_success:'):
            signal_id = data.split(':')[1]
            await update_signal_result(signal_id, True)
            await send_telegram_message(f"✅ Сигнал {signal_id[:6]} отмечен как успешный")
        elif data.startswith('signal_fail:'):
            signal_id = data.split(':')[1]
            await update_signal_result(signal_id, False)
            await send_telegram_message(f"❌ Сигнал {signal_id[:6]} отмечен как неудачный")
        elif data == 'performance_report':
            await send_performance_report()
        elif data == 'start_bot':
            from core import init_bot
            await init_bot()
            await send_telegram_message("🟢 Бот был успешно запущен через Telegram")
        elif data == 'stop_bot':
            from core import stop_bot
            await stop_bot()
            await send_telegram_message("🔴 Бот был остановлен через Telegram")
        elif data == 'get_status':
            await send_status_message()
    except Exception as e:
        logger.error(f"Error processing callback: {e}")

async def update_signal_result(signal_id, profitable):
    from database import update_signal_result as db_update_signal_result
    db_update_signal_result(signal_id, profitable)
    
    if profitable:
        bot_status['profitable_signals'] += 1
    else:
        bot_status['unprofitable_signals'] += 1
    
    LearningSystem.update_weights({
        'id': signal_id,
        'profitable': profitable
    })

async def send_start_message():
    keyboard = {
        "inline_keyboard": [
            [{"text": "🟢 Запустить бота", "callback_data": "start_bot"}],
            [{"text": "🔴 Остановить бота", "callback_data": "stop_bot"}],
            [{"text": "📊 Статус", "callback_data": "get_status"}],
            [{"text": "📈 Производительность", "callback_data": "performance_report"}]
        ]
    }
    await send_telegram_message("🤖 <b>Crypto Trading Bot PRO</b>\n\nВыберите действие:", keyboard)

async def send_status_message():
    status = "🟢 Работает" if bot_status['running'] else "🔴 Остановлен"
    profit_ratio = bot_status['profitable_signals'] / (bot_status['profitable_signals'] + bot_status['unprofitable_signals']) if (bot_status['profitable_signals'] + bot_status['unprofitable_signals']) > 0 else 0
    
    message = (
        f"📊 <b>Статус бота</b>\n\n"
        f"{status}\n"
        f"Соединений: {bot_status['connections']}\n"
        f"Сигналов отправлено: {bot_status['signals_sent']}\n"
        f"Успешных сигналов: {bot_status['profitable_signals']}\n"
        f"Неудачных сигналов: {bot_status['unprofitable_signals']}\n"
        f"Процент успеха: {profit_ratio:.2%}"
    )
    await send_telegram_message(message)

async def send_performance_report():
    report = LearningSystem.get_performance_report()
    if not report:
        await send_telegram_message("📊 Данные о производительности отсутствуют")
        return
        
    message = "📈 <b>Отчет по производительности индикаторов</b>\n\n"
    for item in report[:10]:
        message += (
            f"{item['indicator']}:\n"
            f"  Успешность: {item['success_rate']:.2%}\n"
            f"  Вес: {item['weight']:.4f}\n\n"
        )
    
    await send_telegram_message(message)
