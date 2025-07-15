import os

# ======== НАСТРОЙКИ ДЛЯ РУЧНОГО ИЗМЕНЕНИЯ ========
# Если не используете переменные окружения, задайте значения здесь:

# Для Telegram:
MANUAL_TELEGRAM_BOT_TOKEN = "8177951186:AAH6h4_BEezrjDFIwdDUfiqxPNv-8aCb8u0"
MANUAL_TELEGRAM_CHAT_ID = "5331567990"

# Торговые пары и таймфреймы
TRADING_PAIRS = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'XRPUSDT', 
                 'DOGEUSDT', 'ADAUSDT', 'MATICUSDT', 'AVAXUSDT', 'DOTUSDT']
TIMEFRAMES = ['1m', '5m', '15m', '30m', '1h', '4h', '1d']

# Пороговые значения
SIGNAL_THRESHOLD = 0.85
MIN_INDICATORS = 5
CONFIRMATION_THRESHOLD = 0.7  # Порог подтверждения на высшем ТФ
# ================================================

# Состояние бота
bot_status = {
    'running': False,
    'paused': False,
    'connections': 0,
    'data_received': 0,
    'signals_sent': 0,
    'profitable_signals': 0,
    'unprofitable_signals': 0
}

# Данные рынка
market_data = {}

# Веса индикаторов (базовые значения)
indicator_weights = {
    'EMA': 0.05,
    'SMA': 0.05,
    'MACD': 0.07,
    'RSI': 0.06,
    'Bollinger_Bands': 0.06,
    'Supertrend': 0.05,
    'Ichimoku': 0.06,
    'Parabolic_SAR': 0.04,
    'ADX': 0.05,
    'Hull_MA': 0.05,
    'Pivot_Points': 0.04,
    'VWAP': 0.05,
    'CCI': 0.04,
    'Stochastic': 0.05,
    'TSI': 0.04,
    'Williams_R': 0.04,
    'OBV': 0.05,
    'Volume_Oscillator': 0.05,
    'Chaikin_MF': 0.04,
    'Z_Score': 0.04,
    'ATR': 0.04,
    'Keltner_Channel': 0.05,
    'Donchian_Channel': 0.04,
    'Heikin_Ashi': 0.05,
    'Engulfing': 0.06,
    'Pin_Bar': 0.06,
    'Hammer': 0.06,
    'Doji': 0.05,
    'Combined_Trend_Volume': 0.07,
    'Stability_Filter': 0.08
}

# Конфигурация Telegram
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', MANUAL_TELEGRAM_BOT_TOKEN)
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', MANUAL_TELEGRAM_CHAT_ID)

# Иерархия таймфреймов для подтверждения сигналов
TIMEFRAME_HIERARCHY = {
    '1m': ['5m', '15m'],
    '5m': ['15m', '30m'],
    '15m': ['30m', '1h'],
    '30m': ['1h', '4h'],
    '1h': ['4h', '1d'],
    '4h': ['1d'],
    '1d': []
}
