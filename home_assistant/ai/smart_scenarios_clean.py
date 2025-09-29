"""
AI-powered Smart Scenarios система для автоматического создания и оптимизации сценариев.

Анализирует паттерны поведения пользователя и автоматически предлагает умные сценарии.
"""

import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import numpy as np
from dataclasses import dataclass
from enum import Enum


class ScenarioType(Enum):
    TIME_BASED = "time_based"
    CONDITION_BASED = "condition_based"
    PATTERN_BASED = "pattern_based"
    ENERGY_OPTIMIZATION = "energy_optimization"
    SECURITY = "security"
    COMFORT = "comfort"


@dataclass
class PatternData:
    """Данные о паттерне поведения."""
    timestamp: datetime
    device_id: str
    action: str
    room: str
    trigger_type: str  # manual, schedule, sensor
    context: Dict[str, Any]  # время суток, день недели, погода и т.д.


@dataclass
class SmartScenario:
    """Умный сценарий, созданный AI."""
    id: str
    name: str
    description: str
    scenario_type: ScenarioType
    trigger_conditions: List[Dict[str, Any]]
    actions: List[Dict[str, Any]]
    confidence: float  # Уверенность AI в полезности сценария
    frequency: int  # Сколько раз паттерн повторялся
    energy_impact: float  # Влияние на энергопотребление (положительное = экономия)
    comfort_score: float  # Оценка комфорта (0-1)
    created_at: datetime
    last_triggered: Optional[datetime] = None
    success_rate: float = 0.0  # Процент успешных выполнений


class SmartScenariosAI:
    """AI система для создания умных сценариев."""
    
    def __init__(self, db_manager, reasoning_engine):
        self.db_manager = db_manager
        self.reasoning_engine = reasoning_engine
        self.pattern_buffer = []
        self.learned_scenarios = {}
        self.min_pattern_frequency = 3  # Минимальное количество повторений для создания сценария
        
    async def analyze_user_patterns(self, days_back: int = 30) -> List[PatternData]:
        """Анализ паттернов поведения пользователя за последние дни."""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)
            
            # Получение логов устройств за период (симуляция)
            patterns = []
            
            # Симуляция типичных паттернов пользователя
            for i in range(60):  # 60 записей за месяц
                timestamp = start_date + timedelta(days=i % 30, hours=(i % 24))
                
                context = {
                    'hour': timestamp.hour,
                    'day_of_week': timestamp.weekday(),
                    'is_weekend': timestamp.weekday() >= 5,
                    'time_of_day': self._get_time_of_day(timestamp.hour),
                    'season': self._get_season(timestamp)
                }
                
                # Утренние паттерны
                if 6 <= timestamp.hour <= 8:
                    pattern = PatternData(
                        timestamp=timestamp,
                        device_id='bedroom_lights',
                        action='turn_on',
                        room='bedroom',
                        trigger_type='manual',
                        context=context
                    )
                    patterns.append(pattern)
                
                # Вечерние паттерны
                elif 19 <= timestamp.hour <= 22:
                    pattern = PatternData(
                        timestamp=timestamp,
                        device_id='living_room_lights',
                        action='turn_on',
                        room='living_room',
                        trigger_type='manual',
                        context=context
                    )
                    patterns.append(pattern)
            
            return patterns
            
        except Exception as e:
            print(f"Error analyzing patterns: {e}")
            return []
    
    def _get_time_of_day(self, hour: int) -> str:
        """Определение времени суток."""
        if 5 <= hour < 12:
            return 'morning'
        elif 12 <= hour < 17:
            return 'afternoon'
        elif 17 <= hour < 22:
            return 'evening'
        else:
            return 'night'
    
    def _get_season(self, timestamp: datetime) -> str:
        """Определение сезона."""
        month = timestamp.month
        if month in [12, 1, 2]:
            return 'winter'
        elif month in [3, 4, 5]:
            return 'spring'
        elif month in [6, 7, 8]:
            return 'summer'
        else:
            return 'autumn'
    
    async def detect_behavioral_patterns(self, patterns: List[PatternData]) -> List[Dict[str, Any]]:
        """Обнаружение повторяющихся паттернов поведения."""
        if not patterns:
            return []
        
        # Группировка паттернов по временным интервалам и действиям
        pattern_groups = {}
        
        for pattern in patterns:
            # Создание ключа для группировки (час + день недели + действие)
            key = f"{pattern.context['hour']}_{pattern.context['day_of_week']}_{pattern.device_id}_{pattern.action}"
            
            if key not in pattern_groups:
                pattern_groups[key] = []
            pattern_groups[key].append(pattern)
        
        # Анализ часто повторяющихся паттернов
        frequent_patterns = []
        for key, group in pattern_groups.items():
            if len(group) >= self.min_pattern_frequency:
                # Вычисление статистики паттерна
                time_variance = self._calculate_time_variance(group)
                context_similarity = self._calculate_context_similarity(group)
                
                pattern_info = {
                    'pattern_key': key,
                    'frequency': len(group),
                    'first_occurrence': min(p.timestamp for p in group),
                    'last_occurrence': max(p.timestamp for p in group),
                    'time_variance': time_variance,
                    'context_similarity': context_similarity,
                    'actions': [p.action for p in group],
                    'devices': [p.device_id for p in group],
                    'rooms': [p.room for p in group],
                    'sample_context': group[0].context
                }
                frequent_patterns.append(pattern_info)
        
        return frequent_patterns
    
    def _calculate_time_variance(self, patterns: List[PatternData]) -> float:
        """Вычисление разброса времени выполнения действий."""
        if len(patterns) < 2:
            return 0.0
            
        times = [p.timestamp.hour * 60 + p.timestamp.minute for p in patterns]
        return np.std(times) / 60.0  # Возвращаем в часах
    
    def _calculate_context_similarity(self, patterns: List[PatternData]) -> float:
        """Вычисление схожести контекста выполнения."""
        if len(patterns) < 2:
            return 1.0
        
        # Проверяем схожесть дня недели, времени суток
        same_day_type = sum(1 for p in patterns if p.context['is_weekend'] == patterns[0].context['is_weekend'])
        same_time_of_day = sum(1 for p in patterns if p.context['time_of_day'] == patterns[0].context['time_of_day'])
        
        return (same_day_type + same_time_of_day) / (2 * len(patterns))
    
    async def create_smart_scenarios(self, behavioral_patterns: List[Dict[str, Any]]) -> List[SmartScenario]:
        """Создание умных сценариев на основе обнаруженных паттернов."""
        smart_scenarios = []
        
        for pattern in behavioral_patterns:
            # Фильтруем только стабильные паттерны
            if pattern['frequency'] >= self.min_pattern_frequency and pattern['time_variance'] <= 2.0:
                scenarios = await self._generate_scenarios_from_pattern(pattern)
                smart_scenarios.extend(scenarios)
        
        # Группировка связанных сценариев
        grouped_scenarios = await self._group_related_scenarios(smart_scenarios)
        
        # Оптимизация сценариев
        optimized_scenarios = await self._optimize_scenarios(grouped_scenarios)
        
        return optimized_scenarios
    
    async def _generate_scenarios_from_pattern(self, pattern: Dict[str, Any]) -> List[SmartScenario]:
        """Генерация сценариев из одного паттерна."""
        scenarios = []
        
        # Анализ типа паттерна
        sample_context = pattern['sample_context']
        time_of_day = sample_context['time_of_day']
        frequency = pattern['frequency']
        
        # Создание временного сценария
        if time_of_day in ['morning', 'evening']:
            scenario = await self._create_routine_scenario(pattern, time_of_day)
            if scenario:
                scenarios.append(scenario)
        
        # Создание энергосберегающего сценария
        energy_scenario = await self._create_energy_saving_scenario(pattern)
        if energy_scenario:
            scenarios.append(energy_scenario)
        
        return scenarios
    
    async def _create_routine_scenario(self, pattern: Dict[str, Any], time_of_day: str) -> Optional[SmartScenario]:
        """Создание рутинного сценария (утро/вечер)."""
        try:
            context = pattern['sample_context']
            devices = pattern['devices']
            actions = pattern['actions']
            
            # Определение времени запуска
            avg_hour = context['hour']
            
            # Создание условий триггера
            trigger_conditions = [{
                "type": "time",
                "value": f"{avg_hour:02d}:00",
                "days": self._get_days_from_pattern(pattern)
            }]
            
            # Создание действий
            scenario_actions = []
            for i, (device, action) in enumerate(zip(devices, actions)):
                scenario_actions.append({
                    "device_id": device,
                    "action": action,
                    "delay": i * 2,  # Задержка между действиями
                    "priority": 1
                })
            
            # Добавление связанных действий
            related_actions = await self._suggest_related_actions(devices, time_of_day)
            scenario_actions.extend(related_actions)
            
            scenario_id = f"routine_{time_of_day}_{abs(hash(str(pattern)))}"
            
            return SmartScenario(
                id=scenario_id,
                name=f"{time_of_day.capitalize()} Routine",
                description=f"Automated {time_of_day} routine based on your usage patterns",
                scenario_type=ScenarioType.PATTERN_BASED,
                trigger_conditions=trigger_conditions,
                actions=scenario_actions,
                confidence=min(0.9, pattern['frequency'] / 10.0),
                frequency=pattern['frequency'],
                energy_impact=await self._estimate_energy_impact(scenario_actions),
                comfort_score=await self._estimate_comfort_score(scenario_actions, time_of_day),
                created_at=datetime.now()
            )
            
        except Exception as e:
            print(f"Error creating routine scenario: {e}")
            return None
    
    async def _create_energy_saving_scenario(self, pattern: Dict[str, Any]) -> Optional[SmartScenario]:
        """Создание энергосберегающего сценария."""
        try:
            # Анализ устройств, которые часто остаются включенными
            devices = pattern['devices']
            actions = pattern['actions']
            
            # Создание сценария для автоматического выключения
            if any('turn_on' in action for action in actions):
                scenario_actions = []
                
                # Добавление действий выключения с задержкой
                for device in devices:
                    scenario_actions.append({
                        "device_id": device,
                        "action": "turn_off",
                        "condition": "no_motion_detected",
                        "delay": 1800,  # 30 минут
                        "priority": 2
                    })
                
                trigger_conditions = [{
                    "type": "no_activity",
                    "duration": 30,  # 30 минут
                    "rooms": list(set(pattern.get('rooms', [])))
                }]
                
                scenario_id = f"energy_saving_{abs(hash(str(pattern)))}"
                
                return SmartScenario(
                    id=scenario_id,
                    name="Smart Energy Saving",
                    description="Automatically turn off devices when no activity detected",
                    scenario_type=ScenarioType.ENERGY_OPTIMIZATION,
                    trigger_conditions=trigger_conditions,
                    actions=scenario_actions,
                    confidence=0.7,
                    frequency=pattern['frequency'],
                    energy_impact=15.0,  # Примерная экономия в процентах
                    comfort_score=0.8,
                    created_at=datetime.now()
                )
            
            return None
            
        except Exception as e:
            print(f"Error creating energy saving scenario: {e}")
            return None
    
    def _get_days_from_pattern(self, pattern: Dict[str, Any]) -> List[str]:
        """Определение дней недели для сценария."""
        context = pattern['sample_context']
        if context['is_weekend']:
            return ['saturday', 'sunday']
        else:
            return ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']
    
    async def _suggest_related_actions(self, devices: List[str], time_of_day: str) -> List[Dict[str, Any]]:
        """Предложение связанных действий для улучшения сценария."""
        related_actions = []
        
        if time_of_day == 'morning':
            # Утренние дополнительные действия
            if 'coffee_maker' not in devices:
                related_actions.append({
                    "device_id": "coffee_maker",
                    "action": "start_brewing",
                    "delay": 5,
                    "priority": 3,
                    "suggested": True
                })
            
            if 'thermostat' not in devices:
                related_actions.append({
                    "device_id": "thermostat",
                    "action": "set_temperature",
                    "params": {"temperature": 21},
                    "delay": 0,
                    "priority": 2,
                    "suggested": True
                })
        
        elif time_of_day == 'evening':
            # Вечерние дополнительные действия
            if any('light' in device for device in devices):
                related_actions.append({
                    "device_id": "outdoor_lights",
                    "action": "turn_on",
                    "delay": 30,
                    "priority": 3,
                    "suggested": True
                })
        
        return related_actions
    
    async def _estimate_energy_impact(self, actions: List[Dict[str, Any]]) -> float:
        """Оценка влияния сценария на энергопотребление."""
        # Простая эвристика для оценки энергетического воздействия
        impact = 0.0
        
        for action in actions:
            action_type = action.get('action', '')
            if 'turn_off' in action_type:
                impact += 5.0  # Экономия
            elif 'turn_on' in action_type:
                impact -= 2.0  # Потребление
            elif 'dim' in action_type or 'brightness' in action_type:
                impact += 1.0  # Небольшая экономия
        
        return impact
    
    async def _estimate_comfort_score(self, actions: List[Dict[str, Any]], time_of_day: str) -> float:
        """Оценка влияния сценария на комфорт."""
        score = 0.5  # Базовый уровень
        
        # Бонусы за полезные действия
        action_types = [action.get('action', '') for action in actions]
        
        if 'gradual' in ' '.join(action_types):
            score += 0.2  # Плавные переходы повышают комфорт
        
        if time_of_day == 'morning' and any('coffee' in action.get('device_id', '') for action in actions):
            score += 0.15  # Утренний кофе
        
        if len(actions) > 1:
            score += 0.1  # Комплексные сценарии
        
        return min(1.0, score)
    
    async def _group_related_scenarios(self, scenarios: List[SmartScenario]) -> List[SmartScenario]:
        """Группировка связанных сценариев для избежания дублирования."""
        if not scenarios:
            return scenarios
        
        # Группировка по времени и типу
        grouped = {}
        for scenario in scenarios:
            key = f"{scenario.scenario_type.value}_{scenario.trigger_conditions[0].get('value', 'none')}"
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(scenario)
        
        # Выбор лучшего сценария из каждой группы
        best_scenarios = []
        for group in grouped.values():
            if len(group) == 1:
                best_scenarios.append(group[0])
            else:
                # Выбираем сценарий с максимальной уверенностью
                best = max(group, key=lambda s: s.confidence * s.frequency)
                best_scenarios.append(best)
        
        return best_scenarios
    
    async def _optimize_scenarios(self, scenarios: List[SmartScenario]) -> List[SmartScenario]:
        """Оптимизация сценариев для повышения эффективности."""
        optimized = []
        
        for scenario in scenarios:
            # Оптимизация действий
            optimized_actions = await self._optimize_actions(scenario.actions)
            
            # Создание оптимизированного сценария
            optimized_scenario = SmartScenario(
                id=scenario.id,
                name=scenario.name,
                description=scenario.description,
                scenario_type=scenario.scenario_type,
                trigger_conditions=scenario.trigger_conditions,
                actions=optimized_actions,
                confidence=scenario.confidence,
                frequency=scenario.frequency,
                energy_impact=scenario.energy_impact,
                comfort_score=scenario.comfort_score,
                created_at=scenario.created_at
            )
            
            optimized.append(optimized_scenario)
        
        return optimized
    
    async def _optimize_actions(self, actions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Оптимизация последовательности действий."""
        if not actions:
            return actions
        
        # Сортировка по приоритету
        sorted_actions = sorted(actions, key=lambda a: a.get('priority', 5))
        
        # Оптимизация задержек
        optimized = []
        current_delay = 0
        
        for action in sorted_actions:
            optimized_action = action.copy()
            optimized_action['delay'] = current_delay
            optimized.append(optimized_action)
            
            # Увеличиваем задержку для следующего действия
            current_delay += action.get('delay', 2)
        
        return optimized
    
    async def suggest_scenario_improvements(self, scenario_id: str, usage_stats: Dict[str, Any]) -> List[str]:
        """Предложение улучшений для существующего сценария."""
        suggestions = []
        
        success_rate = usage_stats.get('success_rate', 0.0)
        user_feedback = usage_stats.get('user_feedback', {})
        
        if success_rate < 0.7:
            suggestions.append("Consider adjusting trigger conditions - low success rate detected")
        
        if user_feedback.get('too_early', 0) > user_feedback.get('too_late', 0):
            suggestions.append("Scenario might be triggering too early - consider delaying by 15-30 minutes")
        elif user_feedback.get('too_late', 0) > user_feedback.get('too_early', 0):
            suggestions.append("Scenario might be triggering too late - consider advancing by 15-30 minutes")
        
        energy_usage = usage_stats.get('energy_usage', 0)
        if energy_usage > 20:  # Высокое потребление
            suggestions.append("High energy usage detected - consider adding energy-saving actions")
        
        return suggestions
    
    async def generate_voice_activated_scenarios(self, voice_commands: List[str]) -> List[SmartScenario]:
        """Создание сценариев на основе голосовых команд."""
        scenarios = []
        
        # Анализ частых голосовых команд
        command_analysis = await self._analyze_voice_commands(voice_commands)
        
        for command_pattern in command_analysis:
            if command_pattern['frequency'] >= 3:
                scenario = await self._create_voice_scenario(command_pattern)
                if scenario:
                    scenarios.append(scenario)
        
        return scenarios
    
    async def _analyze_voice_commands(self, commands: List[str]) -> List[Dict[str, Any]]:
        """Анализ голосовых команд для поиска паттернов."""
        # Простой анализ частоты команд
        command_freq = {}
        for command in commands:
            normalized = command.lower().strip()
            command_freq[normalized] = command_freq.get(normalized, 0) + 1
        
        # Возвращаем команды с частотой больше 1
        patterns = [
            {'command': cmd, 'frequency': freq}
            for cmd, freq in command_freq.items() if freq > 1
        ]
        
        return sorted(patterns, key=lambda x: x['frequency'], reverse=True)
    
    async def _create_voice_scenario(self, command_pattern: Dict[str, Any]) -> Optional[SmartScenario]:
        """Создание сценария на основе голосовой команды."""
        try:
            command = command_pattern['command']
            frequency = command_pattern['frequency']
            
            # Анализ команды для извлечения действий
            if 'включи' in command or 'turn on' in command:
                if 'свет' in command or 'light' in command:
                    actions = [{
                        "device_id": "living_room_lights",
                        "action": "turn_on",
                        "priority": 1
                    }]
                elif 'музыку' in command or 'music' in command:
                    actions = [{
                        "device_id": "spotify",
                        "action": "play",
                        "priority": 1
                    }]
                else:
                    return None
                
                scenario_id = f"voice_command_{abs(hash(command))}"
                
                return SmartScenario(
                    id=scenario_id,
                    name=f"Voice Command: {command.title()}",
                    description=f"Execute frequent voice command: '{command}'",
                    scenario_type=ScenarioType.PATTERN_BASED,
                    trigger_conditions=[{
                        "type": "voice_command",
                        "phrase": command,
                        "similarity_threshold": 0.8
                    }],
                    actions=actions,
                    confidence=min(0.9, frequency / 10.0),
                    frequency=frequency,
                    energy_impact=0.0,
                    comfort_score=0.8,
                    created_at=datetime.now()
                )
            
            return None
            
        except Exception as e:
            print(f"Error creating voice scenario: {e}")
            return None