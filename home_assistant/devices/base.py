"""
Базовые классы для устройств умного дома.

Этот модуль содержит базовые классы и интерфейсы для всех типов
устройств, поддерживаемых системой.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from enum import Enum
from datetime import datetime
import uuid

from pydantic import BaseModel, Field


class DeviceType(Enum):
    """Типы устройств умного дома."""
    
    # Освещение
    LIGHT = "light"
    DIMMER = "dimmer"
    LED_STRIP = "led_strip"
    
    # Климат
    THERMOSTAT = "thermostat"
    TEMPERATURE_SENSOR = "temperature_sensor"
    HUMIDITY_SENSOR = "humidity_sensor"
    AIR_CONDITIONER = "air_conditioner"
    
    # Безопасность
    DOOR_LOCK = "door_lock"
    MOTION_SENSOR = "motion_sensor"
    DOOR_SENSOR = "door_sensor"
    WINDOW_SENSOR = "window_sensor"
    SMOKE_DETECTOR = "smoke_detector"
    CAMERA = "camera"
    
    # Электроника
    SWITCH = "switch"
    OUTLET = "outlet"
    POWER_METER = "power_meter"
    
    # Мультимедиа
    SPEAKER = "speaker"
    TV = "tv"
    MEDIA_PLAYER = "media_player"
    
    # Бытовая техника
    WASHING_MACHINE = "washing_machine"
    DISHWASHER = "dishwasher"
    VACUUM_CLEANER = "vacuum_cleaner"
    
    # Другое
    UNKNOWN = "unknown"


class DeviceState(Enum):
    """Состояния устройства."""
    
    ONLINE = "online"
    OFFLINE = "offline"
    UNAVAILABLE = "unavailable"
    PAIRING = "pairing"
    ERROR = "error"


class Protocol(Enum):
    """Протоколы связи."""
    
    WIFI = "wifi"
    BLUETOOTH = "bluetooth"
    ZIGBEE = "zigbee"
    ZWAVE = "zwave"
    MQTT = "mqtt"
    HTTP = "http"
    COAP = "coap"


class DeviceCapability(BaseModel):
    """Возможности устройства."""
    
    name: str
    type: str
    writable: bool = False
    readable: bool = True
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    step: Optional[float] = None
    options: Optional[List[str]] = None
    unit: Optional[str] = None


class DeviceInfo(BaseModel):
    """Информация об устройстве."""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    device_type: DeviceType
    manufacturer: str
    model: str
    version: Optional[str] = None
    protocol: Protocol
    
    # Сетевая информация
    ip_address: Optional[str] = None
    mac_address: Optional[str] = None
    
    # Метаданные
    room: Optional[str] = None
    description: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    
    # Технические характеристики
    capabilities: List[DeviceCapability] = Field(default_factory=list)
    
    # Состояние
    state: DeviceState = DeviceState.OFFLINE
    last_seen: Optional[datetime] = None
    battery_level: Optional[int] = None
    signal_strength: Optional[int] = None
    
    class Config:
        use_enum_values = True


class BaseDevice(ABC):
    """Базовый класс для всех устройств."""
    
    def __init__(self, device_info: DeviceInfo):
        """
        Инициализация устройства.
        
        Args:
            device_info: Информация об устройстве
        """
        self.info = device_info
        self._attributes: Dict[str, Any] = {}
        self._is_connected = False
        
    @property
    def id(self) -> str:
        """Уникальный идентификатор устройства."""
        return self.info.id
    
    @property
    def name(self) -> str:
        """Имя устройства."""
        return self.info.name
    
    @property
    def device_type(self) -> DeviceType:
        """Тип устройства."""
        return self.info.device_type
    
    @property
    def state(self) -> DeviceState:
        """Текущее состояние устройства."""
        return self.info.state
    
    @property
    def is_connected(self) -> bool:
        """Проверка подключения устройства."""
        return self._is_connected and self.info.state == DeviceState.ONLINE
    
    @property
    def attributes(self) -> Dict[str, Any]:
        """Атрибуты устройства."""
        return self._attributes.copy()
    
    def get_attribute(self, name: str) -> Any:
        """
        Получение значения атрибута.
        
        Args:
            name: Имя атрибута
            
        Returns:
            Значение атрибута или None
        """
        return self._attributes.get(name)
    
    def set_attribute(self, name: str, value: Any) -> None:
        """
        Установка значения атрибута.
        
        Args:
            name: Имя атрибута
            value: Значение атрибута
        """
        self._attributes[name] = value
    
    @abstractmethod
    async def connect(self) -> bool:
        """
        Подключение к устройству.
        
        Returns:
            True если подключение успешно
        """
        pass
    
    @abstractmethod
    async def disconnect(self) -> bool:
        """
        Отключение от устройства.
        
        Returns:
            True если отключение успешно
        """
        pass
    
    @abstractmethod
    async def update_state(self) -> None:
        """Обновление состояния устройства."""
        pass
    
    @abstractmethod
    async def execute_command(self, command: str, parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Выполнение команды на устройстве.
        
        Args:
            command: Команда для выполнения
            parameters: Параметры команды
            
        Returns:
            Результат выполнения команды
        """
        pass
    
    def get_capabilities(self) -> List[DeviceCapability]:
        """Получение списка возможностей устройства."""
        return self.info.capabilities
    
    def has_capability(self, capability_name: str) -> bool:
        """
        Проверка наличия возможности у устройства.
        
        Args:
            capability_name: Имя возможности
            
        Returns:
            True если возможность поддерживается
        """
        return any(cap.name == capability_name for cap in self.info.capabilities)
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразование устройства в словарь."""
        return {
            "info": self.info.dict(),
            "attributes": self._attributes,
            "is_connected": self._is_connected
        }
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self.id}, name={self.name}, type={self.device_type.value})"


class SmartLight(BaseDevice):
    """Умная лампа."""
    
    def __init__(self, device_info: DeviceInfo):
        super().__init__(device_info)
        
        # Добавляем стандартные возможности для освещения
        if not self.has_capability("power"):
            self.info.capabilities.append(
                DeviceCapability(name="power", type="boolean", writable=True)
            )
        
        if not self.has_capability("brightness") and device_info.device_type == DeviceType.DIMMER:
            self.info.capabilities.append(
                DeviceCapability(
                    name="brightness", 
                    type="integer", 
                    writable=True,
                    min_value=0,
                    max_value=100,
                    unit="%"
                )
            )
        
        # Устанавливаем начальные значения
        self.set_attribute("power", False)
        if self.has_capability("brightness"):
            self.set_attribute("brightness", 100)
    
    async def turn_on(self, brightness: Optional[int] = None) -> bool:
        """
        Включение лампы.
        
        Args:
            brightness: Яркость (0-100)
            
        Returns:
            True если команда выполнена успешно
        """
        result = await self.execute_command("turn_on", {"brightness": brightness})
        return result.get("success", False)
    
    async def turn_off(self) -> bool:
        """
        Выключение лампы.
        
        Returns:
            True если команда выполнена успешно
        """
        result = await self.execute_command("turn_off")
        return result.get("success", False)
    
    async def set_brightness(self, brightness: int) -> bool:
        """
        Установка яркости.
        
        Args:
            brightness: Яркость (0-100)
            
        Returns:
            True если команда выполнена успешно
        """
        if not self.has_capability("brightness"):
            return False
        
        brightness = max(0, min(100, brightness))
        result = await self.execute_command("set_brightness", {"brightness": brightness})
        return result.get("success", False)


class SmartSwitch(BaseDevice):
    """Умный выключатель."""
    
    def __init__(self, device_info: DeviceInfo):
        super().__init__(device_info)
        
        # Добавляем стандартные возможности для выключателя
        if not self.has_capability("power"):
            self.info.capabilities.append(
                DeviceCapability(name="power", type="boolean", writable=True)
            )
        
        self.set_attribute("power", False)
    
    async def turn_on(self) -> bool:
        """Включение выключателя."""
        result = await self.execute_command("turn_on")
        return result.get("success", False)
    
    async def turn_off(self) -> bool:
        """Выключение выключателя."""
        result = await self.execute_command("turn_off")
        return result.get("success", False)
    
    async def toggle(self) -> bool:
        """Переключение состояния."""
        current_state = self.get_attribute("power")
        if current_state:
            return await self.turn_off()
        else:
            return await self.turn_on()


class SmartSensor(BaseDevice):
    """Базовый класс для датчиков."""
    
    def __init__(self, device_info: DeviceInfo):
        super().__init__(device_info)
        
        # Датчики обычно только читают данные
        for capability in self.info.capabilities:
            capability.writable = False
    
    async def get_sensor_value(self, sensor_type: str) -> Optional[float]:
        """
        Получение значения датчика.
        
        Args:
            sensor_type: Тип датчика
            
        Returns:
            Значение датчика или None
        """
        if not self.has_capability(sensor_type):
            return None
        
        await self.update_state()
        return self.get_attribute(sensor_type)