"""
Система событий Home Assistant AI.

Этот модуль реализует асинхронную систему событий для координации
работы между различными компонентами системы.
"""

import asyncio
from typing import Any, Dict, List, Optional, Callable, Awaitable
from enum import Enum
from datetime import datetime
import uuid
import structlog

logger = structlog.get_logger(__name__)


class EventType(Enum):
    """Типы системных событий."""
    
    # Системные события
    SYSTEM_STARTUP = "system.startup"
    SYSTEM_SHUTDOWN = "system.shutdown"
    SYSTEM_ERROR = "system.error"
    
    # События устройств
    DEVICE_DISCOVERED = "device.discovered"
    DEVICE_CONNECTED = "device.connected"
    DEVICE_DISCONNECTED = "device.disconnected"
    DEVICE_STATE_CHANGED = "device.state_changed"
    DEVICE_ERROR = "device.error"
    
    # AI события
    AI_REQUEST = "ai.request"
    AI_RESPONSE = "ai.response"
    AI_REASONING_STEP = "ai.reasoning_step"
    AI_ERROR = "ai.error"
    
    # Голосовые события
    VOICE_COMMAND_RECEIVED = "voice.command_received"
    VOICE_RECOGNITION_STARTED = "voice.recognition_started"
    VOICE_RECOGNITION_FINISHED = "voice.recognition_finished"
    VOICE_SYNTHESIS_STARTED = "voice.synthesis_started"
    VOICE_SYNTHESIS_FINISHED = "voice.synthesis_finished"
    
    # API события
    API_REQUEST = "api.request"
    API_RESPONSE = "api.response"
    API_ERROR = "api.error"
    
    # События приватности
    PRIVACY_MODE_ENABLED = "privacy.mode_enabled"
    PRIVACY_MODE_DISABLED = "privacy.mode_disabled"


class Event:
    """Событие в системе."""
    
    def __init__(
        self,
        event_type: EventType,
        data: Optional[Dict[str, Any]] = None,
        source: Optional[str] = None,
        target: Optional[str] = None
    ):
        self.id = str(uuid.uuid4())
        self.type = event_type
        self.data = data or {}
        self.source = source
        self.target = target
        self.timestamp = datetime.now()
    
    def __repr__(self) -> str:
        return f"Event(id={self.id}, type={self.type.value}, source={self.source})"
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразование события в словарь."""
        return {
            "id": self.id,
            "type": self.type.value,
            "data": self.data,
            "source": self.source,
            "target": self.target,
            "timestamp": self.timestamp.isoformat()
        }


EventHandler = Callable[[Event], Awaitable[None]]


class EventBus:
    """Шина событий для координации компонентов системы."""
    
    def __init__(self):
        self._handlers: Dict[EventType, List[EventHandler]] = {}
        self._event_queue: asyncio.Queue[Event] = asyncio.Queue()
        self._running = False
        self._worker_task: Optional[asyncio.Task] = None
        self._logger = structlog.get_logger(__name__)
    
    async def start(self) -> None:
        """Запуск обработчика событий."""
        if self._running:
            return
        
        self._running = True
        self._worker_task = asyncio.create_task(self._event_worker())
        self._logger.info("EventBus started")
    
    async def stop(self) -> None:
        """Остановка обработчика событий."""
        if not self._running:
            return
        
        self._running = False
        
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
        
        self._logger.info("EventBus stopped")
    
    def subscribe(self, event_type: EventType, handler: EventHandler) -> None:
        """
        Подписка на событие.
        
        Args:
            event_type: Тип события
            handler: Асинхронная функция-обработчик
        """
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        
        self._handlers[event_type].append(handler)
        self._logger.debug(
            "Handler subscribed",
            event_type=event_type.value,
            handler=handler.__name__
        )
    
    def unsubscribe(self, event_type: EventType, handler: EventHandler) -> None:
        """
        Отписка от события.
        
        Args:
            event_type: Тип события
            handler: Функция-обработчик
        """
        if event_type in self._handlers:
            try:
                self._handlers[event_type].remove(handler)
                self._logger.debug(
                    "Handler unsubscribed",
                    event_type=event_type.value,
                    handler=handler.__name__
                )
            except ValueError:
                pass
    
    async def emit(self, event: Event) -> None:
        """
        Отправка события.
        
        Args:
            event: Событие для отправки
        """
        await self._event_queue.put(event)
        self._logger.debug(
            "Event emitted",
            event_id=event.id,
            event_type=event.type.value,
            source=event.source
        )
    
    async def emit_sync(self, event: Event) -> None:
        """
        Синхронная отправка события (блокирующая).
        
        Args:
            event: Событие для отправки
        """
        await self._handle_event(event)
    
    async def _event_worker(self) -> None:
        """Воркер для обработки событий из очереди."""
        while self._running:
            try:
                # Ожидаем событие с таймаутом
                event = await asyncio.wait_for(
                    self._event_queue.get(), timeout=1.0
                )
                await self._handle_event(event)
            except asyncio.TimeoutError:
                # Таймаут - это нормально, продолжаем работу
                continue
            except Exception as e:
                self._logger.error(
                    "Error in event worker",
                    error=str(e),
                    exc_info=True
                )
    
    async def _handle_event(self, event: Event) -> None:
        """
        Обработка события.
        
        Args:
            event: Событие для обработки
        """
        handlers = self._handlers.get(event.type, [])
        
        if not handlers:
            self._logger.debug(
                "No handlers for event",
                event_type=event.type.value
            )
            return
        
        self._logger.debug(
            "Processing event",
            event_id=event.id,
            event_type=event.type.value,
            handlers_count=len(handlers)
        )
        
        # Запускаем все обработчики параллельно
        tasks = []
        for handler in handlers:
            task = asyncio.create_task(self._safe_handle(handler, event))
            tasks.append(task)
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _safe_handle(self, handler: EventHandler, event: Event) -> None:
        """
        Безопасная обработка события с логированием ошибок.
        
        Args:
            handler: Функция-обработчик
            event: Событие
        """
        try:
            await handler(event)
        except Exception as e:
            self._logger.error(
                "Error in event handler",
                handler=handler.__name__,
                event_type=event.type.value,
                event_id=event.id,
                error=str(e),
                exc_info=True
            )


# Глобальная шина событий
_global_event_bus: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    """Получение глобальной шины событий."""
    global _global_event_bus
    if _global_event_bus is None:
        _global_event_bus = EventBus()
    return _global_event_bus


async def emit_event(
    event_type: EventType,
    data: Optional[Dict[str, Any]] = None,
    source: Optional[str] = None,
    target: Optional[str] = None
) -> None:
    """
    Утилита для быстрой отправки события.
    
    Args:
        event_type: Тип события
        data: Данные события
        source: Источник события
        target: Целевой получатель
    """
    event = Event(event_type, data, source, target)
    await get_event_bus().emit(event)




# Алиасы для обратной совместимости
EventSystem = EventBus

# Универсальные события для устройств
class DeviceFoundEvent(Event):
    """Событие обнаружения устройства"""
    def __init__(self, *args, **kwargs):
        # Извлекаем стандартные аргументы Event
        event_type = kwargs.pop('event_type', EventType.DEVICE_DISCOVERED)
        data = kwargs.pop('data', None)
        source = kwargs.pop('source', None)
        target = kwargs.pop('target', None)
        
        # Если data не указана, используем все остальные kwargs как data
        if data is None:
            data = kwargs
        
        super().__init__(
            event_type=event_type,
            data=data,
            source=source,
            target=target
        )

class DeviceStateChangedEvent(Event):
    """Событие изменения состояния устройства"""
    def __init__(self, *args, **kwargs):
        # Извлекаем стандартные аргументы Event
        event_type = kwargs.pop('event_type', EventType.DEVICE_STATE_CHANGED)
        data = kwargs.pop('data', None)
        source = kwargs.pop('source', None)
        target = kwargs.pop('target', None)
        
        # Если data не указана, используем все остальные kwargs как data
        if data is None:
            data = kwargs
        
        super().__init__(
            event_type=event_type,
            data=data,
            source=source,
            target=target
        )
