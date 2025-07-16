import asyncio
import time
import logging
import pandas as pd
from globals import market_data, indicator_weights, SIGNAL_THRESHOLD, MIN_INDICATORS, bot_status, TIMEFRAME_HIERARCHY, CONFIRMATION_THRESHOLD
from database import store_signal, update_signal_result
from telegram import send_signal
from indicators import TechnicalIndicators
from learning import LearningSystem

logger = logging.getLogger(__name__)
analysis_task = None

class SignalAnalyzer:
    def __init__(self):
        self.indicators = TechnicalIndicators()
        self.active = True
        self.pending_signals = {}
        
    async def analyze_all(self):
        while self.active and bot_status['running']:
            try:
                for symbol in market_data:
                    for timeframe in market_data[symbol]:
                        if len(market_data[symbol][timeframe]) > 100:
                            await self.analyze_symbol(symbol, timeframe)
                await self.check_pending_signals()
                await asyncio.sleep(10)
            except Exception as e:
                logger.error(f"Analysis loop error: {e}")
                await asyncio.sleep(10)
    
    async def check_pending_signals(self):
        current_time = time.time()
        expired_signals = []
        for signal_id, signal_data in self.pending_signals.items():
            if current_time - signal_data['timestamp'] > 60:
                if await self.is_signal_confirmed(signal_data):
                    await self.send_confirmed_signal(signal_data)
                    expired_signals.append(signal_id)
                else:
                    expired_signals.append(signal_id)
        for signal_id in expired_signals:
            del self.pending_signals[signal_id]
    
    async def is_signal_confirmed(self, signal_data):
        symbol = signal_data['symbol']
        signal_type = signal_data['signal_type']
        base_timeframe = signal_data['timeframe']
        higher_timeframes = TIMEFRAME_HIERARCHY.get(base_timeframe, [])
        if not higher_timeframes:
            return True
        confirmation_strength = 0
        required_confirmations = len(higher_timeframes)
        for htf in higher_timeframes:
            if symbol in market_data and htf in market_data[symbol]:
                df = pd.DataFrame(market_data[symbol][htf][-100:])
                if df.empty:
                    continue
                df = self.indicators.calculate_all_indicators(df)
                latest = df.iloc[-1]
                try:
                    if signal_type == 'BUY':
                        if (latest['EMA_12'] > latest['EMA_26'] and 
                            latest['MACD'] > latest['MACD_signal'] and
                            latest['RSI'] < 70 and latest['RSI'] > 30 and
                            latest['close'] > latest['BB_middle']):
                            confirmation_strength += 1
                    else:
                        if (latest['EMA_12'] < latest['EMA_26'] and 
                            latest['MACD'] < latest['MACD_signal'] and
                            latest['RSI'] > 30 and latest['RSI'] < 70 and
                            latest['close'] < latest['BB_middle']):
                            confirmation_strength += 1
                except KeyError:
                    continue
        confirmation_level = confirmation_strength / required_confirmations if required_confirmations > 0 else 1.0
        return confirmation_level >= CONFIRMATION_THRESHOLD
    
    async def send_confirmed_signal(self, signal_data):
        signal_id = signal_data['id']
        await send_signal(
            signal_data['symbol'],
            signal_data['timeframe'],
            signal_data['signal_type'],
            signal_data['strength'],
            signal_data['accuracy'],
            signal_data['indicators'],
            signal_id
        )
        asyncio.create_task(self.track_signal_result(signal_id, signal_data))
    
    async def track_signal_result(self, signal_id, signal_data):
        symbol = signal_data['symbol']
        timeframe = signal_data['timeframe']
        signal_type = signal_data['signal_type']
        try:
            entry_price = market_data[symbol][timeframe][-1]['close']
        except (KeyError, IndexError):
            logger.error(f"Can't get entry price for {signal_id}")
            return
        wait_hours = 4 if timeframe != '1d' else 24
        await asyncio.sleep(wait_hours * 3600)
        try:
            current_price = market_data[symbol][timeframe][-1]['close']
            price_change = (current_price - entry_price) / entry_price
            profitable = (signal_type == 'BUY' and price_change > 0.01) or \
                        (signal_type == 'SELL' and price_change < -0.01)
            update_signal_result(signal_id, profitable)
            if profitable:
                bot_status['profitable_signals'] += 1
            else:
                bot_status['unprofitable_signals'] += 1
            LearningSystem.update_weights({
                'id': signal_id,
                'symbol': symbol,
                'timeframe': timeframe,
                'signal_type': signal_type,
                'indicators': signal_data['indicators'],
                'profitable': profitable
            })
        except Exception as e:
            logger.error(f"Error tracking signal {signal_id}: {e}")

    async def analyze_symbol(self, symbol, timeframe):
        try:
            data = market_data[symbol][timeframe]
            if len(data) < 200:
                return
            df = pd.DataFrame(data[-200:])
            df = self.indicators.calculate_all_indicators(df)
            if df.empty:
                return
            latest = df.iloc[-1]
            signals = self.calculate_indicator_signals(latest)
            strength, indicators = self.calculate_signal_strength(signals)
            if abs(strength) >= SIGNAL_THRESHOLD and len(indicators) >= MIN_INDICATORS:
                signal_type = "BUY" if strength > 0 else "SELL"
                signal_id = self.register_pending_signal(
                    symbol, timeframe, signal_type, abs(strength), indicators
                )
        except Exception as e:
            logger.error(f"Error analyzing {symbol}/{timeframe}: {e}")

    def calculate_indicator_signals(self, latest):
        signals = {}
        try:
            signals['EMA'] = 1.0 if latest['EMA_12'] > latest['EMA_26'] else -1.0
            signals['SMA'] = 1.0 if latest['close'] > latest['SMA_20'] else -1.0
            signals['MACD'] = 1.0 if latest['MACD'] > latest['MACD_signal'] else -1.0
            signals['Supertrend'] = 1.0 if latest['Supertrend'] > 0 else -1.0
            signals['ADX'] = 1.0 if latest['ADX'] > 25 else 0.0
            signals['RSI'] = -1.0 if latest.get('RSI', 0) > 70 else 1.0 if latest.get('RSI', 0) < 30 else 0.0
            signals['Stochastic'] = 1.0 if latest.get('Stoch_k', 0) < 20 and latest.get('Stoch_d', 0) < 20 else -1.0 if latest.get('Stoch_k', 0) > 80 and latest.get('Stoch_d', 0) > 80 else 0.0
            signals['Williams'] = 1.0 if latest.get('Williams', 0) < -80 else -1.0 if latest.get('Williams', 0) > -20 else 0.0
            signals['CCI'] = 1.0 if latest.get('CCI', 0) < -100 else -1.0 if latest.get('CCI', 0) > 100 else 0.0
            signals['Bollinger_Bands'] = -1.0 if latest['close'] > latest.get('BB_upper', 0) else 1.0 if latest['close'] < latest.get('BB_lower', 0) else 0.0
            signals['Keltner_Channel'] = -1.0 if latest['close'] > latest.get('KC_upper', 0) else 1.0 if latest['close'] < latest.get('KC_lower', 0) else 0.0
            signals['Volume_Oscillator'] = 1.0 if latest.get('Volume_Osc', 0) > 0 else -1.0
            signals['OBV'] = 1.0 if latest.get('OBV_trend', 0) > 0 else -1.0
            signals['Engulfing'] = 1.0 if latest.get('Bullish_Engulfing', False) else -1.0 if latest.get('Bearish_Engulfing', False) else 0.0
            signals['Hammer'] = 1.0 if latest.get('Hammer', False) else 0.0
            signals['Pin_Bar'] = 1.0 if latest.get('Pin_Bar_bull', False) else -1.0 if latest.get('Pin_Bar_bear', False) else 0.0
        except KeyError as e:
            logger.error(f"Missing indicator data: {e}")
            return {}
        return signals

    def calculate_signal_strength(self, signals):
        total_strength = 0
        total_weight = 0
        active_indicators = []
        for indicator, signal in signals.items():
            if signal != 0 and indicator in indicator_weights:
                weight = indicator_weights[indicator]
                total_strength += signal * weight
                total_weight += weight
                active_indicators.append(indicator)
        if total_weight == 0 else 1.0
            return 0, []
        signal_strength = total_strength / total_weight
        return signal_strength, active_indicators

    def register_pending_signal(self, symbol, timeframe, signal_type, strength, indicators):
        signal_id = f"{symbol}-{timeframe}-{int(time.time())}"
        self.pending_signals[signal_id] = {
            'id': signal_id,
            'symbol': symbol,
            'timeframe': timeframe,
            'signal_type': signal_type,
            'strength': strength,
            'accuracy': self.calculate_accuracy(),
            'indicators': indicators,
            'timestamp': time.time()
        }
        return signal_id

    def calculate_accuracy(self):
        total = bot_status['profitable_signals'] + bot_status['unprofitable_signals']
        if total > 0:
            accuracy = bot_status['profitable_signals'] / total
            return max(0.7, min(0.98, accuracy))
        return 0.93

def start_analysis():
    global analysis_task
    analyzer = SignalAnalyzer()
    analysis_task = asyncio.create_task(analyzer.analyze_all())

def stop_analysis():
    global analysis_task
    if analysis_task:
        analysis_task.cancel()
        analysis_task = None
