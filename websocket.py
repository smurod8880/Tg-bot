import asyncio
import websockets
import json
import logging
from globals import TRADING_PAIRS, TIMEFRAMES, bot_status, market_data

logger = logging.getLogger(__name__)
websocket_tasks = []

async def binance_websocket(symbol, timeframe):
    stream_name = f"{symbol.lower()}@kline_{timeframe}"
    uri = f"wss://stream.binance.com:9443/ws/{stream_name}"
    
    while bot_status.get('running', False):
        try:
            async with websockets.connect(uri, ping_interval=20, ping_timeout=25) as websocket:
                logger.info("Connected to %s %s", symbol, timeframe)
                bot_status['connections'] = bot_status.get('connections', 0) + 1
                
                async for message in websocket:
                    if not bot_status.get('running', False):
                        break
                    data = json.loads(message)
                    await process_kline_data(symbol, timeframe, data.get('k', {}))
        except websockets.ConnectionClosed:
            logger.warning("Connection closed for %s %s", symbol, timeframe)
        except Exception as e:
            logger.error("WebSocket error for %s %s: %s", symbol, timeframe, str(e))
            await asyncio.sleep(5)
        finally:
            bot_status['connections'] = max(0, bot_status.get('connections', 0) - 1)

async def process_kline_data(symbol, timeframe, kline):
    if not kline:
        return
        
    try:
        candle = {
            'open': float(kline['o']),
            'high': float(kline['h']),
            'low': float(kline['l']),
            'close': float(kline['c']),
            'volume': float(kline['v']),
            'timestamp': kline['t'],
            'is_closed': kline['x']
        }
        
        if symbol not in market_data:
            market_data[symbol] = {}
        if timeframe not in market_data[symbol]:
            market_data[symbol][timeframe] = []
            
        candles = market_data[symbol][timeframe]
        
        if candles and not candle['is_closed']:
            candles[-1] = candle
        elif candle['is_closed']:
            candles.append(candle)
            # Сохраняем только последние 500 свечей
            market_data[symbol][timeframe] = candles[-500:]
            bot_status['data_received'] = bot_status.get('data_received', 0) + 1
    except Exception as e:
        logger.error("Error processing kline: %s", str(e))

async def start_websocket_connections():
    global websocket_tasks
    for symbol in TRADING_PAIRS:
        for timeframe in TIMEFRAMES:
            task = asyncio.create_task(binance_websocket(symbol, timeframe))
            websocket_tasks.append(task)
            await asyncio.sleep(0.1)

async def stop_websocket_connections():
    global websocket_tasks
    for task in websocket_tasks:
        task.cancel()
    websocket_tasks = []
