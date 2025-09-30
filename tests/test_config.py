"""Тесты для модуля конфигурации."""

import pytest
from pathlib import Path
import tempfile
import yaml

from home_assistant.core.config import HomeAssistantConfig, DatabaseConfig, AIConfig


class TestHomeAssistantConfig:
    """Тесты для класса HomeAssistantConfig."""
    
    def test_default_config(self):
        """Тест создания конфигурации по умолчанию."""
        config = HomeAssistantConfig()
        
        assert config.debug is False
        assert config.log_level == "INFO"
        assert config.data_dir == Path("./data")
        assert config.config_dir == Path("./config")
        
        # Проверка подконфигураций
        assert isinstance(config.database, DatabaseConfig)
        assert isinstance(config.ai, AIConfig)
    
    def test_load_from_file(self):
        """Тест загрузки конфигурации из файла."""
        config_data = {
            "debug": True,
            "log_level": "DEBUG",
            "database": {
                "type": "sqlite",
                "url": "sqlite:///test.db"
            },
            "ai": {
                "openai_model": "gpt-3.5-turbo",
                "temperature": 0.5
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            config_path = Path(f.name)
        
        try:
            config = HomeAssistantConfig.load_from_file(config_path)
            
            assert config.debug is True
            assert config.log_level == "DEBUG"
            assert config.database.url == "sqlite:///test.db"
            assert config.ai.openai_model == "gpt-3.5-turbo"
            assert config.ai.temperature == 0.5
            
        finally:
            config_path.unlink()
    
    def test_save_to_file(self):
        """Тест сохранения конфигурации в файл."""
        config = HomeAssistantConfig()
        config.debug = True
        config.log_level = "DEBUG"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            config_path = Path(f.name)
        
        try:
            config.save_to_file(config_path)
            
            # Проверяем, что файл создан и содержит правильные данные
            assert config_path.exists()
            
            with open(config_path, 'r') as f:
                saved_data = yaml.safe_load(f)
            
            assert saved_data['debug'] is True
            assert saved_data['log_level'] == "DEBUG"
            
        finally:
            config_path.unlink()
    
    def test_privacy_mode_check(self):
        """Тест проверки режима приватности."""
        config = HomeAssistantConfig()
        assert config.is_privacy_mode() is False
        
        config.privacy.enabled = True
        assert config.is_privacy_mode() is True
    
    def test_active_protocols(self):
        """Тест получения активных протоколов."""
        config = HomeAssistantConfig()
        protocols = config.get_active_protocols()
        
        assert "wifi" in protocols
        assert "bluetooth" in protocols
        assert "mqtt" in protocols
    
    def test_database_url_sqlite(self):
        """Тест генерации URL для SQLite базы данных."""
        config = HomeAssistantConfig()
        config.data_dir = Path("/tmp/test")
        config.database.url = "sqlite:///home_assistant.db"
        
        db_url = config.get_database_url()
        assert db_url.startswith("sqlite:///")
        assert "home_assistant.db" in db_url


class TestDatabaseConfig:
    """Тесты для класса DatabaseConfig."""
    
    def test_default_values(self):
        """Тест значений по умолчанию."""
        config = DatabaseConfig()
        
        assert config.type == "sqlite"
        assert config.url == "sqlite:///./data/home_assistant.db"
        assert config.pool_size == 5
        assert config.echo is False


class TestAIConfig:
    """Тесты для класса AIConfig."""
    
    def test_default_values(self):
        """Тест значений по умолчанию."""
        config = AIConfig()
        
        assert config.openai_api_key is None
        assert config.openai_model == "gpt-4"
        assert config.local_llm_enabled is True
        assert config.local_llm_model == "llama2:7b"
        assert config.local_llm_url == "http://localhost:11434"
        assert config.max_reasoning_steps == 10
        assert config.temperature == 0.7
        assert config.max_tokens == 2048
