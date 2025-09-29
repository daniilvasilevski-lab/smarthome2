/**
 * Enhanced Home Assistant AI Web Application
 * Полнофункциональное приложение с WiFi и Spotify интеграцией
 */

class EnhancedHomeAssistantUI {
    constructor() {
        this.currentLanguage = localStorage.getItem('language') || 'en';
        this.isVoiceListening = false;
        this.wifiNetworks = [];
        this.spotifyConnected = false;
        this.currentTrack = null;
        
        this.translations = {
            en: {
                appTitle: 'Home Assistant AI',
                welcome: 'Welcome to your Smart Home',
                voiceInstructions: 'Tap the microphone to talk to your AI assistant',
                listening: 'Listening...',
                processing: 'Processing...',
                devices: 'Devices',
                scenarios: 'Scenarios',
                settings: 'Settings',
                analytics: 'Analytics',
                wifiTitle: 'WiFi Setup',
                spotifyTitle: 'Spotify',
                connected: 'Connected',
                disconnected: 'Disconnected',
                scanNetworks: 'Scan Networks',
                connectToSpotify: 'Connect to Spotify',
                disconnect: 'Disconnect',
                save: 'Save',
                cancel: 'Cancel',
                connecting: 'Connecting...',
                scanningNetworks: 'Scanning networks...',
                password: 'Password',
                networkName: 'Network Name',
                securityType: 'Security Type',
                signalStrength: 'Signal Strength',
                currentTrack: 'Current Track',
                volume: 'Volume',
                play: 'Play',
                pause: 'Pause',
                next: 'Next',
                previous: 'Previous',
                clientId: 'Client ID',
                clientSecret: 'Client Secret',
                redirectUri: 'Redirect URI',
                authenticationSuccess: 'Authentication successful!',
                connectionFailed: 'Connection failed',
                energyUsage: 'Energy Usage',
                deviceUsage: 'Device Usage',
                scenarios: 'Scenarios',
                createScenario: 'Create Scenario',
                executeScenario: 'Execute',
                editScenario: 'Edit',
                deleteScenario: 'Delete'
            },
            ru: {
                appTitle: 'Home Assistant AI',
                welcome: 'Добро пожаловать в ваш Умный Дом',
                voiceInstructions: 'Нажмите на микрофон для общения с ИИ ассистентом',
                listening: 'Слушаю...',
                processing: 'Обрабатываю...',
                devices: 'Устройства',
                scenarios: 'Сценарии',
                settings: 'Настройки',
                analytics: 'Аналитика',
                wifiTitle: 'Настройка WiFi',
                spotifyTitle: 'Spotify',
                connected: 'Подключено',
                disconnected: 'Отключено',
                scanNetworks: 'Сканировать сети',
                connectToSpotify: 'Подключить Spotify',
                disconnect: 'Отключить',
                save: 'Сохранить',
                cancel: 'Отмена',
                connecting: 'Подключение...',
                scanningNetworks: 'Сканирование сетей...',
                password: 'Пароль',
                networkName: 'Имя сети',
                securityType: 'Тип защиты',
                signalStrength: 'Уровень сигнала',
                currentTrack: 'Текущий трек',
                volume: 'Громкость',
                play: 'Воспроизвести',
                pause: 'Пауза',
                next: 'Следующий',
                previous: 'Предыдущий',
                clientId: 'ID клиента',
                clientSecret: 'Секрет клиента',
                redirectUri: 'URI перенаправления',
                authenticationSuccess: 'Аутентификация успешна!',
                connectionFailed: 'Ошибка подключения',
                energyUsage: 'Потребление энергии',
                deviceUsage: 'Использование устройств',
                scenarios: 'Сценарии',
                createScenario: 'Создать сценарий',
                executeScenario: 'Выполнить',
                editScenario: 'Редактировать',
                deleteScenario: 'Удалить'
            },
            pl: {
                appTitle: 'Home Assistant AI',
                welcome: 'Witaj w swoim Inteligentnym Domu',
                voiceInstructions: 'Dotknij mikrofon, aby porozmawiać z asystentem AI',
                listening: 'Słucham...',
                processing: 'Przetwarzam...',
                devices: 'Urządzenia',
                scenarios: 'Scenariusze',
                settings: 'Ustawienia',
                analytics: 'Analityka',
                wifiTitle: 'Konfiguracja WiFi',
                spotifyTitle: 'Spotify',
                connected: 'Połączono',
                disconnected: 'Rozłączono',
                scanNetworks: 'Skanuj sieci',
                connectToSpotify: 'Połącz ze Spotify',
                disconnect: 'Rozłącz',
                save: 'Zapisz',
                cancel: 'Anuluj',
                connecting: 'Łączenie...',
                scanningNetworks: 'Skanowanie sieci...',
                password: 'Hasło',
                networkName: 'Nazwa sieci',
                securityType: 'Typ zabezpieczeń',
                signalStrength: 'Siła sygnału',
                currentTrack: 'Bieżący utwór',
                volume: 'Głośność',
                play: 'Odtwórz',
                pause: 'Pauza',
                next: 'Następny',
                previous: 'Poprzedni',
                clientId: 'ID klienta',
                clientSecret: 'Sekret klienta',
                redirectUri: 'URI przekierowania',
                authenticationSuccess: 'Uwierzytelnienie pomyślne!',
                connectionFailed: 'Błąd połączenia',
                energyUsage: 'Zużycie energii',
                deviceUsage: 'Użycie urządzeń',
                scenarios: 'Scenariusze',
                createScenario: 'Utwórz scenariusz',
                executeScenario: 'Wykonaj',
                editScenario: 'Edytuj',
                deleteScenario: 'Usuń'
            }
        };
        
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.updateLanguage();
        this.loadStatus();
        this.checkSpotifyStatus();
        this.checkWiFiStatus();
        
        // Обрабатываем URL параметры для PWA shortcuts
        this.handleURLParams();
        
        // Обновление статуса каждые 30 секунд
        setInterval(() => {
            this.loadStatus();
            this.checkSpotifyStatus();
        }, 30000);
    }

    setupEventListeners() {
        // Переключатель языка
        const languageSelect = document.getElementById('languageSelect');
        if (languageSelect) {
            languageSelect.value = this.currentLanguage;
            languageSelect.addEventListener('change', (e) => {
                this.setLanguage(e.target.value);
            });
        }

        // Кнопка голосового управления
        const voiceBtn = document.getElementById('voiceButton');
        if (voiceBtn) {
            voiceBtn.addEventListener('click', () => this.toggleVoice());
        }

        // Кнопки вкладок
        document.querySelectorAll('.tab').forEach(tab => {
            tab.addEventListener('click', (e) => {
                this.switchTab(e.target.dataset.tab);
            });
        });

        // Кнопка отправки сообщения
        const sendBtn = document.getElementById('sendMessage');
        if (sendBtn) {
            sendBtn.addEventListener('click', () => this.sendMessage());
        }

        // Enter в поле ввода
        const chatInput = document.getElementById('chatInput');
        if (chatInput) {
            chatInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.sendMessage();
                }
            });
        }
    }

    translate(key) {
        return this.translations[this.currentLanguage][key] || key;
    }

    setLanguage(lang) {
        this.currentLanguage = lang;
        localStorage.setItem('language', lang);
        this.updateLanguage();
    }

    updateLanguage() {
        // Обновляем текстовые элементы
        document.querySelectorAll('[data-translate]').forEach(element => {
            const key = element.dataset.translate;
            element.textContent = this.translate(key);
        });

        // Обновляем placeholder'ы
        document.querySelectorAll('[data-translate-placeholder]').forEach(element => {
            const key = element.dataset.translatePlaceholder;
            element.placeholder = this.translate(key);
        });

        // Обновляем title'ы
        document.querySelectorAll('[data-translate-title]').forEach(element => {
            const key = element.dataset.translateTitle;
            element.title = this.translate(key);
        });
    }

    async loadStatus() {
        try {
            const response = await fetch('/status');
            const data = await response.json();
            
            if (data) {
                this.updateStatusDisplay(data);
            }
        } catch (error) {
            console.error('Failed to load status:', error);
        }
    }

    updateStatusDisplay(status) {
        // Обновляем счетчики устройств
        const deviceCount = document.getElementById('deviceCount');
        if (deviceCount) {
            deviceCount.textContent = status.devices_count || 0;
        }

        // Обновляем статус ИИ
        const aiStatus = document.getElementById('aiStatus');
        if (aiStatus) {
            aiStatus.textContent = status.ai_provider || 'Unknown';
        }
    }

    switchTab(tabName) {
        // Скрываем все контенты
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.add('hidden');
        });

        // Убираем активный класс со всех вкладок
        document.querySelectorAll('.tab').forEach(tab => {
            tab.classList.remove('active');
        });

        // Показываем нужный контент
        const targetContent = document.getElementById(tabName + 'Content');
        if (targetContent) {
            targetContent.classList.remove('hidden');
        }

        // Активируем вкладку
        const activeTab = document.querySelector(`.tab[data-tab="${tabName}"]`);
        if (activeTab) {
            activeTab.classList.add('active');
        }

        // Загружаем контент для вкладки
        this.loadTabContent(tabName);
    }

    async loadTabContent(tabName) {
        switch (tabName) {
            case 'devices':
                await this.loadDevices();
                break;
            case 'scenarios':
                await this.loadScenarios();
                break;
            case 'analytics':
                await this.loadAnalytics();
                break;
            case 'settings':
                this.loadSettings();
                break;
        }
    }

    async loadDevices() {
        try {
            const response = await fetch('/devices');
            const devices = await response.json();
            
            const devicesList = document.getElementById('devicesList');
            if (devicesList && Array.isArray(devices)) {
                devicesList.innerHTML = devices.map(device => `
                    <div class="device-card" data-device-id="${device.id}">
                        <div class="device-header">
                            <h3>${device.name}</h3>
                            <span class="device-type">${device.device_type}</span>
                        </div>
                        <div class="device-controls">
                            <button class="btn btn-primary" onclick="ui.controlDevice('${device.id}', 'toggle')">
                                ${device.state === 'on' ? 'Turn Off' : 'Turn On'}
                            </button>
                        </div>
                    </div>
                `).join('');
            }
        } catch (error) {
            console.error('Failed to load devices:', error);
        }
    }

    async controlDevice(deviceId, action) {
        try {
            const response = await fetch(`/devices/${deviceId}/action`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ command: action })
            });
            
            const result = await response.json();
            if (result.success) {
                this.showNotification('Device command sent successfully', 'success');
                await this.loadDevices(); // Перезагружаем устройства
            } else {
                this.showNotification('Failed to send device command', 'error');
            }
        } catch (error) {
            console.error('Device control failed:', error);
            this.showNotification('Device control failed', 'error');
        }
    }

    async scanDevices() {
        const scanBtn = document.getElementById('scanDevices');
        if (scanBtn) {
            scanBtn.disabled = true;
            scanBtn.textContent = 'Scanning...';
        }

        try {
            await fetch('/devices/scan', { method: 'POST' });
            this.showNotification('Device scan started', 'success');
            
            // Перезагружаем устройства через 5 секунд
            setTimeout(() => this.loadDevices(), 5000);
        } catch (error) {
            console.error('Device scan failed:', error);
            this.showNotification('Device scan failed', 'error');
        } finally {
            if (scanBtn) {
                scanBtn.disabled = false;
                scanBtn.textContent = 'Scan Devices';
            }
        }
    }

    // WiFi функционал
    async scanWiFiNetworks() {
        const scanBtn = document.getElementById('scanWiFi');
        if (scanBtn) {
            scanBtn.disabled = true;
            scanBtn.textContent = this.translate('scanningNetworks');
        }

        try {
            const response = await fetch('/wifi/networks');
            const data = await response.json();
            
            if (data.success) {
                this.wifiNetworks = data.networks;
                this.displayWiFiNetworks();
                this.showNotification('WiFi networks scanned successfully', 'success');
            } else {
                this.showNotification('Failed to scan WiFi networks', 'error');
            }
        } catch (error) {
            console.error('WiFi scan failed:', error);
            this.showNotification('WiFi scan failed', 'error');
        } finally {
            if (scanBtn) {
                scanBtn.disabled = false;
                scanBtn.textContent = this.translate('scanNetworks');
            }
        }
    }

    displayWiFiNetworks() {
        const networksList = document.getElementById('wifiNetworksList');
        if (!networksList) return;

        networksList.innerHTML = this.wifiNetworks.map(network => `
            <div class="wifi-network ${network.connected ? 'connected' : ''}" onclick="ui.selectWiFiNetwork('${network.ssid}')">
                <div class="network-info">
                    <div class="network-name">${network.ssid}</div>
                    <div class="network-details">
                        <span class="security">${network.security}</span>
                        <span class="signal">
                            <div class="signal-bars">
                                ${this.getSignalBars(network.signal_strength)}
                            </div>
                            ${network.signal_strength}%
                        </span>
                    </div>
                </div>
                ${network.connected ? '<span class="connected-indicator">✓</span>' : ''}
            </div>
        `).join('');
    }

    getSignalBars(strength) {
        const bars = Math.ceil(strength / 25);
        return Array.from({length: 4}, (_, i) => 
            `<div class="bar ${i < bars ? 'active' : ''}"></div>`
        ).join('');
    }

    selectWiFiNetwork(ssid) {
        const network = this.wifiNetworks.find(n => n.ssid === ssid);
        if (!network) return;

        document.getElementById('selectedSSID').value = ssid;
        
        if (network.security !== 'Open') {
            document.getElementById('wifiPasswordSection').style.display = 'block';
            document.getElementById('wifiPassword').focus();
        } else {
            document.getElementById('wifiPasswordSection').style.display = 'none';
        }
    }

    async connectToWiFi() {
        const ssid = document.getElementById('selectedSSID').value;
        const password = document.getElementById('wifiPassword').value;
        
        if (!ssid) {
            this.showNotification('Please select a network', 'error');
            return;
        }

        const connectBtn = document.getElementById('connectWiFi');
        if (connectBtn) {
            connectBtn.disabled = true;
            connectBtn.textContent = this.translate('connecting');
        }

        try {
            const response = await fetch('/wifi/connect', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    ssid: ssid,
                    password: password || null
                })
            });

            const data = await response.json();
            
            if (data.success) {
                this.showNotification(data.message || 'Connected successfully', 'success');
                await this.checkWiFiStatus();
                document.getElementById('wifiPassword').value = '';
            } else {
                this.showNotification(data.message || 'Connection failed', 'error');
            }
        } catch (error) {
            console.error('WiFi connection failed:', error);
            this.showNotification('WiFi connection failed', 'error');
        } finally {
            if (connectBtn) {
                connectBtn.disabled = false;
                connectBtn.textContent = 'Connect';
            }
        }
    }

    async checkWiFiStatus() {
        try {
            const response = await fetch('/wifi/status');
            const status = await response.json();
            
            this.updateWiFiStatus(status);
        } catch (error) {
            console.error('Failed to check WiFi status:', error);
        }
    }

    updateWiFiStatus(status) {
        const statusElement = document.getElementById('wifiStatus');
        if (statusElement) {
            if (status.connected) {
                statusElement.innerHTML = `
                    <div class="status-connected">
                        <span class="status-indicator connected"></span>
                        ${this.translate('connected')} to ${status.ssid}
                        <div class="status-details">
                            Signal: ${status.signal_strength}% | IP: ${status.ip_address}
                        </div>
                    </div>
                `;
            } else {
                statusElement.innerHTML = `
                    <div class="status-disconnected">
                        <span class="status-indicator disconnected"></span>
                        ${this.translate('disconnected')}
                    </div>
                `;
            }
        }
    }

    // Spotify функционал
    async connectSpotify() {
        const clientId = document.getElementById('spotifyClientId').value;
        const clientSecret = document.getElementById('spotifyClientSecret').value;

        if (!clientId || !clientSecret) {
            this.showNotification('Please enter Spotify credentials', 'error');
            return;
        }

        try {
            const response = await fetch('/spotify/auth', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    client_id: clientId,
                    client_secret: clientSecret,
                    redirect_uri: window.location.origin + '/spotify/callback'
                })
            });

            const data = await response.json();
            
            if (data.success) {
                // Открываем окно авторизации Spotify
                const authWindow = window.open(data.auth_url, 'spotify-auth', 'width=500,height=600');
                
                // Ожидаем закрытия окна авторизации
                const checkClosed = setInterval(() => {
                    if (authWindow.closed) {
                        clearInterval(checkClosed);
                        // Проверяем статус подключения
                        setTimeout(() => this.checkSpotifyStatus(), 2000);
                    }
                }, 1000);
            } else {
                this.showNotification('Failed to initiate Spotify authentication', 'error');
            }
        } catch (error) {
            console.error('Spotify authentication failed:', error);
            this.showNotification('Spotify authentication failed', 'error');
        }
    }

    async checkSpotifyStatus() {
        try {
            const response = await fetch('/spotify/status');
            const status = await response.json();
            
            this.updateSpotifyStatus(status);
        } catch (error) {
            console.error('Failed to check Spotify status:', error);
        }
    }

    updateSpotifyStatus(status) {
        const statusElement = document.getElementById('spotifyStatus');
        const connectSection = document.getElementById('spotifyConnect');
        const playerSection = document.getElementById('spotifyPlayer');
        
        this.spotifyConnected = status.connected;

        if (status.connected) {
            if (connectSection) connectSection.style.display = 'none';
            if (playerSection) playerSection.style.display = 'block';
            
            if (status.current_track) {
                this.currentTrack = status.current_track;
                this.updateSpotifyPlayer(status);
            }
            
            if (statusElement) {
                statusElement.innerHTML = `
                    <div class="status-connected">
                        <span class="status-indicator connected"></span>
                        ${this.translate('connected')} to Spotify
                    </div>
                `;
            }
        } else {
            if (connectSection) connectSection.style.display = 'block';
            if (playerSection) playerSection.style.display = 'none';
            
            if (statusElement) {
                statusElement.innerHTML = `
                    <div class="status-disconnected">
                        <span class="status-indicator disconnected"></span>
                        ${this.translate('disconnected')}
                    </div>
                `;
            }
        }
    }

    updateSpotifyPlayer(status) {
        if (!status.current_track) return;

        const track = status.current_track;
        
        // Обновляем информацию о треке
        const trackName = document.getElementById('currentTrackName');
        const trackArtist = document.getElementById('currentTrackArtist');
        const playPauseBtn = document.getElementById('playPauseBtn');
        const volumeSlider = document.getElementById('volumeSlider');

        if (trackName) trackName.textContent = track.name;
        if (trackArtist) trackArtist.textContent = track.artist;
        
        if (playPauseBtn) {
            playPauseBtn.textContent = track.is_playing ? '⏸️' : '▶️';
            playPauseBtn.onclick = () => this.spotifyControl(track.is_playing ? 'pause' : 'play');
        }

        if (volumeSlider) {
            volumeSlider.value = status.volume || 50;
        }

        // Обновляем прогресс трека
        this.updateTrackProgress(track);
    }

    updateTrackProgress(track) {
        const progressBar = document.getElementById('trackProgress');
        if (!progressBar) return;

        const progress = (track.position / track.duration) * 100;
        progressBar.style.width = `${progress}%`;

        // Обновляем времена
        const currentTime = document.getElementById('currentTime');
        const totalTime = document.getElementById('totalTime');
        
        if (currentTime) currentTime.textContent = this.formatTime(track.position);
        if (totalTime) totalTime.textContent = this.formatTime(track.duration);
    }

    formatTime(ms) {
        const minutes = Math.floor(ms / 60000);
        const seconds = Math.floor((ms % 60000) / 1000);
        return `${minutes}:${seconds.toString().padStart(2, '0')}`;
    }

    async spotifyControl(action, value = null) {
        if (!this.spotifyConnected) {
            this.showNotification('Spotify not connected', 'error');
            return;
        }

        try {
            const body = { action };
            if (action === 'volume' && value !== null) {
                body.volume = value;
            }

            const response = await fetch('/spotify/control', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body)
            });

            const data = await response.json();
            
            if (data.success) {
                // Обновляем статус через секунду
                setTimeout(() => this.checkSpotifyStatus(), 1000);
            } else {
                this.showNotification(data.message || 'Spotify control failed', 'error');
            }
        } catch (error) {
            console.error('Spotify control failed:', error);
            this.showNotification('Spotify control failed', 'error');
        }
    }

    async disconnectSpotify() {
        try {
            const response = await fetch('/spotify/disconnect', { method: 'POST' });
            const data = await response.json();
            
            if (data.success) {
                this.showNotification('Spotify disconnected', 'success');
                this.checkSpotifyStatus();
            } else {
                this.showNotification('Failed to disconnect Spotify', 'error');
            }
        } catch (error) {
            console.error('Spotify disconnect failed:', error);
            this.showNotification('Spotify disconnect failed', 'error');
        }
    }

    // Голосовое управление
    async toggleVoice() {
        if (this.isVoiceListening) return;

        const voiceBtn = document.getElementById('voiceButton');
        const voiceInstructions = document.getElementById('voiceInstructions');
        
        this.isVoiceListening = true;
        
        if (voiceBtn) {
            voiceBtn.classList.add('listening');
            voiceBtn.textContent = '🔊';
        }
        
        if (voiceInstructions) {
            voiceInstructions.textContent = this.translate('listening');
        }

        try {
            const response = await fetch('/voice/listen', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ timeout: 5.0 })
            });

            const data = await response.json();
            
            if (data.text) {
                this.addChatMessage(data.text, 'user');
                await this.processMessage(data.text);
            }
        } catch (error) {
            console.error('Voice listening failed:', error);
            this.showNotification('Voice listening failed', 'error');
        } finally {
            this.isVoiceListening = false;
            
            if (voiceBtn) {
                voiceBtn.classList.remove('listening');
                voiceBtn.textContent = '🎤';
            }
            
            if (voiceInstructions) {
                voiceInstructions.textContent = this.translate('voiceInstructions');
            }
        }
    }

    async sendMessage() {
        const chatInput = document.getElementById('chatInput');
        const message = chatInput.value.trim();
        
        if (!message) return;

        chatInput.value = '';
        this.addChatMessage(message, 'user');
        await this.processMessage(message);
    }

    async processMessage(message) {
        const chatContainer = document.getElementById('chatContainer');
        
        // Добавляем индикатор обработки
        const processingDiv = document.createElement('div');
        processingDiv.className = 'chat-message assistant processing';
        processingDiv.innerHTML = `<em>${this.translate('processing')}</em>`;
        chatContainer.appendChild(processingDiv);
        chatContainer.scrollTop = chatContainer.scrollHeight;

        try {
            const response = await fetch('/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message: message,
                    session_id: 'web_session'
                })
            });

            const data = await response.json();
            
            // Убираем индикатор обработки
            chatContainer.removeChild(processingDiv);
            
            if (data.response) {
                this.addChatMessage(data.response, 'assistant');
                
                // Если доступен голос, произносим ответ
                try {
                    await fetch('/voice/speak', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ text: data.response, blocking: false })
                    });
                } catch (voiceError) {
                    // Голос недоступен, продолжаем без произнесения
                }
            }
        } catch (error) {
            // Убираем индикатор обработки
            if (chatContainer.contains(processingDiv)) {
                chatContainer.removeChild(processingDiv);
            }
            
            this.addChatMessage('Sorry, there was an error processing your request.', 'assistant');
            console.error('Message processing failed:', error);
        }
    }

    addChatMessage(message, sender) {
        const chatContainer = document.getElementById('chatContainer');
        const messageDiv = document.createElement('div');
        messageDiv.className = `chat-message ${sender}`;
        messageDiv.textContent = message;
        chatContainer.appendChild(messageDiv);
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }

    // Аналитика
    async loadAnalytics() {
        await Promise.all([
            this.loadEnergyAnalytics(),
            this.loadDeviceAnalytics()
        ]);
    }

    async loadEnergyAnalytics() {
        try {
            const response = await fetch('/analytics/energy');
            const data = await response.json();
            
            if (data.success) {
                this.renderEnergyChart(data);
            }
        } catch (error) {
            console.error('Failed to load energy analytics:', error);
        }
    }

    async loadDeviceAnalytics() {
        try {
            const response = await fetch('/analytics/devices');
            const data = await response.json();
            
            if (data.success) {
                this.renderDeviceChart(data.devices);
            }
        } catch (error) {
            console.error('Failed to load device analytics:', error);
        }
    }

    renderEnergyChart(data) {
        const canvas = document.getElementById('energyChart');
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        
        // Простой график (можно заменить на Chart.js)
        const width = canvas.width;
        const height = canvas.height;
        const maxConsumption = Math.max(...data.data.map(d => d.consumption));
        
        ctx.clearRect(0, 0, width, height);
        ctx.strokeStyle = '#3b82f6';
        ctx.lineWidth = 2;
        ctx.beginPath();
        
        data.data.forEach((point, index) => {
            const x = (index / (data.data.length - 1)) * width;
            const y = height - (point.consumption / maxConsumption) * height;
            
            if (index === 0) {
                ctx.moveTo(x, y);
            } else {
                ctx.lineTo(x, y);
            }
        });
        
        ctx.stroke();
    }

    renderDeviceChart(devices) {
        const container = document.getElementById('deviceUsageChart');
        if (!container) return;

        container.innerHTML = devices.map(device => `
            <div class="device-usage-item">
                <div class="device-name">${device.name}</div>
                <div class="usage-bar">
                    <div class="usage-fill" style="width: ${device.usage}%"></div>
                </div>
                <div class="usage-value">${device.usage}%</div>
            </div>
        `).join('');
    }

    // Сценарии
    async loadScenarios() {
        try {
            const response = await fetch('/scenarios');
            const data = await response.json();
            
            if (data.success) {
                this.displayScenarios(data.scenarios);
            }
        } catch (error) {
            console.error('Failed to load scenarios:', error);
        }
    }

    displayScenarios(scenarios) {
        const container = document.getElementById('scenariosList');
        if (!container) return;

        container.innerHTML = scenarios.map(scenario => `
            <div class="scenario-card">
                <div class="scenario-header">
                    <h3>${scenario.name}</h3>
                    <span class="scenario-status ${scenario.enabled ? 'enabled' : 'disabled'}">
                        ${scenario.enabled ? 'Enabled' : 'Disabled'}
                    </span>
                </div>
                <p class="scenario-description">${scenario.description}</p>
                <div class="scenario-actions">
                    <button class="btn btn-primary" onclick="ui.executeScenario('${scenario.id}')">
                        ${this.translate('executeScenario')}
                    </button>
                    <button class="btn btn-secondary" onclick="ui.toggleScenario('${scenario.id}')">
                        ${scenario.enabled ? 'Disable' : 'Enable'}
                    </button>
                </div>
            </div>
        `).join('');
    }

    async executeScenario(scenarioId) {
        try {
            const response = await fetch(`/scenarios/${scenarioId}/execute`, {
                method: 'POST'
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showNotification('Scenario executed successfully', 'success');
            } else {
                this.showNotification('Failed to execute scenario', 'error');
            }
        } catch (error) {
            console.error('Scenario execution failed:', error);
            this.showNotification('Scenario execution failed', 'error');
        }
    }

    async toggleScenario(scenarioId) {
        try {
            const response = await fetch(`/scenarios/${scenarioId}/toggle`, {
                method: 'POST'
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showNotification('Scenario toggled successfully', 'success');
                await this.loadScenarios(); // Перезагружаем сценарии
            } else {
                this.showNotification('Failed to toggle scenario', 'error');
            }
        } catch (error) {
            console.error('Scenario toggle failed:', error);
            this.showNotification('Scenario toggle failed', 'error');
        }
    }

    // Настройки
    loadSettings() {
        // Загружаем текущие настройки
        this.loadVoiceSettings();
        
        // Инициализируем тему
        this.initializeTheme();
    }

    async loadVoiceSettings() {
        try {
            const response = await fetch('/voice/status');
            const status = await response.json();
            
            if (status) {
                this.updateVoiceSettings(status);
            }
        } catch (error) {
            console.error('Failed to load voice settings:', error);
        }
    }

    updateVoiceSettings(status) {
        const sttProvider = document.getElementById('sttProvider');
        const ttsProvider = document.getElementById('ttsProvider');
        const wakeWords = document.getElementById('wakeWords');

        if (sttProvider) sttProvider.value = status.stt_provider || 'google';
        if (ttsProvider) ttsProvider.value = status.tts_provider || 'pyttsx3';
        if (wakeWords) wakeWords.value = status.wake_words ? status.wake_words.join(', ') : '';
    }

    async saveVoiceSettings() {
        const sttProvider = document.getElementById('sttProvider').value;
        const ttsProvider = document.getElementById('ttsProvider').value;
        const wakeWords = document.getElementById('wakeWords').value;

        try {
            const response = await fetch('/voice/settings', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    stt_provider: sttProvider,
                    tts_provider: ttsProvider,
                    wake_words: wakeWords
                })
            });

            const data = await response.json();
            
            if (data.success) {
                this.showNotification('Voice settings saved', 'success');
            } else {
                this.showNotification('Failed to save voice settings', 'error');
            }
        } catch (error) {
            console.error('Failed to save voice settings:', error);
            this.showNotification('Failed to save voice settings', 'error');
        }
    }

    // Уведомления
    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;
        
        const container = document.getElementById('notificationContainer') || document.body;
        container.appendChild(notification);
        
        // Показываем уведомление
        setTimeout(() => notification.classList.add('show'), 10);
        
        // Убираем через 5 секунд
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => {
                if (container.contains(notification)) {
                    container.removeChild(notification);
                }
            }, 300);
        }, 5000);
    }

    // Система тем
    initializeTheme() {
        const themeSelect = document.getElementById('themeSelect');
        const savedTheme = localStorage.getItem('theme') || 'light';
        
        // Устанавливаем сохраненную тему
        this.applyTheme(savedTheme);
        
        if (themeSelect) {
            themeSelect.value = savedTheme;
            themeSelect.addEventListener('change', (e) => {
                this.setTheme(e.target.value);
            });
        }
    }

    setTheme(theme) {
        localStorage.setItem('theme', theme);
        this.applyTheme(theme);
        this.showNotification(`Theme changed to ${theme}`, 'success');
    }

    applyTheme(theme) {
        // Убираем все классы тем
        document.documentElement.removeAttribute('data-theme');
        
        // Применяем новую тему
        if (theme !== 'light') {
            document.documentElement.setAttribute('data-theme', theme);
        }
        
        // Обновляем meta-тег для PWA
        const themeColorMeta = document.querySelector('meta[name="theme-color"]');
        const colors = {
            light: '#2563eb',
            dark: '#1e293b',
            blue: '#0ea5e9',
            green: '#059669'
        };
        
        if (themeColorMeta) {
            themeColorMeta.setAttribute('content', colors[theme] || colors.light);
        }
    }

    // Обработка URL параметров для PWA shortcuts
    handleURLParams() {
        const urlParams = new URLSearchParams(window.location.search);
        
        // Обработка action параметра
        const action = urlParams.get('action');
        if (action === 'voice') {
            // Активируем голосовое управление
            setTimeout(() => this.toggleVoice(), 500);
        } else if (action === 'spotify') {
            // Открываем Spotify секцию
            this.switchTab('home');
            setTimeout(() => {
                const spotifySection = document.querySelector('.card:nth-child(3)'); // Spotify card
                if (spotifySection) {
                    spotifySection.scrollIntoView({ behavior: 'smooth' });
                }
            }, 100);
        }
        
        // Обработка tab параметра
        const tab = urlParams.get('tab');
        if (tab && ['devices', 'scenarios', 'analytics', 'settings'].includes(tab)) {
            this.switchTab(tab);
        } else if (tab === 'wifi') {
            this.switchTab('home');
            setTimeout(() => {
                const wifiSection = document.querySelector('.card:nth-child(2)'); // WiFi card
                if (wifiSection) {
                    wifiSection.scrollIntoView({ behavior: 'smooth' });
                }
            }, 100);
        }
        
        // Обработка AI сценариев
        const ai = urlParams.get('ai');
        if (ai === 'true' && tab === 'scenarios') {
            setTimeout(() => {
                this.showNotification('AI-powered scenarios activated', 'info');
            }, 1000);
        }
        
        // Очищаем URL от параметров после обработки
        if (urlParams.toString()) {
            const newUrl = window.location.pathname;
            window.history.replaceState({}, document.title, newUrl);
        }
    }
}

// Инициализация приложения
let ui;
document.addEventListener('DOMContentLoaded', () => {
    ui = new EnhancedHomeAssistantUI();
    
    // Регистрируем Service Worker для PWA
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('/static/sw.js');
    }
});

// Глобальные функции для HTML
window.ui = ui;