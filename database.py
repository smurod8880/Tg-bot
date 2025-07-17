import sqlite3
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)
DB_PATH = 'data/trading_bot.db'

def get_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    return sqlite3.connect(DB_PATH)

def init_database():
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS signals (
                    id TEXT PRIMARY KEY,
                    symbol TEXT,
                    timeframe TEXT,
                    signal_type TEXT,
                    strength REAL,
                    accuracy REAL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    indicators TEXT,
                    profitable INTEGER DEFAULT NULL
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS indicator_weights (
                    indicator TEXT PRIMARY KEY,
                    weight REAL
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS performance (
                    indicator TEXT PRIMARY KEY,
                    success INTEGER DEFAULT 0,
                    total INTEGER DEFAULT 0
                )
            ''')
            conn.commit()
        logger.info("Database initialized")
    except Exception as e:
        logger.error("Database init error: %s", str(e))

def store_signal(signal_id, symbol, timeframe, signal_type, strength, accuracy, indicators):
    try:
        with get_connection() as conn:
            conn.execute('''
                INSERT INTO signals (id, symbol, timeframe, signal_type, strength, accuracy, indicators)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (signal_id, symbol, timeframe, signal_type, strength, accuracy, ','.join(indicators)))
            conn.commit()
        logger.info("Signal stored: %s", signal_id)
    except Exception as e:
        logger.error("Store signal error: %s", str(e))

def update_signal_result(signal_id, profitable):
    try:
        with get_connection() as conn:
            conn.execute('''
                UPDATE signals SET profitable = ? WHERE id = ?
            ''', (1 if profitable else 0, signal_id))
            conn.commit()
        logger.info("Signal result updated: %s -> %s", signal_id, profitable)
    except Exception as e:
        logger.error("Update signal error: %s", str(e))

def save_weights(weights):
    try:
        with get_connection() as conn:
            for indicator, weight in weights.items():
                conn.execute('''
                    INSERT OR REPLACE INTO indicator_weights (indicator, weight)
                    VALUES (?, ?)
                ''', (indicator, weight))
            conn.commit()
        logger.info("Weights saved: %d indicators", len(weights))
    except Exception as e:
        logger.error("Save weights error: %s", str(e))

def load_weights():
    if not os.path.exists(DB_PATH):
        return {}
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT indicator, weight FROM indicator_weights')
            weights = {row[0]: row[1] for row in cursor.fetchall()}
            logger.info("Loaded %d weights from database", len(weights))
            return weights
    except Exception as e:
        logger.error("Load weights error: %s", str(e))
        return {}
