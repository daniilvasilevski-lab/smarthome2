"""
Audio Manager - управление аудио устройствами и потоками.

Обеспечивает:
- Захват звука с микрофона
- Воспроизведение через динамики
- Управление аудио устройствами
- Обработка аудио потоков
"""

import asyncio
import threading
import queue
from typing import Optional, List, Callable, Any, AsyncGenerator
from dataclasses import dataclass
import numpy as np
import structlog

try:
    import sounddevice as sd
    import pyaudio
    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False
    sd = None
    pyaudio = None

logger = structlog.get_logger(__name__)


@dataclass
class AudioDevice:
    """Информация об аудио устройстве."""
    index: int
    name: str
    max_input_channels: int
    max_output_channels: int
    default_sample_rate: float
    is_input: bool
    is_output: bool


class AudioManager:
    """Менеджер аудио устройств и потоков."""
    
    def __init__(self, 
                 sample_rate: int = 16000,
                 channels: int = 1,
                 chunk_size: int = 1024,
                 input_device: Optional[int] = None,
                 output_device: Optional[int] = None):
        """
        Инициализация Audio Manager.
        
        Args:
            sample_rate: Частота дискретизации (Hz)
            channels: Количество каналов
            chunk_size: Размер буфера
            input_device: Индекс входного устройства
            output_device: Индекс выходного устройства
        """
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk_size = chunk_size
        self.input_device = input_device
        self.output_device = output_device
        
        self._logger = structlog.get_logger(__name__)
        self._recording = False
        self._playing = False
        self._audio_queue: queue.Queue = queue.Queue()
        self._callbacks: List[Callable[[np.ndarray], None]] = []
        
        # PyAudio instance
        self._pyaudio = None
        self._input_stream = None
        self._output_stream = None
        
        if not AUDIO_AVAILABLE:
            self._logger.warning("Audio libraries not available. Voice functions will be disabled.")
    
    async def initialize(self) -> bool:
        """Инициализация аудио системы."""
        if not AUDIO_AVAILABLE:
            self._logger.error("Audio libraries not installed")
            return False
        
        try:
            self._pyaudio = pyaudio.PyAudio()
            
            # Поиск устройств по умолчанию если не указаны
            if self.input_device is None:
                self.input_device = self._find_default_input_device()
            
            if self.output_device is None:
                self.output_device = self._find_default_output_device()
            
            self._logger.info("Audio system initialized",
                            input_device=self.input_device,
                            output_device=self.output_device,
                            sample_rate=self.sample_rate)
            
            return True
            
        except Exception as e:
            self._logger.error("Failed to initialize audio system", error=str(e))
            return False
    
    def _find_default_input_device(self) -> Optional[int]:
        """Поиск устройства ввода по умолчанию."""
        try:
            info = self._pyaudio.get_default_input_device_info()
            return int(info['index'])
        except Exception:
            # Поиск первого доступного входного устройства
            for i in range(self._pyaudio.get_device_count()):
                device_info = self._pyaudio.get_device_info_by_index(i)
                if device_info['maxInputChannels'] > 0:
                    return i
        return None
    
    def _find_default_output_device(self) -> Optional[int]:
        """Поиск устройства вывода по умолчанию."""
        try:
            info = self._pyaudio.get_default_output_device_info()
            return int(info['index'])
        except Exception:
            # Поиск первого доступного выходного устройства
            for i in range(self._pyaudio.get_device_count()):
                device_info = self._pyaudio.get_device_info_by_index(i)
                if device_info['maxOutputChannels'] > 0:
                    return i
        return None
    
    def get_audio_devices(self) -> List[AudioDevice]:
        """Получение списка доступных аудио устройств."""
        devices = []
        
        if not self._pyaudio:
            return devices
        
        try:
            for i in range(self._pyaudio.get_device_count()):
                info = self._pyaudio.get_device_info_by_index(i)
                
                device = AudioDevice(
                    index=i,
                    name=info['name'],
                    max_input_channels=info['maxInputChannels'],
                    max_output_channels=info['maxOutputChannels'],
                    default_sample_rate=info['defaultSampleRate'],
                    is_input=info['maxInputChannels'] > 0,
                    is_output=info['maxOutputChannels'] > 0
                )
                devices.append(device)
                
        except Exception as e:
            self._logger.error("Failed to enumerate audio devices", error=str(e))
        
        return devices
    
    def _audio_callback(self, in_data, frame_count, time_info, status):
        """Callback для обработки входящего аудио."""
        if status:
            self._logger.warning("Audio callback status", status=status)
        
        # Конвертируем в numpy array
        audio_data = np.frombuffer(in_data, dtype=np.float32)
        
        # Добавляем в очередь для обработки
        try:
            self._audio_queue.put_nowait(audio_data)
        except queue.Full:
            # Удаляем старые данные если очередь переполнена
            try:
                self._audio_queue.get_nowait()
                self._audio_queue.put_nowait(audio_data)
            except queue.Empty:
                pass
        
        # Вызываем зарегистрированные callback'и
        for callback in self._callbacks:
            try:
                callback(audio_data)
            except Exception as e:
                self._logger.error("Audio callback error", error=str(e))
        
        return (None, pyaudio.paContinue)
    
    async def start_recording(self) -> bool:
        """Начать запись с микрофона."""
        if not self._pyaudio or self._recording:
            return False
        
        try:
            self._input_stream = self._pyaudio.open(
                format=pyaudio.paFloat32,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                input_device_index=self.input_device,
                frames_per_buffer=self.chunk_size,
                stream_callback=self._audio_callback
            )
            
            self._input_stream.start_stream()
            self._recording = True
            
            self._logger.info("Recording started")
            return True
            
        except Exception as e:
            self._logger.error("Failed to start recording", error=str(e))
            return False
    
    async def stop_recording(self) -> None:
        """Остановить запись."""
        if self._input_stream:
            self._input_stream.stop_stream()
            self._input_stream.close()
            self._input_stream = None
        
        self._recording = False
        self._logger.info("Recording stopped")
    
    async def get_audio_chunk(self, timeout: float = 1.0) -> Optional[np.ndarray]:
        """Получить чанк аудио данных."""
        try:
            return self._audio_queue.get(timeout=timeout)
        except queue.Empty:
            return None
    
    async def record_audio_stream(self) -> AsyncGenerator[np.ndarray, None]:
        """Асинхронный генератор аудио потока."""
        while self._recording:
            chunk = await self.get_audio_chunk()
            if chunk is not None:
                yield chunk
            else:
                await asyncio.sleep(0.01)
    
    async def play_audio(self, audio_data: bytes, blocking: bool = True) -> bool:
        """Воспроизведение аудио."""
        if not self._pyaudio:
            return False
        
        try:
            # Открываем output stream если нужно
            if not self._output_stream:
                self._output_stream = self._pyaudio.open(
                    format=pyaudio.paFloat32,
                    channels=self.channels,
                    rate=self.sample_rate,
                    output=True,
                    output_device_index=self.output_device
                )
            
            self._playing = True
            
            # Воспроизводим аудио
            if blocking:
                self._output_stream.write(audio_data)
            else:
                # Асинхронное воспроизведение в отдельном потоке
                def play_thread():
                    self._output_stream.write(audio_data)
                    self._playing = False
                
                threading.Thread(target=play_thread, daemon=True).start()
            
            if blocking:
                self._playing = False
            
            return True
            
        except Exception as e:
            self._logger.error("Failed to play audio", error=str(e))
            self._playing = False
            return False
    
    def add_audio_callback(self, callback: Callable[[np.ndarray], None]) -> None:
        """Добавить callback для обработки аудио."""
        self._callbacks.append(callback)
    
    def remove_audio_callback(self, callback: Callable[[np.ndarray], None]) -> None:
        """Удалить audio callback."""
        if callback in self._callbacks:
            self._callbacks.remove(callback)
    
    def is_recording(self) -> bool:
        """Проверить состояние записи."""
        return self._recording
    
    def is_playing(self) -> bool:
        """Проверить состояние воспроизведения."""
        return self._playing
    
    async def cleanup(self) -> None:
        """Очистка ресурсов."""
        await self.stop_recording()
        
        if self._output_stream:
            self._output_stream.stop_stream()
            self._output_stream.close()
            self._output_stream = None
        
        if self._pyaudio:
            self._pyaudio.terminate()
            self._pyaudio = None
        
        self._logger.info("Audio manager cleanup completed")