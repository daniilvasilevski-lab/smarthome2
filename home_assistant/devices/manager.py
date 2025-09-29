"""
Менеджер устройств Home Assistant AI.

Этот модуль отвечает за обнаружение, подключение, управление и мониторинг
всех устройств умного дома в системе.
"""

import asyncio
from typing import Dict, List, Optional, Type, Any
from datetime import datetime

import structlog

from ..core.config import HomeAssistantConfig
from ..core.events import EventBus, EventType, Event, emit_event
from .base import BaseDevice, DeviceInfo, DeviceState, DeviceType, Protocol


class DeviceManager:
    """Менеджер устройств умного дома."""
    
    def __init__(self, config: HomeAssistantConfig, event_bus: EventBus):
        """
        Инициализация менеджера устройств.
        
        Args:
            config: Конфигурация системы
            event_bus: Шина событий
        """
        self.config = config
        self.event_bus = event_bus
        self._logger = structlog.get_logger(__name__)
        
        # Хранилище устройств
        self._devices: Dict[str, BaseDevice] = {}
        self._device_factories: Dict[str, Type[BaseDevice]] = {}
        
        # Состояние менеджера
        self._running = False
        self._discovery_task: Optional[asyncio.Task] = None
        self._monitoring_task: Optional[asyncio.Task] = None
        
        # Настройки
        self._discovery_interval = 60  # сек
        self._monitoring_interval = 30  # сек
    
    async def initialize(self) -> None:
        """Инициализация менеджера устройств."""
        self._logger.info("Initializing Device Manager")
        
        # Регистрация обработчиков событий
        self.event_bus.subscribe(EventType.SYSTEM_STARTUP, self._on_system_startup)
        self.event_bus.subscribe(EventType.SYSTEM_SHUTDOWN, self._on_system_shutdown)
        
        # Регистрация фабрик устройств
        self._register_device_factories()
        
        self._logger.info("Device Manager initialized")
    
    async def start(self) -> None:
        """Запуск менеджера устройств."""
        if self._running:
            return
        
        self._logger.info("Starting Device Manager")
        self._running = True
        
        # Запуск фоновых задач
        self._discovery_task = asyncio.create_task(self._discovery_worker())
        self._monitoring_task = asyncio.create_task(self._monitoring_worker())
        
        # Загрузка сохраненных устройств
        await self._load_saved_devices()
        
        self._logger.info("Device Manager started")
    
    async def stop(self) -> None:
        """Остановка менеджера устройств."""
        if not self._running:
            return
        
        self._logger.info("Stopping Device Manager")
        self._running = False
        
        # Остановка фоновых задач
        if self._discovery_task:
            self._discovery_task.cancel()
            try:
                await self._discovery_task
            except asyncio.CancelledError:
                pass
        
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
        
        # Отключение всех устройств
        await self._disconnect_all_devices()
        
        self._logger.info("Device Manager stopped")
    
    def _register_device_factories(self) -> None:
        """Регистрация фабрик для создания устройств."""
        from .base import SmartLight, SmartSwitch, SmartSensor
        
        # Освещение
        self._device_factories["light"] = SmartLight
        self._device_factories["dimmer"] = SmartLight
        
        # Выключатели
        self._device_factories["switch"] = SmartSwitch
        self._device_factories["outlet"] = SmartSwitch
        
        # Датчики
        self._device_factories["temperature_sensor"] = SmartSensor
        self._device_factories["humidity_sensor"] = SmartSensor
        self._device_factories["motion_sensor"] = SmartSensor
    
    async def add_device(self, device_info: DeviceInfo) -> Optional[BaseDevice]:
        """
        Добавление устройства в систему.
        
        Args:
            device_info: Информация об устройстве
            
        Returns:
            Созданное устройство или None при ошибке
        """
        try:
            # Проверка, что устройство еще не добавлено
            if device_info.id in self._devices:
                self._logger.warning(
                    "Device already exists",
                    device_id=device_info.id,
                    device_name=device_info.name
                )
                return self._devices[device_info.id]
            
            # Создание устройства
            device = await self._create_device(device_info)
            if not device:
                return None
            
            # Добавление в хранилище
            self._devices[device_info.id] = device
            
            # Попытка подключения
            try:
                await device.connect()
                self._logger.info(
                    "Device connected",
                    device_id=device.id,
                    device_name=device.name
                )
                
                # Отправка события
                await emit_event(
                    EventType.DEVICE_CONNECTED,
                    data=device.to_dict(),
                    source="devices.manager"
                )
                
            except Exception as e:
                self._logger.warning(
                    "Failed to connect device",
                    device_id=device.id,
                    error=str(e)
                )
            
            return device
            
        except Exception as e:
            self._logger.error(
                "Failed to add device",
                device_info=device_info.dict(),
                error=str(e)
            )
            return None
    
    async def remove_device(self, device_id: str) -> bool:
        """
        Удаление устройства из системы.
        
        Args:
            device_id: Идентификатор устройства
            
        Returns:
            True если устройство успешно удалено
        """
        if device_id not in self._devices:
            return False
        
        device = self._devices[device_id]
        
        try:
            # Отключение устройства
            await device.disconnect()
            
            # Удаление из хранилища
            del self._devices[device_id]
            
            # Отправка события
            await emit_event(
                EventType.DEVICE_DISCONNECTED,
                data={"device_id": device_id, "device_name": device.name},
                source="devices.manager"
            )
            
            self._logger.info(
                "Device removed",
                device_id=device_id,
                device_name=device.name
            )
            
            return True
            
        except Exception as e:
            self._logger.error(
                "Failed to remove device",
                device_id=device_id,
                error=str(e)
            )
            return False
    
    def get_device(self, device_id: str) -> Optional[BaseDevice]:
        """
        Получение устройства по идентификатору.
        
        Args:
            device_id: Идентификатор устройства
            
        Returns:
            Устройство или None
        """
        return self._devices.get(device_id)
    
    def get_devices(self, 
                   device_type: Optional[DeviceType] = None,
                   room: Optional[str] = None,
                   state: Optional[DeviceState] = None) -> List[BaseDevice]:
        """
        Получение списка устройств с фильтрацией.
        
        Args:
            device_type: Фильтр по типу устройства
            room: Фильтр по комнате
            state: Фильтр по состоянию
            
        Returns:
            Список устройств
        """
        devices = list(self._devices.values())
        
        if device_type:
            devices = [d for d in devices if d.device_type == device_type]
        
        if room:
            devices = [d for d in devices if d.info.room == room]
        
        if state:
            devices = [d for d in devices if d.state == state]
        
        return devices
    
    def get_device_count(self) -> int:
        """Получение количества устройств."""
        return len(self._devices)
    
    def get_online_device_count(self) -> int:
        """Получение количества онлайн устройств."""
        return len([d for d in self._devices.values() if d.is_connected])
    
    async def execute_device_command(self, 
                                   device_id: str, 
                                   command: str, 
                                   parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Выполнение команды на устройстве.
        
        Args:
            device_id: Идентификатор устройства
            command: Команда
            parameters: Параметры команды
            
        Returns:
            Результат выполнения команды
        """
        device = self.get_device(device_id)
        if not device:
            return {"success": False, "error": "Device not found"}
        
        if not device.is_connected:
            return {"success": False, "error": "Device not connected"}
        
        try:
            result = await device.execute_command(command, parameters)
            
            # Отправка события об изменении состояния
            await emit_event(
                EventType.DEVICE_STATE_CHANGED,
                data={
                    "device_id": device_id,
                    "command": command,
                    "parameters": parameters,
                    "result": result
                },
                source="devices.manager"
            )
            
            return result
            
        except Exception as e:
            self._logger.error(
                "Failed to execute device command",
                device_id=device_id,
                command=command,
                error=str(e)
            )
            return {"success": False, "error": str(e)}
    
    async def _create_device(self, device_info: DeviceInfo) -> Optional[BaseDevice]:
        """
        Создание устройства с использованием фабрики.
        
        Args:
            device_info: Информация об устройстве
            
        Returns:
            Созданное устройство или None
        """
        device_type_str = device_info.device_type.value
        
        # Поиск фабрики для типа устройства
        factory = self._device_factories.get(device_type_str)
        if not factory:
            self._logger.warning(
                "No factory found for device type",
                device_type=device_type_str
            )
            # Используем базовый класс как fallback
            from .base import BaseDevice
            
            class GenericDevice(BaseDevice):
                async def connect(self) -> bool:
                    self._is_connected = True
                    self.info.state = DeviceState.ONLINE
                    return True
                
                async def disconnect(self) -> bool:
                    self._is_connected = False
                    self.info.state = DeviceState.OFFLINE
                    return True
                
                async def update_state(self) -> None:
                    pass
                
                async def execute_command(self, command: str, parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
                    return {"success": False, "error": "Generic device does not support commands"}
            
            factory = GenericDevice
        
        try:
            device = factory(device_info)
            return device
        except Exception as e:
            self._logger.error(
                "Failed to create device",
                device_info=device_info.dict(),
                error=str(e)
            )
            return None
    
    async def _discovery_worker(self) -> None:
        """Фоновая задача для обнаружения новых устройств."""
        while self._running:
            try:
                await self._discover_devices()
                await asyncio.sleep(self._discovery_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self._logger.error("Error in discovery worker", error=str(e))
                await asyncio.sleep(10)  # Короткая пауза при ошибке
    
    async def _monitoring_worker(self) -> None:
        """Фоновая задача для мониторинга состояния устройств."""
        while self._running:
            try:
                await self._monitor_devices()
                await asyncio.sleep(self._monitoring_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self._logger.error("Error in monitoring worker", error=str(e))
                await asyncio.sleep(10)  # Короткая пауза при ошибке
    
    async def _discover_devices(self) -> None:
        """Обнаружение новых устройств."""
        self._logger.debug("Starting device discovery")
        
        # Здесь будет логика обнаружения устройств
        # для различных протоколов (WiFi, Bluetooth, Zigbee, Z-Wave)
        
        # Пока заглушка
        pass
    
    async def _monitor_devices(self) -> None:
        """Мониторинг состояния существующих устройств."""
        for device in self._devices.values():
            try:
                await device.update_state()
                
                # Обновление времени последней активности
                device.info.last_seen = datetime.now()
                
            except Exception as e:
                self._logger.warning(
                    "Failed to update device state",
                    device_id=device.id,
                    error=str(e)
                )
                
                # Отметка устройства как недоступного
                device.info.state = DeviceState.UNAVAILABLE
    
    async def _load_saved_devices(self) -> None:
        """Загрузка сохраненных устройств из базы данных."""
        # Здесь будет логика загрузки устройств из базы данных
        self._logger.debug("Loading saved devices")
        pass
    
    async def _disconnect_all_devices(self) -> None:
        """Отключение всех устройств."""
        for device in self._devices.values():
            try:
                await device.disconnect()
            except Exception as e:
                self._logger.warning(
                    "Failed to disconnect device",
                    device_id=device.id,
                    error=str(e)
                )
    
    async def _on_system_startup(self, event: Event) -> None:
        """Обработчик события запуска системы."""
        self._logger.debug("System startup event received")
    
    async def _on_system_shutdown(self, event: Event) -> None:
        """Обработчик события остановки системы."""
        self._logger.debug("System shutdown event received")
        await self.stop()