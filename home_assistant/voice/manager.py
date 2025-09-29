"""Voice Manager - основной класс для управления голосовой системой."""

from enum import Enum
from dataclasses import dataclass
from typing import Optional, Dict, List, Callable, Any
import asyncio
import structlog
import time

from .audio import AudioManager
from .stt import STTEngine, STTProvider, STTResult
from .tts import TTSEngine, TTSProvider, TTSResult
from .wake_word import WakeWordDetector, WakeWordProvider, WakeWordResult

logger = structlog.get_logger(__name__)


class VoiceState(Enum):
    IDLE = "idle"
    LISTENING_WAKE_WORD = "listening_wake_word"
    LISTENING_COMMAND = "listening_command"
    PROCESSING = "processing"
    SPEAKING = "speaking"
    ERROR = "error"


@dataclass
class VoiceConfig:
    stt_provider: STTProvider = STTProvider.GOOGLE
    stt_language: str = "ru"
    stt_model: str = "base"
    
    tts_provider: TTSProvider = TTSProvider.PYTTSX3
    tts_language: str = "ru"
    tts_rate: int = 200
    tts_volume: float = 0.9
    
    wake_word_provider: WakeWordProvider = WakeWordProvider.SIMPLE_STT
    wake_words: List[str] = None
    wake_word_sensitivity: float = 0.5
    
    sample_rate: int = 16000
    channels: int = 1
    chunk_size: int = 1024
    
    openai_api_key: Optional[str] = None
    
    def __post_init__(self):
        if self.wake_words is None:
            self.wake_words = ["привет ассистент", "окей дом"]


@dataclass
class VoiceInteraction:
    wake_word: str
    start_time: float
    command: Optional[str] = None
    response: Optional[str] = None
    end_time: Optional[float] = None


class VoiceManager:
    def __init__(self, config: VoiceConfig, reasoning_engine=None, event_system=None):
        self.config = config
        self.reasoning_engine = reasoning_engine
        self.event_system = event_system
        
        self._logger = structlog.get_logger(__name__)
        self._state = VoiceState.IDLE
        self._initialized = False
        self._callbacks: Dict[str, List[Callable]] = {}
        self._current_interaction: Optional[VoiceInteraction] = None
        
        # Компоненты
        self.audio_manager: Optional[AudioManager] = None
        self.stt_engine: Optional[STTEngine] = None
        self.tts_engine: Optional[TTSEngine] = None
        self.wake_word_detector: Optional[WakeWordDetector] = None
    
    async def initialize(self) -> bool:
        """Инициализация всех компонентов голосовой системы."""
        try:
            # Audio Manager
            self.audio_manager = AudioManager(
                sample_rate=self.config.sample_rate,
                channels=self.config.channels,
                chunk_size=self.config.chunk_size
            )
            if not await self.audio_manager.initialize():
                self._logger.error("Failed to initialize audio manager")
                return False
            
            # STT Engine
            self.stt_engine = STTEngine(
                provider=self.config.stt_provider,
                language=self.config.stt_language
            )
            if not await self.stt_engine.initialize():
                self._logger.error("Failed to initialize STT engine")
                return False
            
            # TTS Engine
            self.tts_engine = TTSEngine(
                provider=self.config.tts_provider,
                language=self.config.tts_language
            )
            if not await self.tts_engine.initialize():
                self._logger.error("Failed to initialize TTS engine")
                return False
            
            # Wake Word Detector
            self.wake_word_detector = WakeWordDetector(
                provider=self.config.wake_word_provider,
                wake_words=self.config.wake_words
            )
            if not await self.wake_word_detector.initialize():
                self._logger.error("Failed to initialize wake word detector")
                return False
            
            self._initialized = True
            self._logger.info("Voice manager initialized successfully")
            return True
            
        except Exception as e:
            self._logger.error("Voice manager initialization failed", error=str(e))
            return False
    
    async def start(self) -> bool:
        """Запуск голосовой системы."""
        if not self._initialized:
            self._logger.error("Voice manager not initialized")
            return False
        
        try:
            # Запускаем аудио запись
            if not await self.audio_manager.start_recording():
                self._logger.error("Failed to start audio recording")
                return False
            
            # Запускаем детектор ключевых слов
            if not await self.wake_word_detector.start_listening():
                self._logger.error("Failed to start wake word detection")
                return False
            
            self._state = VoiceState.LISTENING_WAKE_WORD
            self._logger.info("Voice system started")
            return True
            
        except Exception as e:
            self._logger.error("Failed to start voice system", error=str(e))
            return False
    
    async def stop(self) -> None:
        """Остановка голосовой системы."""
        try:
            if self.audio_manager:
                await self.audio_manager.stop_recording()
            
            if self.wake_word_detector:
                await self.wake_word_detector.stop_listening()
            
            self._state = VoiceState.IDLE
            self._logger.info("Voice system stopped")
            
        except Exception as e:
            self._logger.error("Error stopping voice system", error=str(e))
    

    
    async def _process_voice_command(self, stt_result: STTResult) -> None:
        """Обработка распознанной команды."""
        if not self.reasoning_engine:
            await self.speak("Система ИИ недоступна")
            return
        
        try:
            self._state = VoiceState.PROCESSING
            
            # Обрабатываем команду через AI
            result = await self.reasoning_engine.process_user_input(
                user_input=stt_result.text,
                session_id="voice_session"
            )
            
            response = result.get("response", "Команда обработана")
            
            # Произносим ответ
            await self.speak(response)
            
            # Обновляем взаимодействие
            if self._current_interaction:
                self._current_interaction.command = stt_result.text
                self._current_interaction.response = response
                self._current_interaction.end_time = time.time()
            
        except Exception as e:
            self._logger.error("Command processing failed", error=str(e))
            await self.speak("Произошла ошибка при обработке команды")
    
    async def _on_wake_word_detected(self, result: WakeWordResult) -> None:
        """Обработка детекции ключевого слова."""
        self._logger.info("Wake word detected", keyword=result.keyword)
        
        # Создаем новое взаимодействие
        self._current_interaction = VoiceInteraction(
            wake_word=result.keyword,
            start_time=result.timestamp
        )
        
        self._state = VoiceState.LISTENING_COMMAND
        
        # Здесь должна быть логика прослушивания команды
        # Для демонстрации используем простую заглушку
        await self.speak("Слушаю")
    
    def get_state(self) -> VoiceState:
        """Получить текущее состояние."""
        return self._state
    
    def is_listening(self) -> bool:
        """Проверить, прослушивает ли система."""
        return self._state in [VoiceState.LISTENING_WAKE_WORD, VoiceState.LISTENING_COMMAND]
    
    def is_available(self) -> bool:
        """Проверить доступность голосовой системы."""
        return (self._initialized and 
                self.audio_manager and self.audio_manager.is_recording() and
                self.stt_engine and self.stt_engine.is_available() and
                self.tts_engine and self.tts_engine.is_available())
    
    def add_callback(self, event: str, callback: Callable) -> None:
        """Добавить callback для события."""
        if event not in self._callbacks:
            self._callbacks[event] = []
        self._callbacks[event].append(callback)
    
    def remove_callback(self, event: str, callback: Callable) -> None:
        """Удалить callback для события."""
        if event in self._callbacks and callback in self._callbacks[event]:
            self._callbacks[event].remove(callback)
    
    async def speak(self, text: str, blocking: bool = False) -> bool:
        """Произнести текст."""
        try:
            if not self.tts_engine:
                return False
            
            result = await self.tts_engine.synthesize(text)
            if result.success and result.audio_data:
                await self.audio_manager.play_audio(result.audio_data)
                return True
            return False
        except Exception as e:
            self._logger.error("Failed to speak text", error=str(e))
            return False
    
    async def listen_once(self, timeout: float = 5.0) -> Optional[str]:
        """Прослушать одну команду."""
        try:
            if not self.stt_engine:
                return None
            
            # Записываем аудио
            audio_data = await self.audio_manager.record_audio(duration=timeout)
            if not audio_data:
                return None
            
            # Распознаем речь
            result = await self.stt_engine.transcribe(audio_data)
            return result.text if result.success else None
            
        except Exception as e:
            self._logger.error("Failed to listen for command", error=str(e))
            return None