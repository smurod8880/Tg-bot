import logging
import json
import os
import numpy as np
from globals import indicator_weights

logger = logging.getLogger(__name__)

PERFORMANCE_FILE = 'data/performance.json'

class LearningSystem:
    performance_data = {}
    learning_rate = 0.01  # Скорость обучения
    
    @classmethod
    def initialize(cls):
        """Загрузка данных о производительности"""
        try:
            if os.path.exists(PERFORMANCE_FILE):
                with open(PERFORMANCE_FILE, 'r') as f:
                    cls.performance_data = json.load(f)
                logger.info("Performance data loaded")
        except Exception as e:
            logger.error(f"Error loading performance data: {e}")
    
    @classmethod
    def save_performance(cls):
        """Сохранение данных о производительности"""
        try:
            with open(PERFORMANCE_FILE, 'w') as f:
                json.dump(cls.performance_data, f)
            logger.info("Performance data saved")
        except Exception as e:
            logger.error(f"Error saving performance data: {e}")
    
    @classmethod
    def update_weights(cls, signal_result):
        """Адаптация весов на основе результата сигнала"""
        try:
            if not signal_result['indicators']:
                return
                
            # Обновляем статистику
            for indicator in signal_result['indicators']:
                if indicator not in cls.performance_data:
                    cls.performance_data[indicator] = {'success': 0, 'total': 0}
                
                cls.performance_data[indicator]['total'] += 1
                if signal_result['profitable']:
                    cls.performance_data[indicator]['success'] += 1
            
            # Адаптация весов
            for indicator, data in cls.performance_data.items():
                if data['total'] > 10:  # Минимум 10 сигналов для адаптации
                    success_rate = data['success'] / data['total']
                    current_weight = indicator_weights.get(indicator, 0)
                    
                    # Увеличиваем вес успешных индикаторов
                    if success_rate > 0.6:
                        new_weight = current_weight * (1 + cls.learning_rate)
                    # Уменьшаем вес неуспешных
                    elif success_rate < 0.4:
                        new_weight = current_weight * (1 - cls.learning_rate)
                    else:
                        new_weight = current_weight
                    
                    # Ограничиваем диапазон весов
                    new_weight = max(0.02, min(0.15, new_weight))
                    indicator_weights[indicator] = new_weight
            
            cls.save_performance()
            return True
        except Exception as e:
            logger.error(f"Error updating weights: {e}")
            return False
    
    @classmethod
    def get_performance_report(cls):
        """Отчет о производительности индикаторов"""
        report = []
        for indicator, data in cls.performance_data.items():
            if data['total'] > 0:
                success_rate = data['success'] / data['total']
                report.append({
                    'indicator': indicator,
                    'success_rate': success_rate,
                    'weight': indicator_weights.get(indicator, 0)
                })
        return sorted(report, key=lambda x: x['success_rate'], reverse=True)
