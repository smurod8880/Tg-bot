import pandas as pd
import pandas_ta as ta
import numpy as np
import logging

logger = logging.getLogger(__name__)

class TechnicalIndicators:
    @staticmethod
    def calculate_all_indicators(df):
        try:
            # Трендовые
            df['EMA_12'] = ta.ema(df['close'], length=12)
            df['EMA_26'] = ta.ema(df['close'], length=26)
            df['SMA_20'] = ta.sma(df['close'], length=20)
            
            macd = ta.macd(df['close'], fast=12, slow=26, signal=9)
            df['MACD'] = macd['MACD_12_26_9']
            df['MACD_signal'] = macd['MACDs_12_26_9']
            
            df['ADX'] = ta.adx(df['high'], df['low'], df['close'])['ADX_14']
            
            supertrend = ta.supertrend(df['high'], df['low'], df['close'], length=10, multiplier=3)
            df['Supertrend'] = supertrend['SUPERT_10_3.0']  # 1 - восходящий, -1 - нисходящий
            
            # Осцилляторы
            df['RSI'] = ta.rsi(df['close'], length=14)
            df['CCI'] = ta.cci(df['high'], df['low'], df['close'], length=20)
            
            stoch = ta.stoch(df['high'], df['low'], df['close'], k=14, d=3)
            df['Stoch_k'] = stoch['STOCHk_14_3_3']
            df['Stoch_d'] = stoch['STOCHd_14_3_3']
            
            df['Williams'] = ta.willr(df['high'], df['low'], df['close'], length=14)
            
            # Волатильность
            df['ATR'] = ta.atr(df['high'], df['low'], df['close'], length=14)
            
            bb = ta.bbands(df['close'], length=20, std=2)
            df['BB_upper'] = bb['BBU_20_2.0']
            df['BB_middle'] = bb['BBM_20_2.0']
            df['BB_lower'] = bb['BBL_20_2.0']
            
            kc = ta.kc(df['high'], df['low'], df['close'], length=20, scalar=2)
            df['KC_upper'] = kc['KCUe_20_2']
            df['KC_middle'] = kc['KCLe_20_2']
            df['KC_lower'] = kc['KCLe_20_2']
            
            # Объем
            df['OBV'] = ta.obv(df['close'], df['volume'])
            df['OBV_trend'] = ta.ema(df['OBV'], length=20) - ta.ema(df['OBV'], length=50)
            
            pvo = ta.pvo(df['volume'])
            df['Volume_Osc'] = pvo['PVO_12_26_9']
            
            # Свечные модели
            df['Bullish_Engulfing'] = ta.cdl_pattern(df['open'], df['high'], df['low'], df['close'], "engulfing") == 100
            df['Bearish_Engulfing'] = ta.cdl_pattern(df['open'], df['high'], df['low'], df['close'], "engulfing") == -100
            df['Hammer'] = ta.cdl_pattern(df['open'], df['high'], df['low'], df['close'], "hammer") == 100
            df['Pin_Bar_bull'] = ta.cdl_pattern(df['open'], df['high'], df['low'], df['close'], "piercing") == 100
            df['Pin_Bar_bear'] = ta.cdl_pattern(df['open'], df['high'], df['low'], df['close'], "piercing") == -100
            
            return df.dropna()
        except Exception as e:
            logger.error(f"Error calculating indicators: {e}")
            return df
