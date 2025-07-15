import asyncio
import logging
from database import init_database, load_weights, save_weights
from telegram import handle_telegram_updates
from websocket import start_websocket_connections, stop_websocket_connections
from signal_analyzer import SignalAnalyzer, stop_analysis
from globals import bot_status, indicator_weights
from learning import LearningSystem

logger = logging.getLogger(__name__)

async def init_bot():
    """Инициализация и запуск бота"""
    try:
        if bot_status['running']:
            logger.info("Bot already running")
            return
            
        logger.info("Starting bot...")
        init_database()
        
        # Загрузка адаптивных весов
        loaded_weights = load_weights()
        if loaded_weights:
            indicator_weights.update(loaded_weights)
        
        # Инициализация системы обучения
        LearningSystem.initialize()
        
        # Запуск обработки Telegram сообщений
        asyncio.create_task(handle_telegram_updates())
        
        # Запуск WebSocket соединений
        asyncio.create_task(start_websocket_connections())
        
        # Запуск анализатора сигналов
        analyzer = SignalAnalyzer()
        asyncio.create_task(analyzer.analyze_all())
        
        bot_status['running'] = True
        logger.info("Bot started successfully")
    except Exception as e:
        logger.exception(f"Bot start failed: {e}")
        raise

async def stop_bot():
    """Остановка бота"""
    logger.info("Stopping bot...")
    bot_status['running'] = False
    await stop_websocket_connections()
    stop_analysis()
    
    # Сохранение весов перед остановкой
    save_weights(indicator_weights)
    LearningSystem.save_performance()
    
    logger.info("Bot stopped")
