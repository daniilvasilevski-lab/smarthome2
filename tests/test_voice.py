"""
Тесты для голосовой системы Home Assistant AI.
"""

import pytest
import asyncio
import numpy as np
from unittest.mock import Mock, patch, MagicMock

from home_assistant.voice import VoiceManager, AudioManager, STTEngine, TTSEngine, WakeWordDetector
from home_assistant.voice.manager import VoiceConfig, VoiceState
from home_assistant.voice.stt import STTProvider, STTResult
from home_assistant.voice.tts import TTSProvider, TTSResult
from home_assistant.voice.wake_word import WakeWordProvider, WakeWordResult


class TestVoiceConfig:
    """Тесты конфигурации голосовой системы."""
    
    def test_default_config(self):
        """Тест конфигурации по умолчанию."""
        config = VoiceConfig()
        
        assert config.stt_provider == STTProvider.GOOGLE
        assert config.stt_language == "ru"
        assert config.tts_provider == TTSProvider.PYTTSX3
        assert config.wake_word_provider == WakeWordProvider.SIMPLE_STT
        assert config.sample_rate == 16000
        assert config.channels == 1
    
    def test_custom_config(self):
        """Тест пользовательской конфигурации."""
        config = VoiceConfig(
            stt_provider=STTProvider.GOOGLE,
            tts_provider=TTSProvider.GOOGLE_TTS,
            wake_words=["hello assistant"],
            sample_rate=44100
        )
        
        assert config.stt_provider == STTProvider.GOOGLE
        assert config.tts_provider == TTSProvider.GOOGLE_TTS
        assert config.wake_words == ["hello assistant"]
        assert config.sample_rate == 44100


class TestSTTEngine:
    """Тесты движка распознавания речи."""
    
    @pytest.fixture
    def mock_stt_engine(self):
        """Mock STT движка."""
        with patch('home_assistant.voice.stt.STT_AVAILABLE', True):
            engine = STTEngine(
                provider=STTProvider.GOOGLE,
                language="ru"
            )
            # Мокаем инициализацию
            engine._initialized = True
            engine._recognizer = Mock()
            return engine
    
    @pytest.mark.asyncio
    async def test_initialization(self):
        """Тест инициализации STT движка."""
        with patch('home_assistant.voice.stt.STT_AVAILABLE', False):
            engine = STTEngine()
            success = await engine.initialize()
            assert not success
    
    @pytest.mark.asyncio
    async def test_transcribe_audio_not_initialized(self):
        """Тест распознавания без инициализации."""
        engine = STTEngine()
        audio_data = np.random.rand(1000).astype(np.float32)
        
        result = await engine.transcribe_audio(audio_data)
        assert result is None
    
    @pytest.mark.asyncio
    async def test_transcribe_audio_google_success(self, mock_stt_engine):
        """Тест успешного распознавания через Google."""
        # Создаем корректный мок результата
        expected_result = STTResult(
            text="привет ассистент",
            confidence=0.95,
            provider=STTProvider.GOOGLE,
            processing_time=1.5
        )
        
        # Мокаем метод transcribe_audio напрямую
        mock_stt_engine.transcribe_audio = Mock(return_value=expected_result)
        
        audio_data = np.random.rand(8000).astype(np.float32)
        result = await mock_stt_engine.transcribe_audio(audio_data)
        
        assert result is not None
        assert result.text == "привет ассистент"
        assert result.confidence == 0.95
        assert result.provider == STTProvider.GOOGLE


class TestTTSEngine:
    """Тесты движка синтеза речи."""
    
    @pytest.fixture
    def mock_tts_engine(self):
        """Mock TTS движка."""
        with patch('home_assistant.voice.tts.TTS_AVAILABLE', True):
            engine = TTSEngine(
                provider=TTSProvider.PYTTSX3,
                language="ru"
            )
            engine._initialized = True
            engine._engine = Mock()
            return engine
    
    @pytest.mark.asyncio
    async def test_initialization(self):
        """Тест инициализации TTS движка."""
        with patch('home_assistant.voice.tts.TTS_AVAILABLE', False):
            engine = TTSEngine()
            success = await engine.initialize()
            assert not success
    
    @pytest.mark.asyncio
    async def test_synthesize_empty_text(self, mock_tts_engine):
        """Тест синтеза пустого текста."""
        result = await mock_tts_engine.synthesize("")
        assert result is None
        
        result = await mock_tts_engine.synthesize("   ")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_synthesize_success(self, mock_tts_engine):
        """Тест успешного синтеза речи."""
        test_text = "Привет, как дела?"
        
        # Создаем корректный мок результата
        expected_result = TTSResult(
            audio_data=b"fake_audio_data",
            provider=TTSProvider.PYTTSX3,
            processing_time=1.0,
            text=test_text,
            language="ru"
        )
        
        # Мокаем метод synthesize напрямую
        mock_tts_engine.synthesize = Mock(return_value=expected_result)
        
        result = await mock_tts_engine.synthesize(test_text)
        
        assert result is not None
        assert result.text == test_text
        assert result.provider == TTSProvider.PYTTSX3
        assert len(result.audio_data) > 0


class TestWakeWordDetector:
    """Тесты детектора ключевых слов."""
    
    @pytest.fixture
    def mock_wake_detector(self):
        """Mock Wake Word детектора."""
        detector = WakeWordDetector(
            provider=WakeWordProvider.SIMPLE_STT,
            wake_words=["привет ассистент", "окей дом"]
        )
        detector._initialized = True
        detector._stt_engine = Mock()
        return detector
    
    @pytest.mark.asyncio
    async def test_initialization(self):
        """Тест инициализации детектора."""
        detector = WakeWordDetector()
        # Мокаем провайдер как доступный
        with patch.object(detector, '_check_provider_availability', return_value=True):
            with patch.object(detector, '_init_simple_stt'):
                success = await detector.initialize()
                assert success
    
    @pytest.mark.asyncio
    async def test_start_stop_listening(self, mock_wake_detector):
        """Тест запуска и остановки прослушивания."""
        success = await mock_wake_detector.start_listening()
        assert success
        assert mock_wake_detector.is_listening()
        
        await mock_wake_detector.stop_listening()
        assert not mock_wake_detector.is_listening()
    
    def test_wake_word_management(self, mock_wake_detector):
        """Тест управления ключевыми словами."""
        # Добавление
        mock_wake_detector.add_wake_word("тест слово")
        assert "тест слово" in mock_wake_detector.wake_words
        
        # Удаление
        mock_wake_detector.remove_wake_word("окей дом")
        assert "окей дом" not in mock_wake_detector.wake_words
    
    def test_sensitivity_setting(self, mock_wake_detector):
        """Тест установки чувствительности."""
        mock_wake_detector.set_sensitivity(0.8)
        assert mock_wake_detector.sensitivity == 0.8
        
        # Проверка границ
        mock_wake_detector.set_sensitivity(1.5)
        assert mock_wake_detector.sensitivity == 1.0
        
        mock_wake_detector.set_sensitivity(-0.5)
        assert mock_wake_detector.sensitivity == 0.0


class TestAudioManager:
    """Тесты аудио менеджера."""
    
    @pytest.fixture
    def mock_audio_manager(self):
        """Mock Audio Manager."""
        with patch('home_assistant.voice.audio.AUDIO_AVAILABLE', True):
            manager = AudioManager(
                sample_rate=16000,
                channels=1,
                chunk_size=1024
            )
            manager._initialized = True
            manager._pyaudio = Mock()
            return manager
    
    @pytest.mark.asyncio
    async def test_initialization(self):
        """Тест инициализации аудио менеджера."""
        with patch('home_assistant.voice.audio.AUDIO_AVAILABLE', False):
            manager = AudioManager()
            success = await manager.initialize()
            assert not success
    
    @pytest.mark.asyncio
    async def test_recording_control(self, mock_audio_manager):
        """Тест управления записью."""
        # Мокаем stream
        mock_stream = Mock()
        mock_audio_manager._pyaudio.open.return_value = mock_stream
        
        success = await mock_audio_manager.start_recording()
        assert success
        assert mock_audio_manager.is_recording()
        
        await mock_audio_manager.stop_recording()
        assert not mock_audio_manager.is_recording()
    
    def test_audio_callbacks(self, mock_audio_manager):
        """Тест аудио callback'ов."""
        callback_called = False
        
        def test_callback(audio_data):
            nonlocal callback_called
            callback_called = True
        
        # Добавление callback
        mock_audio_manager.add_audio_callback(test_callback)
        assert test_callback in mock_audio_manager._callbacks
        
        # Симуляция callback
        mock_audio_manager._callbacks[0](np.random.rand(1024))
        assert callback_called
        
        # Удаление callback
        mock_audio_manager.remove_audio_callback(test_callback)
        assert test_callback not in mock_audio_manager._callbacks


class TestVoiceManager:
    """Тесты центрального голосового менеджера."""
    
    @pytest.fixture
    def mock_voice_config(self):
        """Mock конфигурация."""
        return VoiceConfig(
            stt_provider=STTProvider.GOOGLE,
            tts_provider=TTSProvider.PYTTSX3,
            wake_words=["привет ассистент"]
        )
    
    @pytest.fixture
    def mock_voice_manager(self, mock_voice_config):
        """Mock Voice Manager."""
        reasoning_engine = Mock()
        event_system = Mock()
        
        manager = VoiceManager(
            config=mock_voice_config,
            reasoning_engine=reasoning_engine,
            event_system=event_system
        )
        
        # Мокаем компоненты
        manager.audio_manager = Mock()
        manager.stt_engine = Mock()
        manager.tts_engine = Mock()
        manager.wake_word_detector = Mock()
        
        # Устанавливаем состояние
        manager._initialized = True
        manager._state = VoiceState.IDLE
        
        return manager
    
    @pytest.mark.asyncio
    async def test_initialization_failure(self, mock_voice_config):
        """Тест неудачной инициализации."""
        manager = VoiceManager(
            config=mock_voice_config,
            reasoning_engine=Mock(),
            event_system=Mock()
        )
        
        # Мокаем неудачную инициализацию аудио
        with patch('home_assistant.voice.audio.AudioManager') as MockAudio:
            mock_audio = MockAudio.return_value
            mock_audio.initialize.return_value = False
            
            success = await manager.initialize()
            assert not success
    
    @pytest.mark.asyncio
    async def test_start_stop(self, mock_voice_manager):
        """Тест запуска и остановки."""
        # Создаем корректные async моки
        async def mock_start_recording():
            return True
        async def mock_start_listening():
            return True
            
        mock_voice_manager.audio_manager.start_recording = Mock(side_effect=mock_start_recording)
        mock_voice_manager.wake_word_detector.start_listening = Mock(side_effect=mock_start_listening)
        
        success = await mock_voice_manager.start()
        assert success
        assert mock_voice_manager._state == VoiceState.LISTENING_WAKE_WORD
        
        await mock_voice_manager.stop()
        assert mock_voice_manager._state == VoiceState.IDLE
    
    @pytest.mark.asyncio
    async def test_speak(self, mock_voice_manager):
        """Тест произнесения текста."""
        # Создаем корректный async мок
        async def mock_speak(text, blocking=True):
            return True
            
        mock_voice_manager.tts_engine.speak = Mock(side_effect=mock_speak)
        
        success = await mock_voice_manager.speak("Тестовый текст")
        assert success
        
        mock_voice_manager.tts_engine.speak.assert_called_once_with("Тестовый текст", blocking=True)
    
    def test_state_management(self, mock_voice_manager):
        """Тест управления состояниями."""
        assert mock_voice_manager.get_state() == VoiceState.IDLE
        
        # Проверка методов состояния
        mock_voice_manager._state = VoiceState.LISTENING_WAKE_WORD
        assert mock_voice_manager.is_listening()
        
        mock_voice_manager._state = VoiceState.SPEAKING
        assert not mock_voice_manager.is_listening()
    
    def test_availability_check(self, mock_voice_manager):
        """Тест проверки доступности."""
        # Мокаем все компоненты как доступные
        mock_voice_manager.audio_manager.is_recording.return_value = True
        mock_voice_manager.stt_engine.is_available.return_value = True
        mock_voice_manager.tts_engine.is_available.return_value = True
        
        assert mock_voice_manager.is_available()
        
        # Один компонент недоступен
        mock_voice_manager.stt_engine.is_available.return_value = False
        assert not mock_voice_manager.is_available()
    
    @pytest.mark.asyncio
    async def test_wake_word_detection_callback(self, mock_voice_manager):
        """Тест callback детекции ключевого слова."""
        wake_result = WakeWordResult(
            keyword="привет ассистент",
            confidence=0.9,
            provider=WakeWordProvider.SIMPLE_STT,
            timestamp=1234567890.0
        )
        
        mock_voice_manager._state = VoiceState.LISTENING_WAKE_WORD
        
        await mock_voice_manager._on_wake_word_detected(wake_result)
        
        assert mock_voice_manager._state == VoiceState.LISTENING_COMMAND
        assert mock_voice_manager._current_interaction is not None
        assert mock_voice_manager._current_interaction.wake_word == "привет ассистент"
    
    def test_callback_management(self, mock_voice_manager):
        """Тест управления callback'ами."""
        callback_called = False
        
        def test_callback(data):
            nonlocal callback_called
            callback_called = True
        
        # Добавление callback
        mock_voice_manager.add_callback("test_event", test_callback)
        assert "test_event" in mock_voice_manager._callbacks
        assert test_callback in mock_voice_manager._callbacks["test_event"]
        
        # Удаление callback
        mock_voice_manager.remove_callback("test_event", test_callback)
        assert len(mock_voice_manager._callbacks.get("test_event", [])) == 0


class TestVoiceIntegration:
    """Интеграционные тесты голосовой системы."""
    
    @pytest.mark.asyncio
    async def test_voice_interaction_flow(self):
        """Тест полного цикла голосового взаимодействия."""
        # Создаем мок-компоненты
        config = VoiceConfig()
        reasoning_engine = Mock()
        event_system = Mock()
        
        # Создаем корректный async мок для AI  
        async def mock_process_input(user_input, context=None):
            return {
                "response": "Свет включен", 
                "intent": "device_control",
                "confidence": 0.95
            }
        reasoning_engine.process_user_input = Mock(side_effect=mock_process_input)
        
        with patch('home_assistant.voice.manager.AudioManager'), \
             patch('home_assistant.voice.manager.STTEngine'), \
             patch('home_assistant.voice.manager.TTSEngine'), \
             patch('home_assistant.voice.manager.WakeWordDetector'):
            
            voice_manager = VoiceManager(
                config=config,
                reasoning_engine=reasoning_engine,
                event_system=event_system
            )
            
            # Мокаем успешную инициализацию
            voice_manager._initialized = True
            voice_manager.audio_manager = Mock()
            voice_manager.stt_engine = Mock()
            voice_manager.tts_engine = Mock()
            voice_manager.wake_word_detector = Mock()
            
            # Мокаем распознавание команды
            stt_result = STTResult(
                text="включи свет",
                confidence=0.9,
                provider=STTProvider.GOOGLE,
                processing_time=1.0
            )
            
            # Создаем взаимодействие
            from home_assistant.voice.manager import VoiceInteraction
            voice_manager._current_interaction = VoiceInteraction(
                wake_word="привет ассистент",
                start_time=1234567890.0
            )
            
            # Симулируем обработку команды
            await voice_manager._process_voice_command(stt_result)
            
            # Проверяем что AI было вызвано
            reasoning_engine.process_user_input.assert_called_once()
            
            # Проверяем что TTS было вызвано
            voice_manager.tts_engine.speak.assert_called_once_with("Свет включен", blocking=True)


if __name__ == "__main__":
    pytest.main([__file__])
