"""
Упрощенная система событий для Home Assistant AI.
"""

import asyncio
from typing import Any, Dict, List, Optional, Callable, Awaitable
from datetime import datetime
from dataclasses import dataclass
import structlog

logger = structlog.get_logger(__name__)


@dataclass
class Event:
    """Базовый класс события."""
    timestamp: datetime
    source: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


@dataclass  
class DeviceFoundEvent:
    """Событие обнаружения устройства."""
    device_id: str
    device_type: str
    protocol: str
    metadata: Dict[str, Any]
    timestamp: datetime = None
    source: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


@dataclass
class DeviceStateChangedEvent:
    """Событие изменения состояния устройства."""
    device_id: str
    attribute: str
    old_value: Any
    new_value: Any
    timestamp: datetime = None
    source: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


class EventSystem:
    """Простая система событий."""
    
    def __init__(self):
        self._handlers = {}
        self._logger = structlog.get_logger(__name__)
    
    def subscribe(self, event_type, handler):
        """Подписка на событие."""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
        self._logger.debug("Event handler subscribed", event_type=event_type.__name__)
    
    async def emit(self, event):
        """Генерация события."""
        event_type = type(event)
        
        if event_type in self._handlers:
            for handler in self._handlers[event_type]:
                try:
                    await handler(event)
                except Exception as e:
                    self._logger.error("Event handler error", 
                                     event_type=event_type.__name__, 
                                     error=str(e))
        
        self._logger.debug("Event emitted", event_type=event_type.__name__)