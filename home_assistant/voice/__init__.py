"""
Голосовая система Home Assistant AI.

Обеспечивает:
- Распознавание речи (Speech-to-Text)
- Синтез речи (Text-to-Speech)
- Детекция ключевых слов (Wake Word Detection)
- Управление аудио устройствами
- Интеграция с AI reasoning
"""

from .audio import AudioManager
from .stt import STTEngine, STTProvider, STTResult
from .tts import TTSEngine, TTSProvider, TTSResult
from .wake_word import WakeWordDetector, WakeWordProvider, WakeWordResult
from .manager import VoiceManager, VoiceConfig, VoiceState

__all__ = [
    'AudioManager',
    'STTEngine', 'STTProvider', 'STTResult',
    'TTSEngine', 'TTSProvider', 'TTSResult',
    'WakeWordDetector', 'WakeWordProvider', 'WakeWordResult',
    'VoiceManager', 'VoiceConfig', 'VoiceState'
]