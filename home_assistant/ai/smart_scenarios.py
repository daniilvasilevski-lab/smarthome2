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

try:
    from sklearn.cluster import KMeans
    from sklearn.preprocessing import StandardScaler
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False


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
            
            # Получение логов устройств за период
            device_logs = await self.db_manager.get_device_logs_period(start_date, end_date)
            
            patterns = []
            for log in device_logs:
                # Извлечение контекста из времени
                timestamp = datetime.fromisoformat(log['timestamp'])
                context = {
                    'hour': timestamp.hour,
                    'day_of_week': timestamp.weekday(),
                    'is_weekend': timestamp.weekday() >= 5,
                    'time_of_day': self._get_time_of_day(timestamp.hour),
                    'season': self._get_season(timestamp)
                }
                
                pattern = PatternData(
                    timestamp=timestamp,
                    device_id=log['device_id'],
                    action=log['action'],
                    room=log.get('room', 'unknown'),
                    trigger_type=log.get('trigger_type', 'manual'),
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
        
        # Создание сценария комфорта
        comfort_scenario = await self._create_comfort_scenario(pattern)
        if comfort_scenario:
            scenarios.append(comfort_scenario)
        
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
            )\n            \n        except Exception as e:\n            print(f\"Error creating routine scenario: {e}\")\n            return None\n    \n    async def _create_energy_saving_scenario(self, pattern: Dict[str, Any]) -> Optional[SmartScenario]:\n        \"\"\"Создание энергосберегающего сценария.\"\"\"\n        try:\n            # Анализ устройств, которые часто остаются включенными\n            devices = pattern['devices']\n            actions = pattern['actions']\n            \n            # Создание сценария для автоматического выключения\n            if any('turn_on' in action for action in actions):\n                scenario_actions = []\n                \n                # Добавление действий выключения с задержкой\n                for device in devices:\n                    scenario_actions.append({\n                        \"device_id\": device,\n                        \"action\": \"turn_off\",\n                        \"condition\": \"no_motion_detected\",\n                        \"delay\": 1800,  # 30 минут\n                        \"priority\": 2\n                    })\n                \n                trigger_conditions = [{\n                    \"type\": \"no_activity\",\n                    \"duration\": 30,  # 30 минут\n                    \"rooms\": list(set(pattern.get('rooms', [])))\n                }]\n                \n                scenario_id = f\"energy_saving_{abs(hash(str(pattern)))}\"\n                \n                return SmartScenario(\n                    id=scenario_id,\n                    name=\"Smart Energy Saving\",\n                    description=\"Automatically turn off devices when no activity detected\",\n                    scenario_type=ScenarioType.ENERGY_OPTIMIZATION,\n                    trigger_conditions=trigger_conditions,\n                    actions=scenario_actions,\n                    confidence=0.7,\n                    frequency=pattern['frequency'],\n                    energy_impact=15.0,  # Примерная экономия в процентах\n                    comfort_score=0.8,\n                    created_at=datetime.now()\n                )\n            \n            return None\n            \n        except Exception as e:\n            print(f\"Error creating energy saving scenario: {e}\")\n            return None\n    \n    async def _create_comfort_scenario(self, pattern: Dict[str, Any]) -> Optional[SmartScenario]:\n        \"\"\"Создание сценария комфорта.\"\"\"\n        try:\n            context = pattern['sample_context']\n            time_of_day = context['time_of_day']\n            \n            # Сценарии комфорта в зависимости от времени\n            comfort_actions = []\n            \n            if time_of_day == 'evening':\n                # Вечерний комфорт: приглушенный свет, теплая атмосфера\n                comfort_actions = [\n                    {\n                        \"device_id\": \"living_room_lights\",\n                        \"action\": \"set_brightness\",\n                        \"params\": {\"brightness\": 30},\n                        \"priority\": 1\n                    },\n                    {\n                        \"device_id\": \"thermostat\",\n                        \"action\": \"set_temperature\",\n                        \"params\": {\"temperature\": 22},\n                        \"priority\": 2\n                    }\n                ]\n            elif time_of_day == 'morning':\n                # Утренний комфорт: постепенное увеличение света\n                comfort_actions = [\n                    {\n                        \"device_id\": \"bedroom_lights\",\n                        \"action\": \"gradual_on\",\n                        \"params\": {\"duration\": 300, \"final_brightness\": 80},\n                        \"priority\": 1\n                    }\n                ]\n            \n            if comfort_actions:\n                trigger_conditions = [{\n                    \"type\": \"presence_detected\",\n                    \"location\": pattern.get('rooms', ['living_room'])[0],\n                    \"time_range\": f\"{context['hour']-1}:00-{context['hour']+1}:00\"\n                }]\n                \n                scenario_id = f\"comfort_{time_of_day}_{abs(hash(str(pattern)))}\"\n                \n                return SmartScenario(\n                    id=scenario_id,\n                    name=f\"{time_of_day.capitalize()} Comfort\",\n                    description=f\"Optimize comfort settings for {time_of_day}\",\n                    scenario_type=ScenarioType.COMFORT,\n                    trigger_conditions=trigger_conditions,\n                    actions=comfort_actions,\n                    confidence=0.75,\n                    frequency=pattern['frequency'],\n                    energy_impact=0.0,\n                    comfort_score=0.9,\n                    created_at=datetime.now()\n                )\n            \n            return None\n            \n        except Exception as e:\n            print(f\"Error creating comfort scenario: {e}\")\n            return None\n    \n    def _get_days_from_pattern(self, pattern: Dict[str, Any]) -> List[str]:\n        \"\"\"Определение дней недели для сценария.\"\"\"\n        context = pattern['sample_context']\n        if context['is_weekend']:\n            return ['saturday', 'sunday']\n        else:\n            return ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']\n    \n    async def _suggest_related_actions(self, devices: List[str], time_of_day: str) -> List[Dict[str, Any]]:\n        \"\"\"Предложение связанных действий для улучшения сценария.\"\"\"\n        related_actions = []\n        \n        if time_of_day == 'morning':\n            # Утренние дополнительные действия\n            if 'coffee_maker' not in devices:\n                related_actions.append({\n                    \"device_id\": \"coffee_maker\",\n                    \"action\": \"start_brewing\",\n                    \"delay\": 5,\n                    \"priority\": 3,\n                    \"suggested\": True\n                })\n            \n            if 'thermostat' not in devices:\n                related_actions.append({\n                    \"device_id\": \"thermostat\",\n                    \"action\": \"set_temperature\",\n                    \"params\": {\"temperature\": 21},\n                    \"delay\": 0,\n                    \"priority\": 2,\n                    \"suggested\": True\n                })\n        \n        elif time_of_day == 'evening':\n            # Вечерние дополнительные действия\n            if any('light' in device for device in devices):\n                related_actions.append({\n                    \"device_id\": \"outdoor_lights\",\n                    \"action\": \"turn_on\",\n                    \"delay\": 30,\n                    \"priority\": 3,\n                    \"suggested\": True\n                })\n        \n        return related_actions\n    \n    async def _estimate_energy_impact(self, actions: List[Dict[str, Any]]) -> float:\n        \"\"\"Оценка влияния сценария на энергопотребление.\"\"\"\n        # Простая эвристика для оценки энергетического воздействия\n        impact = 0.0\n        \n        for action in actions:\n            action_type = action.get('action', '')\n            if 'turn_off' in action_type:\n                impact += 5.0  # Экономия\n            elif 'turn_on' in action_type:\n                impact -= 2.0  # Потребление\n            elif 'dim' in action_type or 'brightness' in action_type:\n                impact += 1.0  # Небольшая экономия\n        \n        return impact\n    \n    async def _estimate_comfort_score(self, actions: List[Dict[str, Any]], time_of_day: str) -> float:\n        \"\"\"Оценка влияния сценария на комфорт.\"\"\"\n        score = 0.5  # Базовый уровень\n        \n        # Бонусы за полезные действия\n        action_types = [action.get('action', '') for action in actions]\n        \n        if 'gradual' in ' '.join(action_types):\n            score += 0.2  # Плавные переходы повышают комфорт\n        \n        if time_of_day == 'morning' and any('coffee' in action.get('device_id', '') for action in actions):\n            score += 0.15  # Утренний кофе\n        \n        if len(actions) > 1:\n            score += 0.1  # Комплексные сценарии\n        \n        return min(1.0, score)\n    \n    async def _group_related_scenarios(self, scenarios: List[SmartScenario]) -> List[SmartScenario]:\n        \"\"\"Группировка связанных сценариев для избежания дублирования.\"\"\"\n        if not scenarios:\n            return scenarios\n        \n        # Группировка по времени и типу\n        grouped = {}\n        for scenario in scenarios:\n            key = f\"{scenario.scenario_type.value}_{scenario.trigger_conditions[0].get('value', 'none')}\"\n            if key not in grouped:\n                grouped[key] = []\n            grouped[key].append(scenario)\n        \n        # Выбор лучшего сценария из каждой группы\n        best_scenarios = []\n        for group in grouped.values():\n            if len(group) == 1:\n                best_scenarios.append(group[0])\n            else:\n                # Выбираем сценарий с максимальной уверенностью\n                best = max(group, key=lambda s: s.confidence * s.frequency)\n                best_scenarios.append(best)\n        \n        return best_scenarios\n    \n    async def _optimize_scenarios(self, scenarios: List[SmartScenario]) -> List[SmartScenario]:\n        \"\"\"Оптимизация сценариев для повышения эффективности.\"\"\"\n        optimized = []\n        \n        for scenario in scenarios:\n            # Оптимизация действий\n            optimized_actions = await self._optimize_actions(scenario.actions)\n            \n            # Создание оптимизированного сценария\n            optimized_scenario = SmartScenario(\n                id=scenario.id,\n                name=scenario.name,\n                description=scenario.description,\n                scenario_type=scenario.scenario_type,\n                trigger_conditions=scenario.trigger_conditions,\n                actions=optimized_actions,\n                confidence=scenario.confidence,\n                frequency=scenario.frequency,\n                energy_impact=scenario.energy_impact,\n                comfort_score=scenario.comfort_score,\n                created_at=scenario.created_at\n            )\n            \n            optimized.append(optimized_scenario)\n        \n        return optimized\n    \n    async def _optimize_actions(self, actions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:\n        \"\"\"Оптимизация последовательности действий.\"\"\"\n        if not actions:\n            return actions\n        \n        # Сортировка по приоритету\n        sorted_actions = sorted(actions, key=lambda a: a.get('priority', 5))\n        \n        # Оптимизация задержек\n        optimized = []\n        current_delay = 0\n        \n        for action in sorted_actions:\n            optimized_action = action.copy()\n            optimized_action['delay'] = current_delay\n            optimized.append(optimized_action)\n            \n            # Увеличиваем задержку для следующего действия\n            current_delay += action.get('delay', 2)\n        \n        return optimized\n    \n    async def suggest_scenario_improvements(self, scenario_id: str, usage_stats: Dict[str, Any]) -> List[str]:\n        \"\"\"Предложение улучшений для существующего сценария.\"\"\"\n        suggestions = []\n        \n        success_rate = usage_stats.get('success_rate', 0.0)\n        user_feedback = usage_stats.get('user_feedback', {})\n        \n        if success_rate < 0.7:\n            suggestions.append(\"Consider adjusting trigger conditions - low success rate detected\")\n        \n        if user_feedback.get('too_early', 0) > user_feedback.get('too_late', 0):\n            suggestions.append(\"Scenario might be triggering too early - consider delaying by 15-30 minutes\")\n        elif user_feedback.get('too_late', 0) > user_feedback.get('too_early', 0):\n            suggestions.append(\"Scenario might be triggering too late - consider advancing by 15-30 minutes\")\n        \n        energy_usage = usage_stats.get('energy_usage', 0)\n        if energy_usage > 20:  # Высокое потребление\n            suggestions.append(\"High energy usage detected - consider adding energy-saving actions\")\n        \n        return suggestions\n    \n    async def generate_voice_activated_scenarios(self, voice_commands: List[str]) -> List[SmartScenario]:\n        \"\"\"Создание сценариев на основе голосовых команд.\"\"\"\n        scenarios = []\n        \n        # Анализ частых голосовых команд\n        command_analysis = await self._analyze_voice_commands(voice_commands)\n        \n        for command_pattern in command_analysis:\n            if command_pattern['frequency'] >= 3:\n                scenario = await self._create_voice_scenario(command_pattern)\n                if scenario:\n                    scenarios.append(scenario)\n        \n        return scenarios\n    \n    async def _analyze_voice_commands(self, commands: List[str]) -> List[Dict[str, Any]]:\n        \"\"\"Анализ голосовых команд для поиска паттернов.\"\"\"\n        # Простой анализ частоты команд\n        command_freq = {}\n        for command in commands:\n            normalized = command.lower().strip()\n            command_freq[normalized] = command_freq.get(normalized, 0) + 1\n        \n        # Возвращаем команды с частотой больше 1\n        patterns = [\n            {'command': cmd, 'frequency': freq}\n            for cmd, freq in command_freq.items() if freq > 1\n        ]\n        \n        return sorted(patterns, key=lambda x: x['frequency'], reverse=True)\n    \n    async def _create_voice_scenario(self, command_pattern: Dict[str, Any]) -> Optional[SmartScenario]:\n        \"\"\"Создание сценария на основе голосовой команды.\"\"\"\n        try:\n            command = command_pattern['command']\n            frequency = command_pattern['frequency']\n            \n            # Анализ команды для извлечения действий\n            if 'включи' in command or 'turn on' in command:\n                if 'свет' in command or 'light' in command:\n                    actions = [{\n                        \"device_id\": \"living_room_lights\",\n                        \"action\": \"turn_on\",\n                        \"priority\": 1\n                    }]\n                elif 'музыку' in command or 'music' in command:\n                    actions = [{\n                        \"device_id\": \"spotify\",\n                        \"action\": \"play\",\n                        \"priority\": 1\n                    }]\n                else:\n                    return None\n                \n                scenario_id = f\"voice_command_{abs(hash(command))}\"\n                \n                return SmartScenario(\n                    id=scenario_id,\n                    name=f\"Voice Command: {command.title()}\",\n                    description=f\"Execute frequent voice command: '{command}'\",\n                    scenario_type=ScenarioType.PATTERN_BASED,\n                    trigger_conditions=[{\n                        \"type\": \"voice_command\",\n                        \"phrase\": command,\n                        \"similarity_threshold\": 0.8\n                    }],\n                    actions=actions,\n                    confidence=min(0.9, frequency / 10.0),\n                    frequency=frequency,\n                    energy_impact=0.0,\n                    comfort_score=0.8,\n                    created_at=datetime.now()\n                )\n            \n            return None\n            \n        except Exception as e:\n            print(f\"Error creating voice scenario: {e}\")\n            return None\n