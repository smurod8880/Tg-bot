import sqlite3
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def init_database():
    db_path = 'data/trading_bot.db'
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Таблица сигналов
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
    
    # Таблица весов индикаторов
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS indicator_weights (
            indicator TEXT PRIMARY KEY,
            weight REAL
        )
    ''')
    
    # Таблица производительности
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS performance (
            indicator TEXT PRIMARY KEY,
            success INTEGER DEFAULT 0,
            total INTEGER DEFAULT 0
        )
    ''')
    
    conn.commit()
    conn.close()
    logger.info("Database initialized")

def store_signal(signal_id, symbol, timeframe, signal_type, strength, accuracy, indicators):
    db_path = 'data/trading_bot.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO signals (id, symbol, timeframe, signal_type, strength, accuracy, indicators)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (signal_id, symbol, timeframe, signal_type, strength, accuracy, ','.join(indicators)))
    conn.commit()
    conn.close()

def update_signal_result(signal_id, profitable):
    db_path = 'data/trading_bot.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE signals SET profitable = ? WHERE id = ?
    ''', (1 if profitable else 0, signal_id))
    conn.commit()
    conn.close()

def save_weights(weights):
    db_path = 'data/trading_bot.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    for indicator, weight in weights.items():
        cursor.execute('''
            INSERT OR REPLACE INTO indicator_weights (indicator, weight)
            VALUES (?, ?)
        ''', (indicator, weight))
    
    conn.commit()
    conn.close()

def load_weights():
    db_path = 'data/trading_bot.db'
    if not os.path.exists(db_path):
        return None
        
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT indicator, weight FROM indicator_weights')
    weights = {row[0]: row[1] for row in cursor.fetchall()}
    conn.close()
    return weights
