"""Audio Manager - управление аудио устройствами."""

import asyncio
from typing import Optional, List, Callable
from dataclasses import dataclass
import structlog

try:
    import numpy as np
    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False

logger = structlog.get_logger(__name__)


@dataclass
class AudioDevice:
    index: int
    name: str
    max_input_channels: int
    max_output_channels: int
    default_sample_rate: float
    is_input: bool
    is_output: bool


class AudioManager:
    def __init__(self, sample_rate: int = 16000, channels: int = 1, chunk_size: int = 1024,
                 input_device: Optional[int] = None, output_device: Optional[int] = None):
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk_size = chunk_size
        self.input_device = input_device
        self.output_device = output_device
        
        self._logger = structlog.get_logger(__name__)
        self._recording = False
        self._playing = False
        self._callbacks: List[Callable] = []
        
        if not AUDIO_AVAILABLE:
            self._logger.warning("Audio libraries not available")
    
    async def initialize(self) -> bool:
        if not AUDIO_AVAILABLE:
            self._logger.error("Audio libraries not installed")
            return False
        return True
    
    async def start_recording(self) -> bool:
        if not AUDIO_AVAILABLE:
            return False
        self._recording = True
        self._logger.info("Recording started")
        return True
    
    async def stop_recording(self) -> None:
        self._recording = False
        self._logger.info("Recording stopped")
    
    async def play_audio(self, audio_data: bytes, blocking: bool = True) -> bool:
        if not AUDIO_AVAILABLE:
            return False
        self._logger.info("Playing audio")
        return True
    
    def add_audio_callback(self, callback: Callable) -> None:
        self._callbacks.append(callback)
    
    def remove_audio_callback(self, callback: Callable) -> None:
        if callback in self._callbacks:
            self._callbacks.remove(callback)
    
    def is_recording(self) -> bool:
        return self._recording
    
    def is_playing(self) -> bool:
        return self._playing
    
    def get_audio_devices(self) -> List[AudioDevice]:
        return []
    
    async def cleanup(self) -> None:
        await self.stop_recording()
        self._logger.info("Audio manager cleanup completed")