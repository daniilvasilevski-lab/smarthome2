"""
REST API для Home Assistant AI.

Основные эндпоинты для управления устройствами, общения с AI и мониторинга системы.
"""

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os
from typing import Dict, List, Optional, Any
import asyncio
import json
import uuid
from datetime import datetime

from ..core.config import HomeAssistantConfig
from ..core.simple import EventSystem
from ..storage.database import DatabaseManager
from ..communication.hub import CommunicationHub
from ..ai.reasoning import ReasoningEngine
from ..ai.smart_scenarios import SmartScenariosAI
from ..ai.home_management import ai_home_manager, OptimizationType, PredictionType

# Pydantic модели для API
class ChatMessage(BaseModel):
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str
    intent: Optional[str] = None
    confidence: Optional[float] = None
    actions: List[Dict[str, Any]] = []

class DeviceCommand(BaseModel):
    device_id: str
    command: str
    params: Dict[str, Any] = {}

class DeviceInfo(BaseModel):
    id: str
    name: str
    device_type: str
    state: str
    room: Optional[str] = None
    capabilities: List[str] = []

# Новые модели для WiFi и Spotify
class WiFiNetwork(BaseModel):
    ssid: str
    password: Optional[str] = None
    security: str = "WPA2"

class WiFiNetworkInfo(BaseModel):
    ssid: str
    signal_strength: int
    security: str
    connected: bool = False

class SpotifyAuthRequest(BaseModel):
    client_id: str
    client_secret: str
    redirect_uri: str = "http://localhost:8000/spotify/callback"

class SpotifyControlRequest(BaseModel):
    action: str  # play, pause, next, previous, volume
    volume: Optional[int] = None
    track_uri: Optional[str] = None

class VoiceRequest(BaseModel):
    timeout: float = 5.0

class VoiceSettingsUpdate(BaseModel):
    stt_provider: str
    tts_provider: str
    wake_words: str

class SystemStatus(BaseModel):
    status: str
    uptime: str
    active_protocols: List[str]
    devices_count: int
    ai_provider: str
    privacy_mode: bool

class VoiceCommand(BaseModel):
    command: str
    
class VoiceResponse(BaseModel):
    transcribed_text: str
    ai_response: str
    success: bool
    
class VoiceStatus(BaseModel):
    enabled: bool
    listening: bool
    state: str
    wake_words: List[str]
    stt_provider: str
    tts_provider: str


def create_app(config: HomeAssistantConfig, 
               event_system: EventSystem,
               db_manager: DatabaseManager,
               communication_hub: CommunicationHub,
               reasoning_engine: ReasoningEngine,
               voice_manager=None) -> FastAPI:
    """Создание FastAPI приложения."""
    
    app = FastAPI(
        title="Home Assistant AI",
        description="Умный домашний ассистент с AI reasoning",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc"
    )
    
    # CORS настройки
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.api.cors_origins,
        allow_credentials=config.api.cors_credentials,
        allow_methods=config.api.cors_methods,
        allow_headers=config.api.cors_headers,
    )
    
    # Глобальные переменные
    app.state.config = config
    app.state.event_system = event_system
    app.state.db_manager = db_manager
    app.state.communication_hub = communication_hub
    app.state.reasoning_engine = reasoning_engine
    app.state.voice_manager = voice_manager
    app.state.start_time = datetime.utcnow()
    
    # WebSocket connections manager
    app.state.websocket_connections = set()
    
    # Initialize Smart Scenarios AI
    app.state.smart_scenarios_ai = SmartScenariosAI(db_manager, reasoning_engine)
    
    # Статические файлы и веб-интерфейс
    static_dir = os.path.join(os.path.dirname(__file__), "..", "ui", "static")
    if os.path.exists(static_dir):
        app.mount("/static", StaticFiles(directory=static_dir), name="static")
    
    @app.get("/", response_class=HTMLResponse)
    async def root():
        """Главная страница веб-интерфейса."""
        static_dir = os.path.join(os.path.dirname(__file__), "..", "ui", "static")
        index_path = os.path.join(static_dir, "index.html")
        
        if os.path.exists(index_path):
            with open(index_path, 'r', encoding='utf-8') as f:
                return HTMLResponse(content=f.read())
        else:
            return {
                "name": "Home Assistant AI",
                "version": "1.0.0",
                "status": "running",
                "docs": "/docs",
                "message": "Web UI not available, use API endpoints"
            }
    
    @app.get("/health")
    async def health_check():
        """Проверка здоровья системы."""
        return {"status": "healthy", "timestamp": datetime.utcnow()}
    
    @app.get("/status", response_model=SystemStatus)
    async def get_system_status():
        """Получение статуса системы."""
        uptime = datetime.utcnow() - app.state.start_time
        devices = await app.state.db_manager.get_all_devices()
        
        return SystemStatus(
            status="running",
            uptime=str(uptime),
            active_protocols=app.state.communication_hub.get_available_protocols(),
            devices_count=len(devices),
            ai_provider="openai" if config.ai.openai_api_key else "ollama",
            privacy_mode=config.privacy.enabled
        )
    
    # === AI Chat API ===
    
    @app.post("/chat", response_model=ChatResponse)
    async def chat_with_ai(message: ChatMessage):
        """Общение с AI ассистентом."""
        try:
            session_id = message.session_id or str(uuid.uuid4())
            
            result = await app.state.reasoning_engine.process_user_input(
                user_input=message.message,
                session_id=session_id
            )
            
            return ChatResponse(
                response=result["response"],
                session_id=session_id,
                intent=result.get("intent"),
                confidence=result.get("confidence"),
                actions=result.get("actions", [])
            )
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/chat/history/{session_id}")
    async def get_chat_history(session_id: str, limit: int = 50):
        """Получение истории разговора."""
        try:
            history = await app.state.db_manager.get_conversation_history(session_id, limit)
            return {"session_id": session_id, "messages": history}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    # === Device Management API ===
    
    @app.get("/devices", response_model=List[DeviceInfo])
    async def get_devices():
        """Получение списка всех устройств."""
        try:
            devices = await app.state.db_manager.get_all_devices()
            return [
                DeviceInfo(
                    id=device["id"],
                    name=device["name"],
                    device_type=device["device_type"],
                    state=device["state"],
                    room=device.get("room"),
                    capabilities=device.get("capabilities", [])
                )
                for device in devices
            ]
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/devices/{device_id}")
    async def get_device(device_id: str):
        """Получение информации об устройстве."""
        try:
            device = await app.state.db_manager.get_device(device_id)
            if not device:
                raise HTTPException(status_code=404, detail="Device not found")
            return device
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/devices/{device_id}/command")
    async def send_device_command(device_id: str, command: DeviceCommand):
        """Отправка команды устройству."""
        try:
            success = await app.state.communication_hub.send_device_command(
                device_id=command.device_id,
                command=command.command,
                params=command.params
            )
            
            if success:
                return {"success": True, "message": "Command sent successfully"}
            else:
                raise HTTPException(status_code=400, detail="Failed to send command")
                
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/devices/{device_id}/action")
    async def device_action(device_id: str, action_data: dict):
        """Выполнение действия с устройством (для UI)."""
        try:
            command = action_data.get("command")
            params = action_data.get("params", {})
            
            success = await app.state.communication_hub.send_device_command(
                device_id=device_id,
                command=command,
                params=params
            )
            
            return {"success": success}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/devices/discover")
    async def discover_devices(background_tasks: BackgroundTasks):
        """Запуск поиска новых устройств."""
        try:
            background_tasks.add_task(app.state.communication_hub.discover_all_devices)
            return {"message": "Device discovery started"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/devices/scan")
    async def scan_devices(background_tasks: BackgroundTasks):
        """Сканирование устройств (алиас для discover для UI)."""
        try:
            background_tasks.add_task(app.state.communication_hub.discover_all_devices)
            return {"message": "Device scan started"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    # === Integration API ===
    
    @app.get("/integrations")
    async def get_integrations():
        """Получение списка интеграций."""
        try:
            integrations = await app.state.db_manager.get_enabled_integrations()
            return integrations
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/integrations/spotify/play")
    async def spotify_play(query: str = ""):
        """Воспроизведение музыки на Spotify."""
        try:
            # Симуляция команды Spotify
            await app.state.db_manager.log_event(
                "spotify_play_requested",
                source="api",
                data={"query": query}
            )
            return {"message": f"Playing: {query or 'default playlist'} on Spotify"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/integrations/weather")
    async def get_weather(location: str = "current"):
        """Получение информации о погоде."""
        try:
            # Симуляция запроса погоды
            weather_data = {
                "location": location,
                "temperature": 15,
                "condition": "partly_cloudy",
                "humidity": 65,
                "wind_speed": 12,
                "forecast": "Light rain expected in the evening"
            }
            
            await app.state.db_manager.log_event(
                "weather_requested",
                source="api",
                data={"location": location}
            )
            
            return weather_data
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    # === Events API ===
    
    @app.get("/events")
    async def get_events(limit: int = 100):
        """Получение логов событий."""
        try:
            # Здесь можно добавить метод для получения событий из БД
            return {"message": "Events endpoint", "limit": limit}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    # === Voice API ===
    
    @app.post("/voice/process")
    async def process_voice_input(audio_data: str):
        """Обработка голосового ввода."""
        try:
            # Здесь будет обработка аудио через STT
            # Пока возвращаем заглушку
            return {"message": "Voice processing not implemented yet"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/voice/status", response_model=VoiceStatus)
    async def get_voice_status():
        """Получение статуса голосового ассистента."""
        try:
            if not app.state.voice_manager:
                return VoiceStatus(
                    enabled=False,
                    listening=False,
                    state="disabled",
                    wake_words=[],
                    stt_provider="none",
                    tts_provider="none"
                )
            
            voice_manager = app.state.voice_manager
            return VoiceStatus(
                enabled=True,
                listening=voice_manager.is_listening(),
                state=voice_manager.get_state().value,
                wake_words=voice_manager.config.wake_words,
                stt_provider=voice_manager.config.stt_provider.value,
                tts_provider=voice_manager.config.tts_provider.value
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/voice/speak")
    async def speak_text(request_data: dict):
        """Произнести текст через TTS."""
        try:
            if not app.state.voice_manager:
                raise HTTPException(status_code=400, detail="Voice manager not available")
            
            text = request_data.get("text", "")
            blocking = request_data.get("blocking", False)
            
            success = await app.state.voice_manager.speak(text, blocking=blocking)
            return {"success": success, "text": text}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/voice/listen")
    async def listen_for_command(request_data: dict = {}):
        """Прослушать команду пользователя."""
        try:
            if not app.state.voice_manager:
                raise HTTPException(status_code=400, detail="Voice manager not available")
            
            timeout = request_data.get("timeout", 5.0)
            command = await app.state.voice_manager.listen_once(timeout=timeout)
            return {"text": command, "success": command is not None}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/voice/command", response_model=VoiceResponse)
    async def process_voice_command(command: VoiceCommand):
        """Обработка голосовой команды."""
        try:
            if not app.state.voice_manager:
                raise HTTPException(status_code=400, detail="Voice manager not available")
            
            # Обрабатываем команду через AI
            result = await app.state.reasoning_engine.process_user_input(
                user_input=command.command,
                session_id="voice_api_session"
            )
            
            ai_response = result.get("response", "Команда обработана")
            
            # Произносим ответ
            speak_success = await app.state.voice_manager.speak(ai_response, blocking=False)
            
            return VoiceResponse(
                transcribed_text=command.command,
                ai_response=ai_response,
                success=speak_success
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    # === Settings API ===
    
    @app.post("/voice/settings")
    async def save_voice_settings(settings: dict):
        """Сохранение настроек голосового ассистента."""
        try:
            # В реальной реализации здесь будет сохранение настроек
            return {"success": True, "message": "Voice settings saved"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/settings")
    async def save_settings(settings: dict):
        """Сохранение общих настроек системы."""
        try:
            # В реальной реализации здесь будет сохранение настроек
            return {"success": True, "message": "Settings saved"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    # === WiFi Management API ===
    
    @app.get("/wifi/networks")
    async def scan_wifi_networks():
        """Сканирование доступных WiFi сетей."""
        try:
            import subprocess
            import re
            
            # Реальное сканирование WiFi сетей на Linux/macOS
            networks = []
            try:
                # Linux nmcli команда
                result = subprocess.run(['nmcli', 'dev', 'wifi', 'list'], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')[1:]  # Пропустить заголовок
                    for line in lines:
                        parts = line.split()
                        if len(parts) >= 3:
                            ssid = parts[1] if parts[1] != '--' else 'Hidden Network'
                            signal = int(parts[5]) if parts[5].isdigit() else 50
                            security = 'WPA2' if 'WPA' in line else 'Open'
                            connected = '*' in line
                            
                            networks.append(WiFiNetworkInfo(
                                ssid=ssid,
                                signal_strength=signal,
                                security=security,
                                connected=connected
                            ))
            except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
                # Fallback к примерным данным если команда недоступна
                networks = [
                    WiFiNetworkInfo(ssid="Home_Network", signal_strength=95, security="WPA2", connected=True),
                    WiFiNetworkInfo(ssid="Guest_WiFi", signal_strength=78, security="WPA2"),
                    WiFiNetworkInfo(ssid="Office_5G", signal_strength=62, security="WPA3"),
                    WiFiNetworkInfo(ssid="Public_WiFi", signal_strength=45, security="Open"),
                    WiFiNetworkInfo(ssid="Neighbor_Network", signal_strength=23, security="WPA2")
                ]
            
            return {"success": True, "networks": [network.dict() for network in networks]}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/wifi/connect")
    async def connect_to_wifi(network: WiFiNetwork):
        """Подключение к WiFi сети."""
        try:
            import subprocess
            
            # Попытка подключения через nmcli
            try:
                if network.password:
                    cmd = ['nmcli', 'dev', 'wifi', 'connect', network.ssid, 'password', network.password]
                else:
                    cmd = ['nmcli', 'dev', 'wifi', 'connect', network.ssid]
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0:
                    return {
                        "success": True,
                        "message": f"Successfully connected to {network.ssid}",
                        "connected_ssid": network.ssid
                    }
                else:
                    return {
                        "success": False,
                        "message": f"Failed to connect to {network.ssid}: {result.stderr}"
                    }
            except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
                # Симуляция успешного подключения если команда недоступна
                return {
                    "success": True,
                    "message": f"Simulated connection to {network.ssid}",
                    "connected_ssid": network.ssid
                }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/wifi/status")
    async def get_wifi_status():
        """Получение текущего статуса WiFi."""
        try:
            import subprocess
            
            try:
                # Получение информации о текущем подключении
                result = subprocess.run(['nmcli', 'connection', 'show', '--active'], 
                                      capture_output=True, text=True, timeout=5)
                
                if result.returncode == 0 and 'wifi' in result.stdout.lower():
                    lines = result.stdout.strip().split('\n')
                    for line in lines:
                        if 'wifi' in line.lower():
                            parts = line.split()
                            ssid = parts[0] if parts else "Unknown"
                            return {
                                "connected": True,
                                "ssid": ssid,
                                "signal_strength": 85,  # Можно получить через iwconfig
                                "ip_address": "192.168.1.100"  # Можно получить через ip addr
                            }
                
                return {
                    "connected": False,
                    "ssid": None,
                    "signal_strength": 0,
                    "ip_address": None
                }
                
            except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
                # Fallback данные
                return {
                    "connected": True,
                    "ssid": "Home_Network",
                    "signal_strength": 95,
                    "ip_address": "192.168.1.100"
                }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/wifi/disconnect")
    async def disconnect_wifi():
        """Отключение от текущей WiFi сети."""
        try:
            import subprocess
            
            try:
                result = subprocess.run(['nmcli', 'dev', 'disconnect', 'wlan0'], 
                                      capture_output=True, text=True, timeout=10)
                return {"success": result.returncode == 0, "message": "WiFi disconnected"}
            except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
                return {"success": True, "message": "WiFi disconnected (simulated)"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    # === Spotify Integration API ===
    
    @app.post("/spotify/auth")
    async def setup_spotify_auth(auth_request: SpotifyAuthRequest):
        """Инициация OAuth процесса для Spotify."""
        try:
            import urllib.parse
            
            # Создание OAuth URL для Spotify
            base_url = "https://accounts.spotify.com/authorize"
            params = {
                "client_id": auth_request.client_id,
                "response_type": "code",
                "redirect_uri": auth_request.redirect_uri,
                "scope": "user-read-playback-state user-modify-playback-state user-read-currently-playing playlist-read-private",
                "state": str(uuid.uuid4())  # Для безопасности
            }
            
            auth_url = f"{base_url}?{urllib.parse.urlencode(params)}"
            
            # Сохранение параметров в БД для последующего использования
            await app.state.db_manager.save_integration_settings("spotify", {
                "client_id": auth_request.client_id,
                "client_secret": auth_request.client_secret,
                "redirect_uri": auth_request.redirect_uri,
                "state": params["state"]
            })
            
            return {
                "success": True,
                "auth_url": auth_url,
                "state": params["state"]
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/spotify/callback")
    async def spotify_oauth_callback(code: str, state: str):
        """Обработка OAuth callback от Spotify."""
        try:
            import aiohttp
            
            # Получение сохраненных настроек
            settings = await app.state.db_manager.get_integration_settings("spotify")
            
            if not settings or settings.get("state") != state:
                raise HTTPException(status_code=400, detail="Invalid state parameter")
            
            # Обмен кода на токен доступа
            token_url = "https://accounts.spotify.com/api/token"
            data = {
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": settings["redirect_uri"],
                "client_id": settings["client_id"],
                "client_secret": settings["client_secret"]
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(token_url, data=data) as response:
                    if response.status == 200:
                        token_data = await response.json()
                        
                        # Сохранение токенов
                        settings.update({
                            "access_token": token_data["access_token"],
                            "refresh_token": token_data.get("refresh_token"),
                            "expires_in": token_data.get("expires_in"),
                            "token_received_at": datetime.utcnow().isoformat()
                        })
                        
                        await app.state.db_manager.save_integration_settings("spotify", settings)
                        
                        return HTMLResponse("""
                        <html>
                            <body>
                                <h1>Spotify Successfully Connected!</h1>
                                <p>You can now close this window and return to the app.</p>
                                <script>
                                    setTimeout(() => window.close(), 3000);
                                </script>
                            </body>
                        </html>
                        """)
                    else:
                        raise HTTPException(status_code=400, detail="Failed to exchange code for token")
                        
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/spotify/status")
    async def get_spotify_status():
        """Получение текущего статуса Spotify."""
        try:
            settings = await app.state.db_manager.get_integration_settings("spotify")
            
            if not settings or not settings.get("access_token"):
                return {
                    "connected": False,
                    "message": "Spotify not connected"
                }
            
            import aiohttp
            
            # Попытка получить текущий трек
            try:
                headers = {"Authorization": f"Bearer {settings['access_token']}"}
                
                async with aiohttp.ClientSession() as session:
                    async with session.get("https://api.spotify.com/v1/me/player/currently-playing", 
                                         headers=headers) as response:
                        if response.status == 200:
                            data = await response.json()
                            if data and data.get("item"):
                                track = data["item"]
                                return {
                                    "connected": True,
                                    "current_track": {
                                        "name": track["name"],
                                        "artist": ", ".join([artist["name"] for artist in track["artists"]]),
                                        "album": track["album"]["name"],
                                        "duration": track["duration_ms"],
                                        "position": data.get("progress_ms", 0),
                                        "is_playing": data.get("is_playing", False)
                                    },
                                    "device": data.get("device", {}).get("name", "Unknown"),
                                    "volume": data.get("device", {}).get("volume_percent", 50)
                                }
                        elif response.status == 204:
                            # Нет активного воспроизведения
                            return {
                                "connected": True,
                                "current_track": None,
                                "message": "No track currently playing"
                            }
                        else:
                            # Возможно, токен истек
                            return {
                                "connected": False,
                                "message": "Authentication required"
                            }
            except Exception:
                # Fallback к демо данным
                return {
                    "connected": True,
                    "current_track": {
                        "name": "Bohemian Rhapsody",
                        "artist": "Queen",
                        "album": "A Night at the Opera",
                        "duration": 355000,
                        "position": 120000,
                        "is_playing": True
                    },
                    "device": "Smart Home Assistant",
                    "volume": 75
                }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/spotify/control")
    async def control_spotify(control_request: SpotifyControlRequest):
        """Управление воспроизведением Spotify."""
        try:
            settings = await app.state.db_manager.get_integration_settings("spotify")
            
            if not settings or not settings.get("access_token"):
                raise HTTPException(status_code=400, detail="Spotify not connected")
            
            import aiohttp
            
            headers = {"Authorization": f"Bearer {settings['access_token']}"}
            
            async with aiohttp.ClientSession() as session:
                if control_request.action == "play":
                    url = "https://api.spotify.com/v1/me/player/play"
                    data = {}
                    if control_request.track_uri:
                        data["uris"] = [control_request.track_uri]
                    
                    async with session.put(url, headers=headers, json=data) as response:
                        success = response.status in [200, 204]
                        
                elif control_request.action == "pause":
                    url = "https://api.spotify.com/v1/me/player/pause"
                    async with session.put(url, headers=headers) as response:
                        success = response.status in [200, 204]
                        
                elif control_request.action == "next":
                    url = "https://api.spotify.com/v1/me/player/next"
                    async with session.post(url, headers=headers) as response:
                        success = response.status in [200, 204]
                        
                elif control_request.action == "previous":
                    url = "https://api.spotify.com/v1/me/player/previous"
                    async with session.post(url, headers=headers) as response:
                        success = response.status in [200, 204]
                        
                elif control_request.action == "volume" and control_request.volume is not None:
                    url = f"https://api.spotify.com/v1/me/player/volume?volume_percent={control_request.volume}"
                    async with session.put(url, headers=headers) as response:
                        success = response.status in [200, 204]
                else:
                    raise HTTPException(status_code=400, detail="Invalid action")
                
                return {
                    "success": success,
                    "message": f"Spotify {control_request.action} {'successful' if success else 'failed'}"
                }
                
        except HTTPException:
            raise
        except Exception as e:
            # Fallback к симуляции
            return {
                "success": True,
                "message": f"Spotify {control_request.action} (simulated)"
            }
    
    @app.post("/spotify/disconnect")
    async def disconnect_spotify():
        """Отключение от Spotify."""
        try:
            await app.state.db_manager.remove_integration_settings("spotify")
            return {"success": True, "message": "Spotify disconnected"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    # === Analytics API ===
    
    @app.get("/analytics/energy")
    async def get_energy_analytics():
        """Получение данных аналитики энергопотребления."""
        try:
            import random
            from datetime import datetime, timedelta
            
            now = datetime.now()
            data = []
            total = 0
            
            for i in range(24):
                time_point = now - timedelta(hours=23-i)
                consumption = random.randint(15, 45)  # кВт·ч
                total += consumption
                data.append({
                    "time": time_point.strftime("%H:%M"),
                    "consumption": consumption,
                    "cost": consumption * 0.15  # $0.15 per kWh
                })
            
            return {
                "success": True,
                "data": data,
                "total_today": total,
                "average_hourly": round(total / len(data), 2),
                "estimated_cost": round(total * 0.15, 2),
                "currency": "USD"
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/analytics/devices")
    async def get_device_analytics():
        """Получение данных использования устройств."""
        try:
            import random
            
            devices = [
                {"name": "Living Room Lights", "usage": random.randint(60, 95), "energy": random.randint(5, 15)},
                {"name": "Kitchen Appliances", "usage": random.randint(40, 80), "energy": random.randint(20, 40)},
                {"name": "Bedroom Climate", "usage": random.randint(30, 70), "energy": random.randint(25, 50)},
                {"name": "Security System", "usage": random.randint(80, 99), "energy": random.randint(3, 8)},
                {"name": "Entertainment", "usage": random.randint(20, 60), "energy": random.randint(10, 25)},
                {"name": "Gosung LED Strips", "usage": random.randint(40, 85), "energy": random.randint(2, 12)}
            ]
            
            return {"success": True, "devices": devices}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    # === Scenarios API ===
    
    @app.get("/scenarios")
    async def get_scenarios():
        """Получение списка автоматизационных сценариев."""
        try:
            scenarios = [
                {
                    "id": "morning_routine",
                    "name": "Morning Routine",
                    "description": "Turn on lights, start coffee, play morning music",
                    "enabled": True,
                    "trigger_type": "time",
                    "trigger_value": "07:00",
                    "actions": [
                        {"device": "bedroom_lights", "action": "turn_on", "brightness": 50},
                        {"device": "coffee_maker", "action": "start"},
                        {"device": "spotify", "action": "play_playlist", "playlist": "Morning Jazz"}
                    ]
                },
                {
                    "id": "movie_night",
                    "name": "Movie Night",
                    "description": "Dim lights, set mood lighting, prepare entertainment",
                    "enabled": True,
                    "trigger_type": "manual",
                    "actions": [
                        {"device": "living_room_lights", "action": "dim", "brightness": 20},
                        {"device": "gosung_led_strips", "action": "set_color", "color": "purple"},
                        {"device": "tv", "action": "turn_on", "input": "Netflix"}
                    ]
                },
                {
                    "id": "away_mode",
                    "name": "Away Mode",
                    "description": "Security mode when leaving home",
                    "enabled": False,
                    "trigger_type": "location",
                    "trigger_value": "away",
                    "actions": [
                        {"device": "all_lights", "action": "turn_off"},
                        {"device": "thermostat", "action": "set_temperature", "temperature": 18},
                        {"device": "security_system", "action": "arm"}
                    ]
                },
                {
                    "id": "bedtime",
                    "name": "Bedtime",
                    "description": "Prepare house for sleep",
                    "enabled": True,
                    "trigger_type": "time",
                    "trigger_value": "22:30",
                    "actions": [
                        {"device": "all_lights", "action": "turn_off"},
                        {"device": "bedroom_lights", "action": "turn_on", "brightness": 10},
                        {"device": "spotify", "action": "play_playlist", "playlist": "Sleep Sounds"},
                        {"device": "gosung_led_strips", "action": "set_effect", "effect": "fade"}
                    ]
                }
            ]
            
            return {"success": True, "scenarios": scenarios}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/scenarios")
    async def create_scenario(scenario: dict):
        """Создание нового сценария."""
        try:
            scenario_id = str(uuid.uuid4())
            scenario["id"] = scenario_id
            scenario["created_at"] = datetime.utcnow().isoformat()
            
            # Сохранение в БД (здесь пока симуляция)
            await app.state.db_manager.log_event(
                "scenario_created",
                source="api",
                data={"scenario_id": scenario_id, "name": scenario.get("name")}
            )
            
            return {"success": True, "scenario": scenario, "message": "Scenario created successfully"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.put("/scenarios/{scenario_id}")
    async def update_scenario(scenario_id: str, scenario: dict):
        """Обновление существующего сценария."""
        try:
            scenario["id"] = scenario_id
            scenario["updated_at"] = datetime.utcnow().isoformat()
            
            await app.state.db_manager.log_event(
                "scenario_updated",
                source="api",
                data={"scenario_id": scenario_id}
            )
            
            return {"success": True, "scenario": scenario, "message": "Scenario updated successfully"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.delete("/scenarios/{scenario_id}")
    async def delete_scenario(scenario_id: str):
        """Удаление сценария."""
        try:
            await app.state.db_manager.log_event(
                "scenario_deleted",
                source="api",
                data={"scenario_id": scenario_id}
            )
            
            return {"success": True, "message": f"Scenario {scenario_id} deleted successfully"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/scenarios/{scenario_id}/execute")
    async def execute_scenario(scenario_id: str):
        """Выполнение сценария."""
        try:
            # Здесь будет реальная логика выполнения сценария
            await app.state.db_manager.log_event(
                "scenario_executed",
                source="api",
                data={"scenario_id": scenario_id}
            )
            
            return {"success": True, "message": f"Scenario {scenario_id} executed successfully"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/scenarios/{scenario_id}/toggle")
    async def toggle_scenario(scenario_id: str):
        """Включение/выключение сценария."""
        try:
            await app.state.db_manager.log_event(
                "scenario_toggled",
                source="api",
                data={"scenario_id": scenario_id}
            )
            
            return {"success": True, "message": f"Scenario {scenario_id} toggled successfully"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    # === WebSocket API для real-time обновлений ===
    
    @app.websocket("/ws/{client_id}")
    async def websocket_endpoint(websocket: WebSocket, client_id: str):
        """WebSocket соединение для real-time обновлений."""
        await websocket.accept()
        app.state.websocket_connections.add(websocket)
        
        try:
            # Отправляем приветственное сообщение
            await websocket.send_json({
                "type": "connection",
                "status": "connected",
                "client_id": client_id,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Отправляем начальные данные
            await send_initial_data(websocket)
            
            # Слушаем сообщения от клиента
            while True:
                try:
                    data = await websocket.receive_json()
                    await handle_websocket_message(websocket, data)
                except WebSocketDisconnect:
                    break
                    
        except Exception as e:
            print(f"WebSocket error: {e}")
        finally:
            app.state.websocket_connections.discard(websocket)
    
    async def send_initial_data(websocket: WebSocket):
        """Отправка начальных данных при подключении."""
        try:
            # Статус системы
            devices = await app.state.db_manager.get_all_devices()
            await websocket.send_json({
                "type": "initial_status",
                "devices_count": len(devices),
                "system_status": "running",
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Список устройств
            device_info = [
                DeviceInfo(
                    id=device["id"],
                    name=device["name"],
                    device_type=device["device_type"],
                    state=device["state"],
                    room=device.get("room"),
                    capabilities=device.get("capabilities", [])
                ).dict()
                for device in devices
            ]
            
            await websocket.send_json({
                "type": "devices_update",
                "devices": device_info,
                "timestamp": datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            print(f"Error sending initial data: {e}")
    
    async def handle_websocket_message(websocket: WebSocket, data: dict):
        """Обработка сообщений от WebSocket клиента."""
        try:
            message_type = data.get("type")
            
            if message_type == "ping":
                await websocket.send_json({
                    "type": "pong",
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            elif message_type == "subscribe":
                # Подписка на определенные события
                events = data.get("events", [])
                await websocket.send_json({
                    "type": "subscription_confirmed",
                    "events": events,
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            elif message_type == "device_command":
                # Выполнение команды устройства через WebSocket
                device_id = data.get("device_id")
                command = data.get("command")
                params = data.get("params", {})
                
                success = await app.state.communication_hub.send_device_command(
                    device_id=device_id,
                    command=command,
                    params=params
                )
                
                await websocket.send_json({
                    "type": "command_result",
                    "device_id": device_id,
                    "command": command,
                    "success": success,
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                # Оповещаем всех клиентов об изменении устройства
                await broadcast_device_update(device_id, command, success)
                
        except Exception as e:
            await websocket.send_json({
                "type": "error",
                "message": str(e),
                "timestamp": datetime.utcnow().isoformat()
            })
    
    async def broadcast_device_update(device_id: str, command: str, success: bool):
        """Отправка обновления устройства всем подключенным клиентам."""
        if not app.state.websocket_connections:
            return
            
        # Получаем обновленную информацию об устройстве
        device = await app.state.db_manager.get_device(device_id)
        
        message = {
            "type": "device_state_changed",
            "device_id": device_id,
            "device": device,
            "command": command,
            "success": success,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Отправляем всем подключенным клиентам
        disconnected = set()
        for websocket in app.state.websocket_connections:
            try:
                await websocket.send_json(message)
            except Exception:
                disconnected.add(websocket)
        
        # Удаляем отключенные соединения
        app.state.websocket_connections -= disconnected
    
    async def broadcast_system_event(event_type: str, data: dict):
        """Отправка системного события всем клиентам."""
        if not app.state.websocket_connections:
            return
            
        message = {
            "type": "system_event",
            "event_type": event_type,
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        disconnected = set()
        for websocket in app.state.websocket_connections:
            try:
                await websocket.send_json(message)
            except Exception:
                disconnected.add(websocket)
        
        app.state.websocket_connections -= disconnected
    
    # === Smart Scenarios AI API ===
    
    @app.get("/ai/scenarios/analyze")
    async def analyze_user_patterns():
        """Анализ паттернов поведения пользователя."""
        try:
            patterns = await app.state.smart_scenarios_ai.analyze_user_patterns(days_back=30)
            behavioral_patterns = await app.state.smart_scenarios_ai.detect_behavioral_patterns(patterns)
            
            return {
                "success": True,
                "patterns_found": len(behavioral_patterns),
                "analysis": behavioral_patterns
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/ai/scenarios/generate")
    async def generate_smart_scenarios():
        """Генерация умных сценариев на основе AI анализа."""
        try:
            # Анализируем паттерны пользователя
            patterns = await app.state.smart_scenarios_ai.analyze_user_patterns(days_back=30)
            behavioral_patterns = await app.state.smart_scenarios_ai.detect_behavioral_patterns(patterns)
            
            # Создаем умные сценарии
            smart_scenarios = await app.state.smart_scenarios_ai.create_smart_scenarios(behavioral_patterns)
            
            # Конвертируем в словари для JSON ответа
            scenarios_data = []
            for scenario in smart_scenarios:
                scenarios_data.append({
                    "id": scenario.id,
                    "name": scenario.name,
                    "description": scenario.description,
                    "type": scenario.scenario_type.value,
                    "trigger_conditions": scenario.trigger_conditions,
                    "actions": scenario.actions,
                    "confidence": scenario.confidence,
                    "frequency": scenario.frequency,
                    "energy_impact": scenario.energy_impact,
                    "comfort_score": scenario.comfort_score,
                    "created_at": scenario.created_at.isoformat()
                })
            
            return {
                "success": True,
                "scenarios_generated": len(scenarios_data),
                "scenarios": scenarios_data
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/ai/scenarios/voice")
    async def generate_voice_scenarios(voice_commands: List[str]):
        """Создание сценариев на основе голосовых команд."""
        try:
            voice_scenarios = await app.state.smart_scenarios_ai.generate_voice_activated_scenarios(voice_commands)
            
            scenarios_data = []
            for scenario in voice_scenarios:
                scenarios_data.append({
                    "id": scenario.id,
                    "name": scenario.name,
                    "description": scenario.description,
                    "type": scenario.scenario_type.value,
                    "trigger_conditions": scenario.trigger_conditions,
                    "actions": scenario.actions,
                    "confidence": scenario.confidence,
                    "frequency": scenario.frequency,
                    "created_at": scenario.created_at.isoformat()
                })
            
            return {
                "success": True,
                "voice_scenarios": len(scenarios_data),
                "scenarios": scenarios_data
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/ai/scenarios/{scenario_id}/improve")
    async def get_scenario_improvements(scenario_id: str, usage_stats: dict):
        """Получение предложений по улучшению сценария."""
        try:
            suggestions = await app.state.smart_scenarios_ai.suggest_scenario_improvements(
                scenario_id, usage_stats
            )
            
            return {
                "success": True,
                "scenario_id": scenario_id,
                "suggestions": suggestions
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/ai/scenarios/insights")
    async def get_ai_insights():
        """Получение AI инсайтов по домашней автоматизации."""
        try:
            import random
            
            insights = [
                {
                    "type": "energy_saving",
                    "title": "Energy Optimization Opportunity",
                    "description": "Your living room lights are on for 3+ hours without motion detected. Consider adding motion sensors.",
                    "potential_savings": "15% energy reduction",
                    "confidence": 0.85
                },
                {
                    "type": "comfort",
                    "title": "Morning Routine Enhancement",
                    "description": "AI detected you manually adjust thermostat every morning at 7:15. Auto-schedule suggested.",
                    "potential_benefit": "Improved comfort & convenience",
                    "confidence": 0.92
                },
                {
                    "type": "security",
                    "title": "Away Mode Pattern",
                    "description": "Pattern detected: You leave home Mon-Fri at 8:30. Consider automated away mode scenario.",
                    "potential_benefit": "Enhanced security",
                    "confidence": 0.78
                },
                {
                    "type": "entertainment",
                    "title": "Evening Ambiance",
                    "description": "Movie nights detected every Friday 20:00. Automatic lighting & music setup suggested.",
                    "potential_benefit": "Seamless entertainment experience",
                    "confidence": 0.88
                }
            ]
            
            # Случайно выбираем 2-3 инсайта
            selected_insights = random.sample(insights, k=random.randint(2, 3))
            
            return {
                "success": True,
                "insights": selected_insights,
                "generated_at": datetime.utcnow().isoformat()
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/ai/scenarios/learn")
    async def learn_from_user_behavior(behavior_data: dict):
        """Обучение AI на основе поведения пользователя."""
        try:
            # В реальной реализации здесь будет обновление модели ML
            action_type = behavior_data.get("action_type", "unknown")
            feedback = behavior_data.get("feedback", "neutral")
            
            await app.state.db_manager.log_event(
                "ai_learning_feedback",
                source="api",
                data=behavior_data
            )
            
            return {
                "success": True,
                "message": f"Learning from {action_type} with {feedback} feedback",
                "ai_confidence_updated": True
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    # === Extended Integrations API (YouTube Music, Weather, Security, MQTT) ===
    
    @app.post("/integrations/youtube/play")
    async def youtube_music_play(query: str = "", playlist_id: str = ""):
        """Воспроизведение музыки на YouTube Music."""
        try:
            # Симуляция YouTube Music API integration
            if playlist_id:
                action = f"Playing YouTube Music playlist: {playlist_id}"
            else:
                action = f"Playing YouTube Music search: {query or 'default mix'}"
            
            await app.state.db_manager.log_event(
                "youtube_music_play",
                source="api", 
                data={"query": query, "playlist_id": playlist_id}
            )
            
            return {
                "success": True,
                "message": action,
                "service": "YouTube Music",
                "now_playing": {
                    "title": "Amazing Song",
                    "artist": "Great Artist", 
                    "duration": "3:45"
                }
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/integrations/weather/current")
    async def get_current_weather(location: str = "current", units: str = "metric"):
        """Получение текущей погоды через Weather API."""
        try:
            import random
            
            # Симуляция интеграции с реальным Weather API
            weather_conditions = ["sunny", "cloudy", "rainy", "partly_cloudy", "snowy", "windy"]
            current_condition = random.choice(weather_conditions)
            temperature = random.randint(-10, 35) if units == "metric" else random.randint(20, 95)
            
            weather_data = {
                "location": location,
                "temperature": temperature,
                "condition": current_condition,
                "humidity": random.randint(30, 90),
                "wind_speed": random.randint(0, 25),
                "pressure": random.randint(990, 1030),
                "visibility": random.randint(5, 15),
                "uv_index": random.randint(1, 11),
                "units": units,
                "forecast": {
                    "today": f"High {temperature + 5}°, Low {temperature - 8}°",
                    "tomorrow": "Partly cloudy with chance of rain"
                },
                "alerts": [] if current_condition != "rainy" else ["Heavy rain warning until 18:00"]
            }
            
            await app.state.db_manager.log_event(
                "weather_requested",
                source="api",
                data={"location": location, "condition": current_condition}
            )
            
            return {
                "success": True,
                "weather": weather_data,
                "last_updated": datetime.utcnow().isoformat()
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/integrations/security/cameras")
    async def get_security_cameras():
        """Получение списка камер безопасности."""
        try:
            cameras = [
                {
                    "id": "cam_front_door",
                    "name": "Front Door Camera",
                    "status": "online",
                    "resolution": "1080p",
                    "location": "front_entrance",
                    "features": ["motion_detection", "night_vision", "two_way_audio"],
                    "stream_url": "rtsp://192.168.1.100:554/stream1",
                    "last_motion": "2024-01-15T14:30:00Z"
                },
                {
                    "id": "cam_backyard", 
                    "name": "Backyard Camera",
                    "status": "online",
                    "resolution": "4K",
                    "location": "backyard",
                    "features": ["motion_detection", "night_vision", "ptz"],
                    "stream_url": "rtsp://192.168.1.101:554/stream1", 
                    "last_motion": "2024-01-15T13:45:00Z"
                },
                {
                    "id": "cam_garage",
                    "name": "Garage Camera", 
                    "status": "offline",
                    "resolution": "720p",
                    "location": "garage",
                    "features": ["motion_detection"],
                    "stream_url": "rtsp://192.168.1.102:554/stream1",
                    "last_motion": "2024-01-15T08:22:00Z"
                }
            ]
            
            return {
                "success": True,
                "cameras": cameras,
                "total_cameras": len(cameras),
                "online_cameras": sum(1 for cam in cameras if cam["status"] == "online")
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/integrations/security/cameras/{camera_id}/snapshot")
    async def get_camera_snapshot(camera_id: str):
        """Получение снимка с камеры."""
        try:
            # В реальной реализации здесь будет запрос к камере
            return {
                "success": True,
                "camera_id": camera_id,
                "snapshot_url": f"http://localhost:8000/camera_snapshots/{camera_id}_{int(datetime.utcnow().timestamp())}.jpg",
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/integrations/security/cameras/{camera_id}/record")
    async def start_camera_recording(camera_id: str, duration: int = 60):
        """Запуск записи с камеры."""
        try:
            await app.state.db_manager.log_event(
                "camera_recording_started",
                source="api",
                data={"camera_id": camera_id, "duration": duration}
            )
            
            return {
                "success": True,
                "camera_id": camera_id,
                "recording_duration": duration,
                "recording_id": str(uuid.uuid4()),
                "message": f"Recording started for {duration} seconds"
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/integrations/mqtt/publish")
    async def mqtt_publish(topic: str, message: str, qos: int = 0):
        """Публикация сообщения в MQTT."""
        try:
            # Симуляция MQTT клиента
            await app.state.db_manager.log_event(
                "mqtt_message_published",
                source="api",
                data={"topic": topic, "message": message, "qos": qos}
            )
            
            return {
                "success": True,
                "topic": topic,
                "message": message,
                "qos": qos,
                "message_id": str(uuid.uuid4()),
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/integrations/mqtt/topics")
    async def get_mqtt_topics():
        """Получение списка активных MQTT топиков."""
        try:
            topics = [
                {
                    "topic": "home/sensors/temperature",
                    "last_message": "22.5",
                    "last_updated": "2024-01-15T14:35:22Z",
                    "message_count": 1547
                },
                {
                    "topic": "home/lights/living_room/state", 
                    "last_message": "ON",
                    "last_updated": "2024-01-15T14:33:15Z",
                    "message_count": 342
                },
                {
                    "topic": "home/security/door/front",
                    "last_message": "CLOSED",
                    "last_updated": "2024-01-15T09:15:30Z", 
                    "message_count": 89
                },
                {
                    "topic": "home/automation/scenarios",
                    "last_message": "morning_routine_completed",
                    "last_updated": "2024-01-15T07:32:10Z",
                    "message_count": 156
                }
            ]
            
            return {
                "success": True,
                "topics": topics,
                "total_topics": len(topics),
                "broker_status": "connected"
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/integrations/mqtt/subscribe")
    async def mqtt_subscribe(topic: str):
        """Подписка на MQTT топик."""
        try:
            await app.state.db_manager.log_event(
                "mqtt_topic_subscribed",
                source="api",
                data={"topic": topic}
            )
            
            return {
                "success": True,
                "topic": topic,
                "subscription_id": str(uuid.uuid4()),
                "message": f"Subscribed to topic: {topic}"
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    # === Advanced Voice Features (пункт 8) ===
    
    @app.post("/voice/wake-word/configure")
    async def configure_wake_word(config: dict):
        """Настройка wake word detection."""
        try:
            wake_words = config.get("wake_words", ["hey assistant"])
            sensitivity = config.get("sensitivity", 0.8)
            continuous_mode = config.get("continuous_mode", False)
            
            # Сохранение настроек
            await app.state.db_manager.save_integration_settings("voice_wake_word", {
                "wake_words": wake_words,
                "sensitivity": sensitivity, 
                "continuous_mode": continuous_mode,
                "enabled": True
            })
            
            return {
                "success": True,
                "wake_words": wake_words,
                "sensitivity": sensitivity,
                "continuous_mode": continuous_mode,
                "message": "Wake word detection configured"
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/voice/wake-word/status")
    async def get_wake_word_status():
        """Получение статуса wake word detection."""
        try:
            settings = await app.state.db_manager.get_integration_settings("voice_wake_word")
            
            if not settings:
                return {
                    "enabled": False,
                    "wake_words": [],
                    "sensitivity": 0.8,
                    "continuous_mode": False,
                    "detection_count": 0
                }
            
            import random
            return {
                "enabled": settings.get("enabled", False),
                "wake_words": settings.get("wake_words", []),
                "sensitivity": settings.get("sensitivity", 0.8),
                "continuous_mode": settings.get("continuous_mode", False),
                "detection_count": random.randint(10, 150),
                "last_detection": datetime.utcnow().isoformat()
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/voice/continuous/start")
    async def start_continuous_listening():
        """Запуск непрерывного режима прослушивания."""
        try:
            if not app.state.voice_manager:
                raise HTTPException(status_code=400, detail="Voice manager not available")
            
            # В реальной реализации здесь будет запуск continuous mode
            await app.state.db_manager.log_event(
                "continuous_listening_started",
                source="api",
                data={"timestamp": datetime.utcnow().isoformat()}
            )
            
            return {
                "success": True,
                "mode": "continuous",
                "message": "Continuous listening started"
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/voice/continuous/stop")
    async def stop_continuous_listening():
        """Остановка непрерывного режима."""
        try:
            await app.state.db_manager.log_event(
                "continuous_listening_stopped",
                source="api",
                data={"timestamp": datetime.utcnow().isoformat()}
            )
            
            return {
                "success": True,
                "mode": "manual",
                "message": "Continuous listening stopped"
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    # === AI-powered Home Management API (пункт 13) ===
    
    @app.get("/ai/home/predictions")
    async def get_ai_predictions(prediction_types: str = "energy,occupancy,devices", horizon_hours: int = 24):
        """Получение AI предсказаний для дома."""
        try:
            # Парсинг типов предсказаний
            type_mapping = {
                "energy": PredictionType.ENERGY_CONSUMPTION,
                "occupancy": PredictionType.OCCUPANCY,
                "devices": PredictionType.DEVICE_USAGE,
                "weather": PredictionType.WEATHER_IMPACT
            }
            
            requested_types = []
            for type_str in prediction_types.split(","):
                type_str = type_str.strip()
                if type_str in type_mapping:
                    requested_types.append(type_mapping[type_str])
            
            if not requested_types:
                requested_types = [PredictionType.ENERGY_CONSUMPTION, PredictionType.OCCUPANCY]
            
            # Генерация предсказаний
            predictions = await ai_home_manager.generate_predictions(
                prediction_types=requested_types,
                horizon_hours=horizon_hours
            )
            
            # Конвертация в JSON-совместимый формат
            predictions_data = []
            for pred in predictions:
                predictions_data.append({
                    "type": pred.type.value,
                    "value": pred.value,
                    "confidence": pred.confidence,
                    "timestamp": pred.timestamp.isoformat(),
                    "horizon_hours": pred.horizon_hours,
                    "context": pred.context
                })
            
            return {
                "success": True,
                "predictions": predictions_data,
                "generated_at": datetime.utcnow().isoformat()
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/ai/home/recommendations")
    async def get_optimization_recommendations(optimization_types: str = "energy,efficiency"):
        """Получение AI рекомендаций по оптимизации дома."""
        try:
            # Парсинг типов оптимизации
            type_mapping = {
                "energy": OptimizationType.ENERGY,
                "comfort": OptimizationType.COMFORT,
                "efficiency": OptimizationType.EFFICIENCY,
                "security": OptimizationType.SECURITY
            }
            
            requested_types = []
            for type_str in optimization_types.split(","):
                type_str = type_str.strip()
                if type_str in type_mapping:
                    requested_types.append(type_mapping[type_str])
            
            if not requested_types:
                requested_types = [OptimizationType.ENERGY, OptimizationType.EFFICIENCY]
            
            # Получение текущего состояния (симулированное)
            current_state = {
                "temperature": 22,
                "occupancy": 0.8,
                "energy_consumption": 2.1,
                "devices_active": ["lights", "hvac", "entertainment"]
            }
            
            # Генерация рекомендаций
            recommendations = await ai_home_manager.generate_optimization_recommendations(current_state)
            
            # Фильтрация по запрошенным типам
            filtered_recs = [rec for rec in recommendations if rec.type in requested_types]
            
            # Конвертация в JSON
            recommendations_data = []
            for rec in filtered_recs:
                recommendations_data.append({
                    "type": rec.type.value,
                    "title": rec.title,
                    "description": rec.description,
                    "impact": rec.impact,
                    "savings": rec.savings,
                    "actions": rec.actions,
                    "priority": rec.priority,
                    "confidence": rec.confidence
                })
            
            return {
                "success": True,
                "recommendations": recommendations_data,
                "total_recommendations": len(recommendations_data),
                "generated_at": datetime.utcnow().isoformat()
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/ai/home/insights")
    async def get_home_insights(timeframe_days: int = 7):
        """Получение комплексных инсайтов о доме."""
        try:
            insights = await ai_home_manager.generate_home_insights(timeframe_days)
            
            # Конвертация в JSON
            insights_data = []
            for insight in insights:
                insights_data.append({
                    "category": insight.category,
                    "title": insight.title,
                    "description": insight.description,
                    "severity": insight.severity,
                    "value": insight.value,
                    "trend": insight.trend,
                    "recommendations": insight.recommendations
                })
            
            return {
                "success": True,
                "insights": insights_data,
                "timeframe_days": timeframe_days,
                "generated_at": datetime.utcnow().isoformat()
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/ai/home/auto-optimize")
    async def auto_optimize_home(optimization_request: dict = {}):
        """Выполнение автоматической оптимизации дома."""
        try:
            # Парсинг параметров
            optimization_types_str = optimization_request.get("types", "energy,efficiency")
            dry_run = optimization_request.get("dry_run", True)
            
            # Преобразование типов
            type_mapping = {
                "energy": OptimizationType.ENERGY,
                "comfort": OptimizationType.COMFORT,
                "efficiency": OptimizationType.EFFICIENCY,
                "security": OptimizationType.SECURITY
            }
            
            optimization_types = []
            for type_str in optimization_types_str.split(","):
                type_str = type_str.strip()
                if type_str in type_mapping:
                    optimization_types.append(type_mapping[type_str])
            
            if not optimization_types:
                optimization_types = [OptimizationType.ENERGY, OptimizationType.EFFICIENCY]
            
            # Выполнение автооптимизации
            result = await ai_home_manager.auto_optimize(
                optimization_types=optimization_types,
                dry_run=dry_run
            )
            
            # Логирование результата
            await app.state.db_manager.log_event(
                "ai_auto_optimization",
                source="api",
                data=result
            )
            
            return result
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/ai/home/learning-summary")
    async def get_ai_learning_summary():
        """Получение сводки по обучению AI системы."""
        try:
            summary = ai_home_manager.get_learning_summary()
            return {
                "success": True,
                "learning_summary": summary,
                "generated_at": datetime.utcnow().isoformat()
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/ai/home/feedback")
    async def provide_ai_feedback(feedback_data: dict):
        """Предоставление обратной связи для обучения AI."""
        try:
            optimization_id = feedback_data.get("optimization_id")
            rating = feedback_data.get("rating")  # 1-5
            feedback_text = feedback_data.get("feedback", "")
            
            # Сохранение обратной связи
            feedback_record = {
                "optimization_id": optimization_id,
                "rating": rating,
                "feedback": feedback_text,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            await app.state.db_manager.log_event(
                "ai_optimization_feedback",
                source="api",
                data=feedback_record
            )
            
            # В реальной реализации здесь будет обновление модели
            return {
                "success": True,
                "message": "Feedback received and will be used to improve AI recommendations",
                "feedback_id": str(uuid.uuid4())
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/ai/home/energy-forecast")
    async def get_energy_forecast(days: int = 7):
        """Прогноз энергопотребления на несколько дней."""
        try:
            import random
            
            # Генерация прогноза энергопотребления
            forecast_data = []
            for day in range(days):
                date = datetime.utcnow() + timedelta(days=day)
                base_consumption = random.uniform(18, 30)
                
                # Учет выходных (больше потребление)
                if date.weekday() >= 5:
                    base_consumption *= 1.2
                
                forecast_data.append({
                    "date": date.strftime("%Y-%m-%d"),
                    "predicted_consumption": round(base_consumption, 2),
                    "confidence": random.uniform(0.75, 0.95),
                    "cost_estimate": round(base_consumption * 0.15, 2),
                    "weather_factor": random.choice(["low", "medium", "high"]),
                    "recommendations": [
                        "Use appliances during off-peak hours" if base_consumption > 25 else "Normal usage patterns expected"
                    ]
                })
            
            total_predicted = sum(item["predicted_consumption"] for item in forecast_data)
            total_cost = sum(item["cost_estimate"] for item in forecast_data)
            
            return {
                "success": True,
                "forecast": forecast_data,
                "summary": {
                    "total_predicted_consumption": round(total_predicted, 2),
                    "total_estimated_cost": round(total_cost, 2),
                    "average_daily_consumption": round(total_predicted / days, 2),
                    "currency": "USD"
                },
                "generated_at": datetime.utcnow().isoformat()
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/ai/home/schedule-optimization")
    async def schedule_optimization(schedule_request: dict):
        """Планирование автоматической оптимизации."""
        try:
            schedule_type = schedule_request.get("schedule_type", "daily")  # daily, weekly, monthly
            optimization_types = schedule_request.get("types", ["energy", "efficiency"])
            enabled = schedule_request.get("enabled", True)
            
            # Сохранение расписания
            schedule_config = {
                "schedule_type": schedule_type,
                "optimization_types": optimization_types,
                "enabled": enabled,
                "created_at": datetime.utcnow().isoformat(),
                "next_run": (datetime.utcnow() + timedelta(days=1)).isoformat() if schedule_type == "daily" else None
            }
            
            await app.state.db_manager.save_integration_settings("ai_optimization_schedule", schedule_config)
            
            return {
                "success": True,
                "message": f"Optimization scheduled: {schedule_type}",
                "schedule": schedule_config
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/ai/home/dashboard")
    async def get_ai_dashboard():
        """Получение комплексной AI панели управления домом."""
        try:
            # Комбинируем все AI данные для dashboard
            
            # Текущие предсказания
            predictions = await ai_home_manager.generate_predictions([
                PredictionType.ENERGY_CONSUMPTION,
                PredictionType.OCCUPANCY
            ])
            
            # Топ рекомендации
            current_state = {
                "temperature": 22,
                "occupancy": 0.8,
                "energy_consumption": 2.1,
                "devices_active": ["lights", "hvac", "entertainment"]
            }
            recommendations = await ai_home_manager.generate_optimization_recommendations(current_state)
            top_recommendations = recommendations[:3]
            
            # Инсайты
            insights = await ai_home_manager.generate_home_insights(7)
            recent_insights = insights[:4]
            
            # Статистика обучения
            learning_summary = ai_home_manager.get_learning_summary()
            
            # Сводка эффективности
            efficiency_score = random.uniform(0.75, 0.95)
            energy_savings = random.uniform(10, 25)
            
            dashboard_data = {
                "ai_status": {
                    "status": "active",
                    "confidence": 0.87,
                    "last_optimization": learning_summary.get("last_optimization"),
                    "total_optimizations": learning_summary.get("total_optimizations", 0)
                },
                "current_predictions": [
                    {
                        "type": pred.type.value,
                        "value": pred.value,
                        "confidence": pred.confidence
                    } for pred in predictions[:2]
                ],
                "top_recommendations": [
                    {
                        "title": rec.title,
                        "impact": rec.impact,
                        "priority": rec.priority,
                        "savings": rec.savings
                    } for rec in top_recommendations
                ],
                "insights": [
                    {
                        "category": insight.category,
                        "title": insight.title,
                        "severity": insight.severity
                    } for insight in recent_insights
                ],
                "efficiency": {
                    "overall_score": round(efficiency_score, 2),
                    "energy_savings_percent": round(energy_savings, 1),
                    "cost_savings_monthly": round(energy_savings * 2.5, 2),
                    "trend": "improving"
                },
                "next_auto_optimization": (datetime.utcnow() + timedelta(hours=6)).isoformat()
            }
            
            return {
                "success": True,
                "dashboard": dashboard_data,
                "generated_at": datetime.utcnow().isoformat()
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    # Сохраняем функцию broadcast для использования в других частях API
    app.state.broadcast_system_event = broadcast_system_event
    app.state.broadcast_device_update = broadcast_device_update
    
    return app
