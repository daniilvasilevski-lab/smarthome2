"""
Основная функция запуска Home Assistant AI.
"""

import asyncio
import signal
import sys
import uvicorn
from typing import Dict, Any, Optional
from pathlib import Path
import structlog

from .config import HomeAssistantConfig
from .events_simple import EventSystem
from ..storage.database import DatabaseManager
from ..communication.hub import CommunicationHub
from ..ai.reasoning import ReasoningEngine
from ..api.main import create_app

logger = structlog.get_logger(__name__)


class LifecycleManager:
    """Менеджер жизненного цикла приложения."""
    
    def __init__(self):
        """Инициализация менеджера жизненного цикла."""
        self.components: Dict[str, Any] = {}
        self.running = False
        self._shutdown_event = asyncio.Event()
        self._logger = structlog.get_logger(__name__)
    
    def register_component(self, name: str, component: Any) -> None:
        """
        Регистрация компонента в системе.
        
        Args:
            name: Имя компонента
            component: Экземпляр компонента
        """
        self.components[name] = component
        self._logger.debug("Component registered", name=name)
    
    async def shutdown(self) -> None:
        """Корректное завершение всех компонентов."""
        if not self.running:
            return
        
        self._logger.info("Shutting down all components")
        self.running = False
        
        # Завершаем компоненты в обратном порядке
        for name, component in reversed(list(self.components.items())):
            try:
                if hasattr(component, 'stop'):
                    await component.stop()
                elif hasattr(component, 'shutdown'):
                    await component.shutdown()
                self._logger.info("Component stopped", name=name)
            except Exception as e:
                self._logger.error("Error stopping component", 
                                 name=name, error=str(e))
        
        self._shutdown_event.set()


async def main() -> None:
    """Основная функция запуска приложения."""
    # Настройка логирования
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer()
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    logger = structlog.get_logger(__name__)
    
    try:
        # Загружаем конфигурацию
        config = HomeAssistantConfig()
        
        print("🏠 Запуск Home Assistant AI...")
        print(f"📊 Debug режим: {config.debug}")
        print(f"🗃️ База данных: {config.get_database_url()}")
        print(f"🤖 AI провайдер: {'OpenAI' if config.ai.openai_api_key else 'Локальный'}")
        print(f"🔒 Privacy режим: {config.privacy.enabled}")
        print(f"🌐 API сервер: {config.api.host}:{config.api.port}")
        
        # Создаем директории
        Path(config.data_dir).mkdir(parents=True, exist_ok=True)
        Path(config.config_dir).mkdir(parents=True, exist_ok=True)
        Path("logs").mkdir(exist_ok=True)
        
        # Инициализация основных компонентов
        print("\n🔧 Инициализация компонентов...")
        
        # Система событий
        event_system = EventSystem()
        print("✅ Система событий")
        
        # База данных
        db_manager = DatabaseManager(config)
        await db_manager.initialize()
        print("✅ База данных")
        
        # Communication Hub
        communication_hub = CommunicationHub(config, event_system, db_manager)
        await communication_hub.start()
        print("✅ Communication Hub")
        
        # AI Reasoning Engine
        reasoning_engine = ReasoningEngine(config, event_system, db_manager, communication_hub)
        print("✅ AI Reasoning Engine")
        
        # Lifecycle Manager
        lifecycle_manager = LifecycleManager()
        lifecycle_manager.register_component("event_system", event_system)
        lifecycle_manager.register_component("db_manager", db_manager)
        lifecycle_manager.register_component("communication_hub", communication_hub)
        lifecycle_manager.register_component("reasoning_engine", reasoning_engine)
        print("✅ Lifecycle Manager")
        
        # Создание FastAPI приложения (пока без voice_manager)
        app = create_app(
            config=config,
            event_system=event_system,
            db_manager=db_manager,
            communication_hub=communication_hub,
            reasoning_engine=reasoning_engine,
            voice_manager=None  # Установим позже
        )
        print("✅ REST API")
        
        # Запуск поиска устройств
        print("\n🔍 Запуск поиска устройств...")
        devices = await communication_hub.discover_all_devices()
        print(f"✅ Найдено устройств: {len(devices)}")
        
        # Демонстрационные интеграции
        print("\n🔌 Настройка интеграций...")
        
        # Spotify интеграция (симуляция)
        await db_manager.save_integration({
            "id": "spotify_main",
            "name": "Spotify",
            "type": "spotify",
            "enabled": True,
            "config": {"client_id": "demo", "client_secret": "demo"},
            "credentials": {}
        })
        
        # Weather интеграция (симуляция)
        await db_manager.save_integration({
            "id": "weather_main",
            "name": "OpenWeatherMap",
            "type": "weather",
            "enabled": True,
            "config": {"api_key": "demo", "location": "Moscow"},
            "credentials": {}
        })
        
        print("✅ Spotify")
        print("✅ Weather API")
        
        # Инициализация голосового ассистента
        voice_manager = None
        if config.voice.enabled:
            print("\n🎤 Инициализация голосового ассистента...")
            
            try:
                from ..voice import VoiceManager
                from ..voice.manager import VoiceConfig
                from ..voice.stt import STTProvider
                from ..voice.tts import TTSProvider
                from ..voice.wake_word import WakeWordProvider
                
                # Создаем конфигурацию голосового ассистента
                voice_config = VoiceConfig(
                    # STT настройки
                    stt_provider=STTProvider.GOOGLE if config.voice.stt_engine == "google" 
                                else STTProvider.WHISPER_LOCAL if config.voice.stt_engine == "whisper"
                                else STTProvider.VOSK,
                    stt_language=config.voice.stt_language,
                    stt_model="base",
                    
                    # TTS настройки
                    tts_provider=TTSProvider.PYTTSX3 if config.voice.tts_engine == "pyttsx3"
                                else TTSProvider.GOOGLE_TTS,
                    tts_language=config.voice.tts_language,
                    tts_rate=config.voice.tts_voice_rate,
                    tts_volume=1.0,
                    
                    # Wake Word настройки
                    wake_word_provider=WakeWordProvider.SIMPLE_STT,
                    wake_words=["привет ассистент", "окей дом", "эй ассистент"],
                    wake_word_sensitivity=0.5,
                    
                    # API ключи
                    openai_api_key=config.ai.openai_api_key
                )
                
                # Создаем Voice Manager
                voice_manager = VoiceManager(
                    config=voice_config,
                    reasoning_engine=reasoning_engine,
                    event_system=event_system
                )
                
                # Инициализируем голосовую систему
                if await voice_manager.initialize():
                    # Запускаем голосового ассистента
                    if await voice_manager.start():
                        print("✅ Голосовой ассистент активен")
                        print(f"   🎙️ Ключевые слова: {', '.join(voice_config.wake_words)}")
                        print(f"   🗣️ STT: {voice_config.stt_provider.value}")
                        print(f"   🔊 TTS: {voice_config.tts_provider.value}")
                    else:
                        print("⚠️ Не удалось запустить голосового ассистента")
                        voice_manager = None
                else:
                    print("⚠️ Не удалось инициализировать голосовую систему")
                    voice_manager = None
                    
            except ImportError as e:
                print(f"⚠️ Голосовые библиотеки не установлены: {e}")
                print("   Установите зависимости: pip install 'home-assistant-ai[voice]'")
                voice_manager = None
            except Exception as e:
                print(f"❌ Ошибка инициализации голосового ассистента: {e}")
                voice_manager = None
        else:
            print("\n🔇 Голосовое управление отключено в конфигурации")
        
        # Устанавливаем voice_manager в приложение
        app.state.voice_manager = voice_manager
        
        print(f"\n🚀 Home Assistant AI запущен!")
        print(f"📖 API документация: http://{config.api.host}:{config.api.port}/docs")
        print(f"💬 Чат API: http://{config.api.host}:{config.api.port}/chat")
        print(f"🏠 Устройства: http://{config.api.host}:{config.api.port}/devices")
        print(f"📊 Статус: http://{config.api.host}:{config.api.port}/status")
        
        if voice_manager:
            print(f"🎤 Голосовой API: http://{config.api.host}:{config.api.port}/voice/status")
        
        print("\n💡 Примеры команд:")
        print("  - Включи свет")
        print("  - Какая погода?")
        print("  - Включи музыку")
        print("  - Что умеешь?")
        
        # Запуск API сервера
        config_uvicorn = uvicorn.Config(
            app,
            host=config.api.host,
            port=config.api.port,
            reload=config.api.reload,
            log_level="info" if not config.debug else "debug"
        )
        
        server = uvicorn.Server(config_uvicorn)
        
        # Graceful shutdown
        try:
            await server.serve()
        except KeyboardInterrupt:
            print("\n🛑 Остановка Home Assistant AI...")
            await lifecycle_manager.shutdown()
            print("✅ Система остановлена")
        
    except Exception as e:
        logger.error("Ошибка запуска", error=str(e))
        print(f"❌ Ошибка: {e}")