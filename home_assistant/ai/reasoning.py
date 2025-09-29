"""
AI Reasoning Engine - умный движок для понимания и выполнения команд пользователя.

Поддерживает работу с внешними LLM (OpenAI) и локальными моделями (Ollama).
Включает контекстное понимание, планирование действий и исполнение команд.
"""

import asyncio
import json
import re
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from dataclasses import dataclass
import structlog

from ..core.config import HomeAssistantConfig
from ..core.events_simple import EventSystem
from ..storage.database import DatabaseManager

logger = structlog.get_logger(__name__)


@dataclass
class ReasoningContext:
    """Контекст для AI reasoning."""
    user_input: str
    session_id: str
    conversation_history: List[Dict[str, Any]]
    available_devices: List[Dict[str, Any]]
    current_time: datetime
    user_location: Optional[str] = None
    privacy_mode: bool = False


@dataclass
class ActionPlan:
    """План действий для выполнения."""
    intent: str  # Намерение пользователя
    confidence: float  # Уверенность в понимании
    actions: List[Dict[str, Any]]  # Список действий
    requires_confirmation: bool = False
    explanation: str = ""  # Объяснение действий


class LLMProvider:
    """Базовый класс для провайдеров LLM."""
    
    async def generate_response(self, prompt: str, **kwargs) -> str:
        """Генерация ответа от LLM."""
        raise NotImplementedError
    
    async def analyze_intent(self, user_input: str, context: ReasoningContext) -> Dict[str, Any]:
        """Анализ намерения пользователя."""
        raise NotImplementedError


class OpenAIProvider(LLMProvider):
    """Провайдер для OpenAI API."""
    
    def __init__(self, api_key: str, model: str = "gpt-4"):
        self.api_key = api_key
        self.model = model
        self._logger = structlog.get_logger(__name__)
    
    async def generate_response(self, prompt: str, **kwargs) -> str:
        """Генерация ответа через OpenAI API."""
        try:
            # Симуляция вызова OpenAI API
            # В реальной реализации здесь будет использоваться openai library
            
            self._logger.info("Generating OpenAI response", model=self.model)
            
            # Пример умного ответа
            if "включи свет" in prompt.lower() or "turn on light" in prompt.lower():
                return "Конечно! Включаю свет в гостиной. Умная лампа теперь включена с яркостью 80%."
            
            elif "какая погода" in prompt.lower() or "weather" in prompt.lower():
                return "Сейчас на улице +15°C, небольшая облачность. Вечером ожидается небольшой дождь."
            
            elif "включи музыку" in prompt.lower() or "play music" in prompt.lower():
                return "Запускаю вашу любимую музыку на Spotify. Включаю плейлист 'Домашняя атмосфера'."
            
            elif "что умеешь" in prompt.lower() or "what can you do" in prompt.lower():
                return """Я умею многое! Могу:
                
🏠 Управлять умными устройствами (свет, розетки, датчики)
🎵 Включать музыку через Spotify
🌤️ Сообщать погоду и прогноз
🗣️ Вести естественные разговоры
🔧 Автоматизировать рутинные задачи
🔒 Работать полностью локально в приватном режиме

Просто скажите, что вам нужно!"""
            
            else:
                return f"Понял ваш запрос: '{prompt}'. Анализирую возможные действия и найду лучшее решение."
        
        except Exception as e:
            self._logger.error("OpenAI API error", error=str(e))
            return "Извините, произошла ошибка при обработке запроса."
    
    async def analyze_intent(self, user_input: str, context: ReasoningContext) -> Dict[str, Any]:
        """Анализ намерения пользователя через OpenAI."""
        try:
            # Создаем промпт для анализа намерения
            prompt = f"""
Проанализируй намерение пользователя и создай план действий.

Пользователь сказал: "{user_input}"

Доступные устройства: {[d['name'] for d in context.available_devices]}

Верни JSON с полями:
- intent: тип намерения (device_control, information, conversation, music, weather)
- confidence: уверенность 0-1
- target_devices: список ID устройств для управления
- parameters: параметры команды
- response: ответ пользователю

Пример:
{{"intent": "device_control", "confidence": 0.95, "target_devices": ["light_001"], "parameters": {{"action": "turn_on", "brightness": 80}}, "response": "Включаю свет"}}
"""
            
            # Симуляция анализа намерения
            intent_data = self._analyze_user_intent(user_input, context)
            
            return intent_data
            
        except Exception as e:
            self._logger.error("Intent analysis error", error=str(e))
            return {
                "intent": "conversation",
                "confidence": 0.5,
                "target_devices": [],
                "parameters": {},
                "response": "Не могу точно понять запрос, но попробую помочь."
            }
    
    def _analyze_user_intent(self, user_input: str, context: ReasoningContext) -> Dict[str, Any]:
        """Внутренний анализ намерения (симуляция OpenAI)."""
        input_lower = user_input.lower()
        
        # Управление светом
        if any(word in input_lower for word in ["свет", "лампа", "light", "включи", "выключи", "turn on", "turn off"]):
            action = "turn_on" if any(word in input_lower for word in ["включи", "turn on"]) else "turn_off"
            light_devices = [d for d in context.available_devices if d.get("device_type") == "light"]
            
            return {
                "intent": "device_control",
                "confidence": 0.9,
                "target_devices": [d["id"] for d in light_devices[:1]] if light_devices else [],
                "parameters": {"action": action, "brightness": 80 if action == "turn_on" else 0},
                "response": f"{'Включаю' if action == 'turn_on' else 'Выключаю'} свет"
            }
        
        # Музыка
        elif any(word in input_lower for word in ["музыка", "песня", "плейлист", "music", "song", "play"]):
            return {
                "intent": "music",
                "confidence": 0.85,
                "target_devices": [],
                "parameters": {"service": "spotify", "action": "play", "query": "домашняя атмосфера"},
                "response": "Включаю музыку на Spotify"
            }
        
        # Погода
        elif any(word in input_lower for word in ["погода", "температура", "weather", "температура"]):
            return {
                "intent": "weather",
                "confidence": 0.9,
                "target_devices": [],
                "parameters": {"location": "current"},
                "response": "Получаю информацию о погоде"
            }
        
        # Обычная беседа
        else:
            return {
                "intent": "conversation",
                "confidence": 0.7,
                "target_devices": [],
                "parameters": {},
                "response": "Понял, отвечаю на ваш вопрос"
            }


class OllamaProvider(LLMProvider):
    """Провайдер для локальных моделей через Ollama."""
    
    def __init__(self, model: str = "llama2:7b", base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url
        self._logger = structlog.get_logger(__name__)
    
    async def generate_response(self, prompt: str, **kwargs) -> str:
        """Генерация ответа через Ollama."""
        try:
            # Симуляция вызова Ollama API
            self._logger.info("Generating Ollama response", model=self.model)
            
            # Упрощенные ответы для локальной модели
            if "включи свет" in prompt.lower():
                return "Включаю свет."
            elif "музыка" in prompt.lower():
                return "Запускаю музыку."
            elif "погода" in prompt.lower():
                return "Проверяю погоду."
            else:
                return "Обрабатываю ваш запрос."
            
        except Exception as e:
            self._logger.error("Ollama API error", error=str(e))
            return "Ошибка локальной модели."
    
    async def analyze_intent(self, user_input: str, context: ReasoningContext) -> Dict[str, Any]:
        """Упрощенный анализ намерения для локальной модели."""
        return {
            "intent": "conversation",
            "confidence": 0.6,
            "target_devices": [],
            "parameters": {},
            "response": "Понял ваш запрос."
        }


class ReasoningEngine:
    """Основной движок AI reasoning."""
    
    def __init__(self, config: HomeAssistantConfig, event_system: EventSystem,
                 db_manager: DatabaseManager, communication_hub):
        """
        Инициализация Reasoning Engine.
        
        Args:
            config: Конфигурация системы
            event_system: Система событий
            db_manager: Менеджер базы данных
            communication_hub: Хаб связи для управления устройствами
        """
        self.config = config
        self.event_system = event_system
        self.db_manager = db_manager
        self.communication_hub = communication_hub
        self._logger = structlog.get_logger(__name__)
        
        # Инициализация провайдеров LLM
        self._init_llm_providers()
    
    def _init_llm_providers(self) -> None:
        """Инициализация провайдеров LLM."""
        self.providers = {}
        
        # OpenAI провайдер
        if self.config.ai.openai_api_key:
            self.providers["openai"] = OpenAIProvider(
                api_key=self.config.ai.openai_api_key,
                model=self.config.ai.openai_model
            )
        
        # Ollama провайдер для локальных моделей
        if self.config.ai.local_llm_enabled:
            self.providers["ollama"] = OllamaProvider(
                model=self.config.ai.local_llm_model,
                base_url=self.config.ai.local_llm_url
            )
        
        self._logger.info("LLM providers initialized", providers=list(self.providers.keys()))
    
    def _get_active_provider(self) -> Optional[LLMProvider]:
        """Получение активного провайдера LLM."""
        # В приватном режиме используем только локальные модели
        if self.config.privacy.enabled and self.config.privacy.force_local_processing:
            return self.providers.get("ollama")
        
        # Приоритет: OpenAI -> Ollama
        return self.providers.get("openai") or self.providers.get("ollama")
    
    async def process_user_input(self, user_input: str, session_id: str) -> Dict[str, Any]:
        """
        Обработка пользовательского ввода.
        
        Args:
            user_input: Текст от пользователя
            session_id: Идентификатор сессии
            
        Returns:
            Результат обработки с ответом и действиями
        """
        try:
            self._logger.info("Processing user input", 
                            user_input=user_input, session_id=session_id)
            
            # Сохраняем сообщение пользователя
            await self.db_manager.save_conversation(
                session_id=session_id,
                message_type="user",
                content=user_input
            )
            
            # Собираем контекст
            context = await self._build_context(user_input, session_id)
            
            # Получаем активный провайдер
            provider = self._get_active_provider()
            if not provider:
                response = "LLM провайдер недоступен. Проверьте конфигурацию."
                await self.db_manager.save_conversation(
                    session_id=session_id,
                    message_type="assistant",
                    content=response
                )
                return {"response": response, "actions": []}
            
            # Анализируем намерение
            intent_result = await provider.analyze_intent(user_input, context)
            
            # Создаем план действий
            action_plan = await self._create_action_plan(intent_result, context)
            
            # Выполняем действия
            execution_results = await self._execute_actions(action_plan, session_id)
            
            # Генерируем финальный ответ
            final_response = await self._generate_final_response(
                action_plan, execution_results, provider, context
            )
            
            # Сохраняем ответ ассистента
            await self.db_manager.save_conversation(
                session_id=session_id,
                message_type="assistant",
                content=final_response,
                metadata={
                    "intent": intent_result.get("intent"),
                    "confidence": intent_result.get("confidence"),
                    "actions_count": len(action_plan.actions)
                }
            )
            
            return {
                "response": final_response,
                "actions": execution_results,
                "intent": intent_result.get("intent"),
                "confidence": intent_result.get("confidence")
            }
            
        except Exception as e:
            self._logger.error("Error processing user input", error=str(e))
            error_response = "Извините, произошла ошибка при обработке вашего запроса."
            
            await self.db_manager.save_conversation(
                session_id=session_id,
                message_type="assistant",
                content=error_response
            )
            
            return {"response": error_response, "actions": []}
    
    async def _build_context(self, user_input: str, session_id: str) -> ReasoningContext:
        """Построение контекста для reasoning."""
        # Получаем историю разговора
        conversation_history = await self.db_manager.get_conversation_history(session_id, limit=10)
        
        # Получаем список доступных устройств
        available_devices = await self.db_manager.get_all_devices()
        
        return ReasoningContext(
            user_input=user_input,
            session_id=session_id,
            conversation_history=conversation_history,
            available_devices=available_devices,
            current_time=datetime.utcnow(),
            privacy_mode=self.config.privacy.enabled
        )
    
    async def _create_action_plan(self, intent_result: Dict[str, Any], 
                                 context: ReasoningContext) -> ActionPlan:
        """Создание плана действий на основе анализа намерения."""
        intent = intent_result.get("intent", "conversation")
        actions = []
        
        if intent == "device_control":
            # Команды управления устройствами
            for device_id in intent_result.get("target_devices", []):
                actions.append({
                    "type": "device_command",
                    "device_id": device_id,
                    "command": intent_result.get("parameters", {}).get("action", "toggle"),
                    "params": intent_result.get("parameters", {})
                })
        
        elif intent == "music":
            # Команды управления музыкой
            actions.append({
                "type": "integration_command",
                "service": "spotify",
                "command": "play",
                "params": intent_result.get("parameters", {})
            })
        
        elif intent == "weather":
            # Запрос погоды
            actions.append({
                "type": "integration_command",
                "service": "weather",
                "command": "get_current",
                "params": intent_result.get("parameters", {})
            })
        
        return ActionPlan(
            intent=intent,
            confidence=intent_result.get("confidence", 0.5),
            actions=actions,
            explanation=intent_result.get("response", "")
        )
    
    async def _execute_actions(self, action_plan: ActionPlan, 
                              session_id: str) -> List[Dict[str, Any]]:
        """Выполнение плана действий."""
        results = []
        
        for action in action_plan.actions:
            try:
                result = {"action": action, "success": False, "error": None}
                
                if action["type"] == "device_command":
                    # Выполнение команды устройства
                    success = await self.communication_hub.send_device_command(
                        device_id=action["device_id"],
                        command=action["command"],
                        params=action.get("params", {})
                    )
                    result["success"] = success
                    
                    if success:
                        self._logger.info("Device command executed", 
                                        device_id=action["device_id"],
                                        command=action["command"])
                    else:
                        result["error"] = "Failed to execute device command"
                
                elif action["type"] == "integration_command":
                    # Выполнение команды интеграции
                    success = await self._execute_integration_command(action)
                    result["success"] = success
                    
                    if not success:
                        result["error"] = "Integration command failed"
                
                results.append(result)
                
            except Exception as e:
                self._logger.error("Action execution error", action=action, error=str(e))
                results.append({
                    "action": action,
                    "success": False,
                    "error": str(e)
                })
        
        return results
    
    async def _execute_integration_command(self, action: Dict[str, Any]) -> bool:
        """Выполнение команды интеграции."""
        service = action.get("service")
        command = action.get("command")
        
        try:
            if service == "spotify":
                # Симуляция команды Spotify
                self._logger.info("Executing Spotify command", command=command)
                return True
            
            elif service == "weather":
                # Симуляция запроса погоды
                self._logger.info("Getting weather information")
                return True
            
            return False
            
        except Exception as e:
            self._logger.error("Integration command error", service=service, error=str(e))
            return False
    
    async def _generate_final_response(self, action_plan: ActionPlan,
                                      execution_results: List[Dict[str, Any]],
                                      provider: LLMProvider,
                                      context: ReasoningContext) -> str:
        """Генерация финального ответа пользователю."""
        try:
            # Подсчитываем успешные и неудачные действия
            successful_actions = sum(1 for r in execution_results if r["success"])
            total_actions = len(execution_results)
            
            # Создаем промпт для генерации ответа
            if total_actions == 0:
                # Обычная беседа без действий
                prompt = f"Пользователь сказал: '{context.user_input}'. Ответь дружелюбно и полезно."
            else:
                # Отчет о выполненных действиях
                actions_summary = []
                for result in execution_results:
                    action = result["action"]
                    if result["success"]:
                        if action["type"] == "device_command":
                            actions_summary.append(f"✅ Команда устройству {action['device_id']}: {action['command']}")
                        elif action["type"] == "integration_command":
                            actions_summary.append(f"✅ Команда {action['service']}: {action['command']}")
                    else:
                        actions_summary.append(f"❌ Ошибка: {result.get('error', 'Неизвестная ошибка')}")
                
                prompt = f"""
Пользователь попросил: '{context.user_input}'

Выполненные действия:
{chr(10).join(actions_summary)}

Успешно: {successful_actions}/{total_actions}

Сформулируй краткий и дружелюбный ответ пользователю.
"""
            
            response = await provider.generate_response(prompt)
            return response
            
        except Exception as e:
            self._logger.error("Response generation error", error=str(e))
            return action_plan.explanation or "Задача выполнена."