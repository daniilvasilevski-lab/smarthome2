"""Wake Word Detection."""

from enum import Enum
from dataclasses import dataclass
from typing import Optional, List, Callable
import asyncio
import structlog

try:
    import numpy as np
    WAKE_WORD_AVAILABLE = True
except ImportError:
    WAKE_WORD_AVAILABLE = False

logger = structlog.get_logger(__name__)


class WakeWordProvider(Enum):
    PORCUPINE = "porcupine"
    SIMPLE_STT = "simple_stt"


@dataclass
class WakeWordResult:
    keyword: str
    confidence: float
    provider: WakeWordProvider
    timestamp: float


class WakeWordDetector:
    def __init__(self, provider: WakeWordProvider = WakeWordProvider.SIMPLE_STT,
                 wake_words: Optional[List[str]] = None):
        self.provider = provider
        self.wake_words = wake_words or ["привет ассистент", "окей дом"]
        self.sensitivity = 0.5
        
        self._logger = structlog.get_logger(__name__)
        self._initialized = False
        self._listening = False
        self._callbacks: List[Callable] = []
        
        if not WAKE_WORD_AVAILABLE:
            self._logger.warning("Wake word libraries not available")
    
    async def initialize(self) -> bool:
        if not WAKE_WORD_AVAILABLE:
            return False
        self._initialized = True
        return True
    
    async def start_listening(self) -> bool:
        if not self._initialized:
            return False
        self._listening = True
        self._logger.info("Started listening for wake words")
        return True
    
    async def stop_listening(self):
        self._listening = False
        self._logger.info("Stopped listening for wake words")
    
    def add_wake_word(self, word: str):
        if word not in self.wake_words:
            self.wake_words.append(word)
            self._logger.info("Wake word added", word=word)
    
    def remove_wake_word(self, word: str):
        if word in self.wake_words:
            self.wake_words.remove(word)
            self._logger.info("Wake word removed", word=word)
    
    def set_sensitivity(self, sensitivity: float):
        self.sensitivity = max(0.0, min(1.0, sensitivity))
        self._logger.info("Sensitivity changed", sensitivity=self.sensitivity)
    
    def is_listening(self) -> bool:
        return self._listening
    
    def is_available(self) -> bool:
        return WAKE_WORD_AVAILABLE and self._initialized