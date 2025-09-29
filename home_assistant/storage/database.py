"""
Модуль управления базой данных Home Assistant AI.

Реализует подключение к SQLite базе данных, модели данных и основные операции.
"""

import asyncio
from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path

from sqlalchemy import create_engine, Column, String, Integer, DateTime, Boolean, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
import aiosqlite
import structlog

from ..core.config import HomeAssistantConfig

logger = structlog.get_logger(__name__)

Base = declarative_base()


class DeviceModel(Base):
    """Модель устройства в базе данных."""
    
    __tablename__ = "devices"
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    device_type = Column(String, nullable=False)
    manufacturer = Column(String, nullable=False)
    model = Column(String, nullable=False)
    version = Column(String)
    protocol = Column(String, nullable=False)
    
    # Сетевая информация
    ip_address = Column(String)
    mac_address = Column(String)
    
    # Метаданные
    room = Column(String)
    description = Column(Text)
    tags = Column(JSON)  # Список тегов
    
    # Технические характеристики
    capabilities = Column(JSON)  # Список возможностей
    
    # Состояние
    state = Column(String, default="offline")
    last_seen = Column(DateTime)
    battery_level = Column(Integer)
    signal_strength = Column(Integer)
    
    # Технические поля
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class DeviceStateModel(Base):
    """Модель состояния устройства."""
    
    __tablename__ = "device_states"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    device_id = Column(String, nullable=False)
    attribute_name = Column(String, nullable=False)
    attribute_value = Column(JSON)  # Значение атрибута
    timestamp = Column(DateTime, default=datetime.utcnow)


class ConversationModel(Base):
    """Модель разговоров с AI ассистентом."""
    
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, nullable=False)
    message_type = Column(String, nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    meta_data = Column(JSON)  # Дополнительные данные
    timestamp = Column(DateTime, default=datetime.utcnow)


class IntegrationModel(Base):
    """Модель внешних интеграций."""
    
    __tablename__ = "integrations"
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)  # spotify, weather, etc
    enabled = Column(Boolean, default=True)
    config = Column(JSON)  # Конфигурация интеграции
    credentials = Column(JSON)  # Зашифрованные учетные данные
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class EventLogModel(Base):
    """Модель логов событий системы."""
    
    __tablename__ = "event_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    event_type = Column(String, nullable=False)
    source = Column(String)
    target = Column(String)
    data = Column(JSON)
    timestamp = Column(DateTime, default=datetime.utcnow)


class DatabaseManager:
    """Менеджер базы данных."""
    
    def __init__(self, config: HomeAssistantConfig):
        """
        Инициализация менеджера базы данных.
        
        Args:
            config: Конфигурация системы
        """
        self.config = config
        self._engine = None
        self._session_factory = None
        self._logger = structlog.get_logger(__name__)
    
    async def initialize(self) -> None:
        """Инициализация базы данных."""
        try:
            # Создание директории для базы данных
            db_url = self.config.get_database_url()
            
            if db_url.startswith("sqlite"):
                db_path = db_url.replace("sqlite:///", "")
                Path(db_path).parent.mkdir(parents=True, exist_ok=True)
            
            # Создание движка (синхронного для создания таблиц)
            sync_engine = create_engine(db_url)
            Base.metadata.create_all(sync_engine)
            
            self._logger.info("Database initialized successfully", db_url=db_url)
            
        except Exception as e:
            self._logger.error("Failed to initialize database", error=str(e))
            raise
    
    async def get_session(self) -> AsyncSession:
        """Получение сессии базы данных."""
        # Для простоты используем синхронную сессию
        # В продакшене следует использовать async
        from sqlalchemy.orm import Session
        
        sync_engine = create_engine(self.config.get_database_url())
        session = Session(sync_engine)
        return session
    
    async def save_device(self, device_data: Dict[str, Any]) -> bool:
        """
        Сохранение устройства в базу данных.
        
        Args:
            device_data: Данные устройства
            
        Returns:
            True если сохранение успешно
        """
        try:
            session = await self.get_session()
            
            # Проверяем существование устройства
            existing = session.query(DeviceModel).filter_by(id=device_data["id"]).first()
            
            if existing:
                # Обновляем существующее устройство
                for key, value in device_data.items():
                    if hasattr(existing, key):
                        setattr(existing, key, value)
                existing.updated_at = datetime.utcnow()
            else:
                # Создаем новое устройство
                device = DeviceModel(**device_data)
                session.add(device)
            
            session.commit()
            session.close()
            
            self._logger.debug("Device saved", device_id=device_data["id"])
            return True
            
        except Exception as e:
            self._logger.error("Failed to save device", error=str(e))
            return False
    
    async def get_device(self, device_id: str) -> Optional[Dict[str, Any]]:
        """
        Получение устройства по ID.
        
        Args:
            device_id: Идентификатор устройства
            
        Returns:
            Данные устройства или None
        """
        try:
            session = await self.get_session()
            device = session.query(DeviceModel).filter_by(id=device_id).first()
            session.close()
            
            if device:
                return {
                    "id": device.id,
                    "name": device.name,
                    "device_type": device.device_type,
                    "manufacturer": device.manufacturer,
                    "model": device.model,
                    "version": device.version,
                    "protocol": device.protocol,
                    "ip_address": device.ip_address,
                    "mac_address": device.mac_address,
                    "room": device.room,
                    "description": device.description,
                    "tags": device.tags or [],
                    "capabilities": device.capabilities or [],
                    "state": device.state,
                    "last_seen": device.last_seen,
                    "battery_level": device.battery_level,
                    "signal_strength": device.signal_strength,
                    "created_at": device.created_at,
                    "updated_at": device.updated_at
                }
            return None
            
        except Exception as e:
            self._logger.error("Failed to get device", device_id=device_id, error=str(e))
            return None
    
    async def get_all_devices(self) -> List[Dict[str, Any]]:
        """
        Получение всех устройств.
        
        Returns:
            Список устройств
        """
        try:
            session = await self.get_session()
            devices = session.query(DeviceModel).all()
            session.close()
            
            result = []
            for device in devices:
                result.append({
                    "id": device.id,
                    "name": device.name,
                    "device_type": device.device_type,
                    "manufacturer": device.manufacturer,
                    "model": device.model,
                    "protocol": device.protocol,
                    "room": device.room,
                    "state": device.state,
                    "last_seen": device.last_seen
                })
            
            return result
            
        except Exception as e:
            self._logger.error("Failed to get all devices", error=str(e))
            return []
    
    async def save_device_state(self, device_id: str, attribute_name: str, 
                               attribute_value: Any) -> bool:
        """
        Сохранение состояния устройства.
        
        Args:
            device_id: Идентификатор устройства
            attribute_name: Имя атрибута
            attribute_value: Значение атрибута
            
        Returns:
            True если сохранение успешно
        """
        try:
            session = await self.get_session()
            
            state = DeviceStateModel(
                device_id=device_id,
                attribute_name=attribute_name,
                attribute_value=attribute_value
            )
            session.add(state)
            session.commit()
            session.close()
            
            return True
            
        except Exception as e:
            self._logger.error("Failed to save device state", error=str(e))
            return False
    
    async def save_conversation(self, session_id: str, message_type: str, 
                               content: str, metadata: Optional[Dict] = None) -> bool:
        """
        Сохранение сообщения разговора.
        
        Args:
            session_id: Идентификатор сессии
            message_type: Тип сообщения (user, assistant, system)
            content: Содержимое сообщения
            metadata: Дополнительные данные
            
        Returns:
            True если сохранение успешно
        """
        try:
            session = await self.get_session()
            
            conversation = ConversationModel(
                session_id=session_id,
                message_type=message_type,
                content=content,
                meta_data=metadata or {}
            )
            session.add(conversation)
            session.commit()
            session.close()
            
            return True
            
        except Exception as e:
            self._logger.error("Failed to save conversation", error=str(e))
            return False
    
    async def get_conversation_history(self, session_id: str, 
                                      limit: int = 50) -> List[Dict[str, Any]]:
        """
        Получение истории разговора.
        
        Args:
            session_id: Идентификатор сессии
            limit: Максимальное количество сообщений
            
        Returns:
            История разговора
        """
        try:
            session = await self.get_session()
            
            messages = session.query(ConversationModel)\
                             .filter_by(session_id=session_id)\
                             .order_by(ConversationModel.timestamp.desc())\
                             .limit(limit)\
                             .all()
            
            session.close()
            
            result = []
            for msg in reversed(messages):  # Возвращаем в хронологическом порядке
                result.append({
                    "message_type": msg.message_type,
                    "content": msg.content,
                    "metadata": msg.meta_data,
                    "timestamp": msg.timestamp
                })
            
            return result
            
        except Exception as e:
            self._logger.error("Failed to get conversation history", error=str(e))
            return []
    
    async def save_integration(self, integration_data: Dict[str, Any]) -> bool:
        """
        Сохранение интеграции.
        
        Args:
            integration_data: Данные интеграции
            
        Returns:
            True если сохранение успешно
        """
        try:
            session = await self.get_session()
            
            existing = session.query(IntegrationModel).filter_by(id=integration_data["id"]).first()
            
            if existing:
                for key, value in integration_data.items():
                    if hasattr(existing, key):
                        setattr(existing, key, value)
                existing.updated_at = datetime.utcnow()
            else:
                integration = IntegrationModel(**integration_data)
                session.add(integration)
            
            session.commit()
            session.close()
            
            return True
            
        except Exception as e:
            self._logger.error("Failed to save integration", error=str(e))
            return False
    
    async def get_enabled_integrations(self) -> List[Dict[str, Any]]:
        """
        Получение активных интеграций.
        
        Returns:
            Список активных интеграций
        """
        try:
            session = await self.get_session()
            
            integrations = session.query(IntegrationModel)\
                                 .filter_by(enabled=True)\
                                 .all()
            
            session.close()
            
            result = []
            for integration in integrations:
                result.append({
                    "id": integration.id,
                    "name": integration.name,
                    "type": integration.type,
                    "config": integration.config,
                    "credentials": integration.credentials
                })
            
            return result
            
        except Exception as e:
            self._logger.error("Failed to get integrations", error=str(e))
            return []
    
    async def log_event(self, event_type: str, source: Optional[str] = None,
                       target: Optional[str] = None, data: Optional[Dict] = None) -> bool:
        """
        Логирование события.
        
        Args:
            event_type: Тип события
            source: Источник события
            target: Цель события
            data: Данные события
            
        Returns:
            True если логирование успешно
        """
        try:
            session = await self.get_session()
            
            event_log = EventLogModel(
                event_type=event_type,
                source=source,
                target=target,
                data=data or {}
            )
            session.add(event_log)
            session.commit()
            session.close()
            
            return True
            
        except Exception as e:
            self._logger.error("Failed to log event", error=str(e))
            return False
    
    async def save_integration_settings(self, integration_type: str, settings: Dict[str, Any]) -> bool:
        """
        Сохранение настроек интеграции.
        
        Args:
            integration_type: Тип интеграции (spotify, wifi, etc)
            settings: Настройки для сохранения
            
        Returns:
            True если сохранение успешно
        """
        try:
            session = await self.get_session()
            
            # Используем тип интеграции как ID
            integration_data = {
                "id": integration_type,
                "name": integration_type.title(),
                "type": integration_type,
                "enabled": True,
                "config": settings,
                "credentials": settings.get("credentials", {})
            }
            
            existing = session.query(IntegrationModel).filter_by(id=integration_type).first()
            
            if existing:
                # Обновляем существующую интеграцию
                existing.config = settings
                existing.credentials = settings.get("credentials", {})
                existing.updated_at = datetime.utcnow()
            else:
                # Создаем новую интеграцию
                integration = IntegrationModel(**integration_data)
                session.add(integration)
            
            session.commit()
            session.close()
            
            self._logger.debug("Integration settings saved", 
                             integration_type=integration_type)
            return True
            
        except Exception as e:
            self._logger.error("Failed to save integration settings", 
                             integration_type=integration_type, error=str(e))
            return False
    
    async def get_integration_settings(self, integration_type: str) -> Optional[Dict[str, Any]]:
        """
        Получение настроек интеграции.
        
        Args:
            integration_type: Тип интеграции
            
        Returns:
            Настройки интеграции или None
        """
        try:
            session = await self.get_session()
            integration = session.query(IntegrationModel).filter_by(id=integration_type).first()
            session.close()
            
            if integration:
                return {
                    "config": integration.config or {},
                    "credentials": integration.credentials or {},
                    "enabled": integration.enabled,
                    "created_at": integration.created_at,
                    "updated_at": integration.updated_at
                }
            return None
            
        except Exception as e:
            self._logger.error("Failed to get integration settings", 
                             integration_type=integration_type, error=str(e))
            return None
    
    async def remove_integration_settings(self, integration_type: str) -> bool:
        """
        Удаление настроек интеграции.
        
        Args:
            integration_type: Тип интеграции
            
        Returns:
            True если удаление успешно
        """
        try:
            session = await self.get_session()
            integration = session.query(IntegrationModel).filter_by(id=integration_type).first()
            
            if integration:
                session.delete(integration)
                session.commit()
                
            session.close()
            
            self._logger.debug("Integration settings removed", 
                             integration_type=integration_type)
            return True
            
        except Exception as e:
            self._logger.error("Failed to remove integration settings", 
                             integration_type=integration_type, error=str(e))
            return False
    
    async def get_all_integrations(self) -> List[Dict[str, Any]]:
        """
        Получение всех интеграций.
        
        Returns:
            Список всех интеграций
        """
        try:
            session = await self.get_session()
            integrations = session.query(IntegrationModel).all()
            session.close()
            
            result = []
            for integration in integrations:
                result.append({
                    "id": integration.id,
                    "name": integration.name,
                    "type": integration.type,
                    "enabled": integration.enabled,
                    "config": integration.config or {},
                    "has_credentials": bool(integration.credentials),
                    "created_at": integration.created_at,
                    "updated_at": integration.updated_at
                })
            
            return result
            
        except Exception as e:
            self._logger.error("Failed to get all integrations", error=str(e))
            return []
    
    async def toggle_integration(self, integration_type: str) -> bool:
        """
        Переключение состояния интеграции (включить/выключить).
        
        Args:
            integration_type: Тип интеграции
            
        Returns:
            True если переключение успешно
        """
        try:
            session = await self.get_session()
            integration = session.query(IntegrationModel).filter_by(id=integration_type).first()
            
            if integration:
                integration.enabled = not integration.enabled
                integration.updated_at = datetime.utcnow()
                session.commit()
                
            session.close()
            
            self._logger.debug("Integration toggled", 
                             integration_type=integration_type,
                             enabled=integration.enabled if integration else False)
            return True
            
        except Exception as e:
            self._logger.error("Failed to toggle integration", 
                             integration_type=integration_type, error=str(e))
            return False