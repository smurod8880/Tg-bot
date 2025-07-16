import asyncio
import logging
from database import init_database, load_weights, save_weights
from websocket import start_websocket_connections, stop_websocket_connections
from signal_analyzer import SignalAnalyzer, stop_analysis
from globals import bot_status, indicator_weights
from learning import LearningSystem

logger = logging.getLogger(__name__)

async def init_bot():
    """Инициализация и запуск бота"""
    try:
        if bot_status.get('running', False):
            logger.info("Bot already running")
            return
            
        logger.info("Starting bot...")
        
        # Асинхронная инициализация базы данных
        await asyncio.to_thread(init_database)
        
        # Загрузка адаптивных весов
        loaded_weights = await asyncio.to_thread(load_weights)
        if loaded_weights:
            indicator_weights.update(loaded_weights)
        
        # Инициализация системы обучения
        LearningSystem.initialize()
        
        # Запуск WebSocket соединений
        asyncio.create_task(start_websocket_connections())
        
        # Запуск анализатора сигналов
        analyzer = SignalAnalyzer()
        asyncio.create_task(analyzer.analyze_all())
        
        bot_status['running'] = True
        logger.info("Bot started successfully")
    except Exception as e:
        logger.exception("Bot start failed: %s", str(e))
        raise

async def stop_bot():
    """Остановка бота"""
    try:
        if not bot_status.get('running', False):
            logger.info("Bot not running")
            return
            
        logger.info("Stopping bot...")
        bot_status['running'] = False
        
        # Остановка WebSocket соединений
        await stop_websocket_connections()
        
        # Остановка анализатора сигналов
        stop_analysis()
        
        # Асинхронное сохранение данных
        await asyncio.to_thread(save_weights, indicator_weights)
        await asyncio.to_thread(LearningSystem.save_performance)
        
        logger.info("Bot stopped successfully")
    except Exception as e:
        logger.exception("Bot stop failed: %s", str(e))
        raise
