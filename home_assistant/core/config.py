"""
Конфигурация системы Home Assistant AI.

Этот модуль отвечает за загрузку и валидацию конфигурации,
включая настройки устройств, AI модуля, протоколов связи и режимов приватности.
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from pydantic import BaseModel, Field, validator
from pydantic_settings import BaseSettings


class DatabaseConfig(BaseModel):
    """Конфигурация локальной базы данных."""
    
    type: str = "sqlite"
    url: str = "sqlite:///./data/home_assistant.db"
    pool_size: int = 5
    echo: bool = False


class AIConfig(BaseModel):
    """Конфигурация AI модуля."""
    
    # Облачные LLM
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4"
    
    # Локальные LLM
    local_llm_enabled: bool = True
    local_llm_model: str = "llama2:7b"  # Ollama model
    local_llm_url: str = "http://localhost:11434"
    
    # Reasoning settings
    max_reasoning_steps: int = 10
    temperature: float = 0.7
    max_tokens: int = 2048


class ProtocolConfig(BaseModel):
    """Конфигурация протоколов связи."""
    
    enabled: List[str] = ["wifi", "bluetooth", "mqtt"]
    
    # WiFi settings
    wifi_scan_interval: int = 30
    
    # Bluetooth settings
    bluetooth_scan_interval: int = 10
    bluetooth_discovery_timeout: int = 30
    
    # MQTT settings
    mqtt_broker: str = "localhost"
    mqtt_port: int = 1883
    mqtt_username: Optional[str] = None
    mqtt_password: Optional[str] = None
    mqtt_topic_prefix: str = "homeassistant"
    
    # Zigbee settings (optional)
    zigbee_device: Optional[str] = None  # e.g., "/dev/ttyUSB0"
    zigbee_baudrate: int = 115200
    
    # Z-Wave settings (optional)
    zwave_device: Optional[str] = None  # e.g., "/dev/ttyACM0"


class VoiceConfig(BaseModel):
    """Конфигурация голосового управления."""
    
    enabled: bool = True
    
    # Speech-to-Text
    stt_engine: str = "google"  # google, whisper, vosk
    stt_language: str = "ru-RU"
    
    # Text-to-Speech
    tts_engine: str = "pyttsx3"  # pyttsx3, google, festival
    tts_language: str = "ru"
    tts_voice_rate: int = 200
    
    # Wake word
    wake_word: str = "Hey Assistant"
    wake_word_sensitivity: float = 0.7
    
    # Audio settings
    microphone_index: Optional[int] = None
    sample_rate: int = 16000
    channels: int = 1


class APIConfig(BaseModel):
    """Конфигурация REST API."""
    
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = False
    
    # Security
    secret_key: str = "your-secret-key-change-this"
    access_token_expire_minutes: int = 30
    
    # CORS
    cors_origins: List[str] = ["*"]
    cors_credentials: bool = True
    cors_methods: List[str] = ["*"]
    cors_headers: List[str] = ["*"]


class PrivacyConfig(BaseModel):
    """Конфигурация режимов приватности."""
    
    enabled: bool = False
    
    # Локальный режим
    force_local_processing: bool = False
    disable_cloud_services: bool = False
    disable_external_apis: bool = False
    
    # Шифрование данных
    encrypt_local_data: bool = True
    encryption_key: Optional[str] = None
    
    # Логирование
    disable_usage_analytics: bool = True
    anonymize_logs: bool = True


class HomeAssistantConfig(BaseSettings):
    """Основная конфигурация Home Assistant AI."""
    
    # Основные настройки
    debug: bool = False
    log_level: str = "INFO"
    data_dir: Path = Path("./data")
    config_dir: Path = Path("./config")
    
    # Модули конфигурации
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    ai: AIConfig = Field(default_factory=AIConfig)
    protocols: ProtocolConfig = Field(default_factory=ProtocolConfig)
    voice: VoiceConfig = Field(default_factory=VoiceConfig)
    api: APIConfig = Field(default_factory=APIConfig)
    privacy: PrivacyConfig = Field(default_factory=PrivacyConfig)
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        env_nested_delimiter = "__"
    
    @validator("data_dir", "config_dir", pre=True)
    def create_directories(cls, v: Path) -> Path:
        """Создание директорий если они не существуют."""
        if isinstance(v, str):
            v = Path(v)
        v.mkdir(parents=True, exist_ok=True)
        return v
    
    @classmethod
    def load_from_file(cls, config_path: Optional[Path] = None) -> "HomeAssistantConfig":
        """
        Загрузка конфигурации из YAML файла.
        
        Args:
            config_path: Путь к файлу конфигурации
            
        Returns:
            Экземпляр HomeAssistantConfig
        """
        if config_path is None:
            config_path = Path("config/config.yaml")
        
        if not config_path.exists():
            # Создаем базовую конфигурацию
            config = cls()
            config.save_to_file(config_path)
            return config
        
        with open(config_path, "r", encoding="utf-8") as f:
            yaml_data = yaml.safe_load(f)
        
        return cls(**yaml_data)
    
    def save_to_file(self, config_path: Path) -> None:
        """
        Сохранение конфигурации в YAML файл.
        
        Args:
            config_path: Путь к файлу конфигурации
        """
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_path, "w", encoding="utf-8") as f:
            # Конвертируем в словарь и заменяем Path объекты на строки
            config_dict = self.model_dump()
            
            def convert_paths(obj):
                if isinstance(obj, dict):
                    return {k: convert_paths(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [convert_paths(item) for item in obj]
                elif isinstance(obj, Path):
                    return str(obj)
                else:
                    return obj
            
            config_dict = convert_paths(config_dict)
            
            yaml.dump(
                config_dict,
                f,
                default_flow_style=False,
                allow_unicode=True,
                sort_keys=False
            )
    
    def is_privacy_mode(self) -> bool:
        """Проверка активности режима приватности."""
        return self.privacy.enabled
    
    def get_active_protocols(self) -> List[str]:
        """Получение списка активных протоколов связи."""
        return self.protocols.enabled
    
    def get_database_url(self) -> str:
        """Получение URL базы данных."""
        if self.database.url.startswith("sqlite"):
            # Убеждаемся, что путь к SQLite базе абсолютный
            db_path = self.database.url.replace("sqlite:///", "")
            if not Path(db_path).is_absolute():
                db_path = self.data_dir / db_path
            return f"sqlite:///{db_path}"
        return self.database.url