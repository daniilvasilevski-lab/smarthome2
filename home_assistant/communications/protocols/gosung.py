"""Gosung LED Strip Protocol Handler.

Support for Gosung/Govee-style WiFi LED strips including SL3 model.
Uses local WiFi control and cloud APIs.
"""

import asyncio
import json
import aiohttp
from typing import Dict, List, Optional, Any
import structlog

from ..hub import ProtocolHandler

logger = structlog.get_logger(__name__)


class GosungDevice:
    """Gosung LED device representation."""
    
    def __init__(self, device_id: str, ip_address: str, model: str = "SL3"):
        self.device_id = device_id
        self.ip_address = ip_address
        self.model = model
        self.is_online = False
        self.brightness = 100
        self.color = {"r": 255, "g": 255, "b": 255}
        self.power_state = False
        self.effects = []
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            "device_id": self.device_id,
            "ip_address": self.ip_address,
            "model": self.model,
            "type": "led_strip",
            "brand": "Gosung",
            "is_online": self.is_online,
            "state": {
                "power": self.power_state,
                "brightness": self.brightness,
                "color": self.color
            },
            "capabilities": [
                "power_control",
                "brightness_control", 
                "color_control",
                "effects"
            ]
        }


class GosungHandler(ProtocolHandler):
    """Protocol handler for Gosung LED devices."""
    
    def __init__(self, config: dict, event_system):
        super().__init__(config, event_system)
        self.devices: Dict[str, GosungDevice] = {}
        self.session: Optional[aiohttp.ClientSession] = None
        self._discovery_task: Optional[asyncio.Task] = None
        
    async def start(self) -> bool:
        """Start Gosung protocol handler."""
        try:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=5.0)
            )
            
            # Start device discovery
            self._discovery_task = asyncio.create_task(
                self._discovery_loop()
            )
            
            self.is_running = True
            self._logger.info("Gosung protocol handler started")
            return True
            
        except Exception as e:
            self._logger.error("Failed to start Gosung handler", error=str(e))
            return False
    
    async def stop(self) -> None:
        """Stop Gosung protocol handler."""
        self.is_running = False
        
        if self._discovery_task:
            self._discovery_task.cancel()
            
        if self.session:
            await self.session.close()
            
        self._logger.info("Gosung protocol handler stopped")
    
    async def discover_devices(self) -> List[Dict[str, Any]]:
        """Discover Gosung LED devices on network."""
        devices = []
        
        try:
            # Try common Gosung device IPs and scan local network
            ip_ranges = [
                "192.168.1.{}", 
                "192.168.0.{}",
                "10.0.0.{}"
            ]
            
            tasks = []
            for ip_range in ip_ranges:
                for i in range(1, 255):
                    ip = ip_range.format(i)
                    tasks.append(self._check_gosung_device(ip))
            
            # Run discovery in batches to avoid overwhelming network
            batch_size = 50
            for i in range(0, len(tasks), batch_size):
                batch = tasks[i:i + batch_size]
                results = await asyncio.gather(*batch, return_exceptions=True)
                
                for result in results:
                    if isinstance(result, GosungDevice):
                        devices.append(result.to_dict())
                        self.devices[result.device_id] = result
                        
                        # Emit device found event
                        from ...core.events_simple import DeviceFoundEvent
                        await self.event_system.emit_event(
                            DeviceFoundEvent(
                                device_id=result.device_id,
                                protocol="gosung",
                                device_type="led_strip",
                                properties=result.to_dict()
                            )
                        )
                        
                # Small delay between batches
                await asyncio.sleep(0.1)
                
        except Exception as e:
            self._logger.error("Device discovery failed", error=str(e))
            
        self._logger.info(f"Discovered {len(devices)} Gosung devices")
        return devices
    
    async def _check_gosung_device(self, ip: str) -> Optional[GosungDevice]:
        """Check if IP address hosts a Gosung device."""
        try:
            # Try Gosung API endpoints
            endpoints = [
                f"http://{ip}/api/device/info",
                f"http://{ip}/gosung/status",
                f"http://{ip}/led/info"
            ]
            
            for endpoint in endpoints:
                try:
                    async with self.session.get(endpoint) as response:
                        if response.status == 200:
                            data = await response.json()
                            
                            # Check if this looks like a Gosung device
                            if self._is_gosung_device(data):
                                device_id = data.get('device_id') or f"gosung_{ip.replace('.', '_')}"
                                model = data.get('model', 'SL3')
                                
                                device = GosungDevice(device_id, ip, model)
                                device.is_online = True
                                
                                # Update device state from response
                                if 'state' in data:
                                    state = data['state']
                                    device.power_state = state.get('power', False)
                                    device.brightness = state.get('brightness', 100)
                                    device.color = state.get('color', {"r": 255, "g": 255, "b": 255})
                                
                                return device
                                
                except (aiohttp.ClientError, json.JSONDecodeError):
                    continue
                    
        except Exception:
            pass
            
        return None
    
    def _is_gosung_device(self, data: dict) -> bool:
        """Check if response data indicates a Gosung device."""
        indicators = [
            'gosung' in str(data).lower(),
            'device_id' in data and 'model' in data,
            'led' in str(data).lower() and 'strip' in str(data).lower(),
            data.get('brand', '').lower() in ['gosung', 'govee'],
            data.get('type') == 'led_strip'
        ]
        return any(indicators)
    
    async def send_command(self, device_id: str, command: str, params: Dict[str, Any]) -> bool:
        """Send command to Gosung device."""
        device = self.devices.get(device_id)
        if not device:
            self._logger.error("Device not found", device_id=device_id)
            return False
            
        try:
            endpoint = f"http://{device.ip_address}/api/device/control"
            payload = {
                "command": command,
                "params": params
            }
            
            async with self.session.post(endpoint, json=payload) as response:
                if response.status == 200:
                    # Update local device state
                    await self._update_device_state(device, command, params)
                    return True
                else:
                    self._logger.error(
                        "Command failed", 
                        device_id=device_id,
                        command=command,
                        status=response.status
                    )
                    return False
                    
        except Exception as e:
            self._logger.error(
                "Failed to send command",
                device_id=device_id, 
                command=command,
                error=str(e)
            )
            return False
    
    async def _update_device_state(self, device: GosungDevice, command: str, params: Dict[str, Any]):
        """Update local device state after command."""
        if command == "power":
            device.power_state = params.get("state", False)
        elif command == "brightness":
            device.brightness = params.get("value", device.brightness)
        elif command == "color":
            device.color = params.get("color", device.color)
        elif command == "effect":
            pass  # Effects don't change persistent state
            
        # Emit state change event
        from ...core.events_simple import DeviceStateChangedEvent
        await self.event_system.emit_event(
            DeviceStateChangedEvent(
                device_id=device.device_id,
                old_state={},
                new_state=device.to_dict()["state"]
            )
        )
    
    async def _discovery_loop(self):
        """Continuous device discovery loop."""
        while self.is_running:
            try:
                await self.discover_devices()
                await asyncio.sleep(300)  # Re-scan every 5 minutes
            except asyncio.CancelledError:
                break
            except Exception as e:
                self._logger.error("Discovery loop error", error=str(e))
                await asyncio.sleep(60)  # Wait before retry
    
    async def get_device_state(self, device_id: str) -> Optional[Dict[str, Any]]:
        """Get current device state."""
        device = self.devices.get(device_id)
        if not device:
            return None
            
        try:
            endpoint = f"http://{device.ip_address}/api/device/status"
            async with self.session.get(endpoint) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Update device with fresh state
                    if 'state' in data:
                        state = data['state']
                        device.power_state = state.get('power', device.power_state)
                        device.brightness = state.get('brightness', device.brightness)
                        device.color = state.get('color', device.color)
                        device.is_online = True
                    
                    return device.to_dict()
                    
        except Exception as e:
            self._logger.error("Failed to get device state", device_id=device_id, error=str(e))
            device.is_online = False
            
        return device.to_dict() if device else None
    
    # Convenience methods for common LED operations
    async def set_power(self, device_id: str, state: bool) -> bool:
        """Turn device on/off."""
        return await self.send_command(device_id, "power", {"state": state})
    
    async def set_brightness(self, device_id: str, brightness: int) -> bool:
        """Set brightness (0-100)."""
        brightness = max(0, min(100, brightness))
        return await self.send_command(device_id, "brightness", {"value": brightness})
    
    async def set_color(self, device_id: str, r: int, g: int, b: int) -> bool:
        """Set RGB color."""
        color = {"r": max(0, min(255, r)), "g": max(0, min(255, g)), "b": max(0, min(255, b))}
        return await self.send_command(device_id, "color", {"color": color})
    
    async def set_effect(self, device_id: str, effect_name: str, speed: int = 50) -> bool:
        """Set lighting effect."""
        return await self.send_command(device_id, "effect", {"name": effect_name, "speed": speed})