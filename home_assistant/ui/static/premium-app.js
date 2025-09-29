// Enhanced Home Assistant AI - Premium Interface
class PremiumHomeAssistantUI {
    constructor() {
        this.currentLanguage = 'en';
        this.currentTheme = 'light';
        this.isVoiceListening = false;
        this.devices = [];
        this.hubs = [];
        this.currentHub = null;
        this.translations = {};
        this.notificationQueue = [];
        
        this.init();
    }

    async init() {
        await this.loadTranslations();
        await this.loadHubs();
        this.setupEventListeners();
        this.setupTheme();
        this.updateStatus();
        this.loadDevices();
        
        // Set default language and hub
        const savedLang = localStorage.getItem('language') || 'en';
        const savedTheme = localStorage.getItem('theme') || 'light';
        const savedHub = localStorage.getItem('currentHub') || 'local';
        
        this.setLanguage(savedLang);
        this.setTheme(savedTheme);
        this.setCurrentHub(savedHub);
        
        // Auto-refresh status every 30 seconds
        setInterval(() => this.updateStatus(), 30000);
        
        // Check for first time setup
        this.checkFirstTimeSetup();
    }

    async loadTranslations() {
        this.translations = {
            en: {
                appTitle: "Home Assistant AI",
                appSubtitle: "Your intelligent home automation companion",
                welcomeTitle: "Welcome Home",
                welcomeSubtitle: "Your intelligent AI assistant is ready to help you control your smart home with voice commands and intuitive controls.",
                
                // Navigation
                currentHub: "Current Hub",
                localHub: "Local Hub",
                
                // Voice
                voiceInstructions: "Tap to talk to your AI assistant",
                listening: "Listening...",
                processing: "Processing...",
                speaking: "Speaking...",
                
                // Status
                devices: "Devices",
                hubsConnected: "Hubs Connected",
                voiceAssistant: "Voice Assistant",
                aiReady: "AI Ready",
                online: "Online",
                offline: "Offline",
                partial: "Partial",
                
                // Quick Actions
                devicesTitle: "Smart Devices",
                devicesDescription: "Control your lights, sensors, and smart home devices",
                scenariosTitle: "Automation",
                scenariosDescription: "Create and manage smart home automation scenarios",
                settingsTitle: "Settings",
                settingsDescription: "Configure your assistant and connected services",
                analyticsTitle: "Analytics",
                analyticsDescription: "View energy usage and device activity insights",
                
                // Modals
                hubModalTitle: "Hub Management",
                hubUrlLabel: "Hub Address",
                hubNameLabel: "Hub Name",
                hubTypeLabel: "Hub Type",
                connectedHubsTitle: "Connected Hubs",
                connectButton: "Connect Hub",
                cancelButton: "Cancel",
                
                devicesModalTitle: "Smart Devices",
                scanDevicesButton: "Scan for Devices",
                refreshDevicesButton: "Refresh",
                
                settingsModalTitle: "Settings",
                voiceSettingsTitle: "Voice Assistant",
                sttProviderLabel: "Speech Recognition",
                ttsProviderLabel: "Text-to-Speech",
                wakeWordsLabel: "Wake Words",
                integrationSettingsTitle: "Integrations",
                openaiKeyLabel: "OpenAI API Key",
                spotifyClientIdLabel: "Spotify Client ID",
                saveSettingsButton: "Save Settings",
                cancelSettingsButton: "Cancel",
                
                scenariosModalTitle: "Automation Scenarios",
                scenariosComingSoonTitle: "Coming Soon",
                scenariosComingSoonDescription: "Advanced automation scenarios will be available in the next update.",
                
                analyticsModalTitle: "Analytics & Insights",
                analyticsComingSoonTitle: "Analytics Coming Soon",
                analyticsComingSoonDescription: "Detailed energy usage and device analytics will be available soon.",
                
                // Notifications
                hubConnected: "Hub connected successfully",
                hubConnectionFailed: "Failed to connect to hub",
                devicesScanStarted: "Device scan started",
                settingsSaved: "Settings saved successfully",
                settingsSaveFailed: "Failed to save settings",
                
                // Hub Types
                localHubType: "Local Hub",
                cloudHubType: "Cloud Hub",
                remoteHubType: "Remote Hub",
                
                // Common
                active: "Active",
                inactive: "Inactive",
                connecting: "Connecting...",
                connected: "Connected",
                disconnected: "Disconnected",
                error: "Error"
            },
            ru: {
                appTitle: "Домашний Ассистент ИИ",
                appSubtitle: "Ваш умный компаньон для автоматизации дома",
                welcomeTitle: "Добро пожаловать домой",
                welcomeSubtitle: "Ваш интеллектуальный ИИ-ассистент готов помочь вам управлять умным домом с помощью голосовых команд и интуитивных элементов управления.",
                
                currentHub: "Текущий хаб",
                localHub: "Локальный хаб",
                
                voiceInstructions: "Нажмите, чтобы поговорить с ИИ-ассистентом",
                listening: "Слушаю...",
                processing: "Обрабатываю...",
                speaking: "Говорю...",
                
                devices: "Устройства",
                hubsConnected: "Хабы подключены",
                voiceAssistant: "Голосовой ассистент",
                aiReady: "ИИ готов",
                online: "Онлайн",
                offline: "Оффлайн",
                partial: "Частично",
                
                devicesTitle: "Умные устройства",
                devicesDescription: "Управление освещением, датчиками и устройствами умного дома",
                scenariosTitle: "Автоматизация",
                scenariosDescription: "Создание и управление сценариями автоматизации умного дома",
                settingsTitle: "Настройки",
                settingsDescription: "Настройка ассистента и подключенных сервисов",
                analyticsTitle: "Аналитика",
                analyticsDescription: "Просмотр потребления энергии и активности устройств",
                
                hubModalTitle: "Управление хабами",
                hubUrlLabel: "Адрес хаба",
                hubNameLabel: "Имя хаба",
                hubTypeLabel: "Тип хаба",
                connectedHubsTitle: "Подключенные хабы",
                connectButton: "Подключить хаб",
                cancelButton: "Отмена",
                
                devicesModalTitle: "Умные устройства",
                scanDevicesButton: "Поиск устройств",
                refreshDevicesButton: "Обновить",
                
                settingsModalTitle: "Настройки",
                voiceSettingsTitle: "Голосовой ассистент",
                sttProviderLabel: "Распознавание речи",
                ttsProviderLabel: "Синтез речи",
                wakeWordsLabel: "Ключевые слова",
                integrationSettingsTitle: "Интеграции",
                openaiKeyLabel: "Ключ API OpenAI",
                spotifyClientIdLabel: "Spotify Client ID",
                saveSettingsButton: "Сохранить настройки",
                cancelSettingsButton: "Отмена",
                
                scenariosModalTitle: "Сценарии автоматизации",
                scenariosComingSoonTitle: "Скоро",
                scenariosComingSoonDescription: "Расширенные сценарии автоматизации будут доступны в следующем обновлении.",
                
                analyticsModalTitle: "Аналитика и статистика",
                analyticsComingSoonTitle: "Аналитика скоро",
                analyticsComingSoonDescription: "Подробная аналитика потребления энергии и устройств будет доступна скоро.",
                
                hubConnected: "Хаб успешно подключен",
                hubConnectionFailed: "Не удалось подключиться к хабу",
                devicesScanStarted: "Поиск устройств запущен",
                settingsSaved: "Настройки успешно сохранены",
                settingsSaveFailed: "Не удалось сохранить настройки",
                
                localHubType: "Локальный хаб",
                cloudHubType: "Облачный хаб",
                remoteHubType: "Удаленный хаб",
                
                active: "Активен",
                inactive: "Неактивен",
                connecting: "Подключение...",
                connected: "Подключен",
                disconnected: "Отключен",
                error: "Ошибка"
            },
            pl: {
                appTitle: "Domowy Asystent AI",
                appSubtitle: "Twój inteligentny towarzysz automatyzacji domu",
                welcomeTitle: "Witaj w domu",
                welcomeSubtitle: "Twój inteligentny asystent AI jest gotowy, aby pomóc Ci kontrolować inteligentny dom za pomocą poleceń głosowych i intuicyjnych kontrolek.",
                
                currentHub: "Bieżący hub",
                localHub: "Lokalny hub",
                
                voiceInstructions: "Dotknij, aby porozmawiać z asystentem AI",
                listening: "Słucham...",
                processing: "Przetwarzam...",
                speaking: "Mówię...",
                
                devices: "Urządzenia",
                hubsConnected: "Huby podłączone",
                voiceAssistant: "Asystent głosowy",
                aiReady: "AI gotowe",
                online: "Online",
                offline: "Offline",
                partial: "Częściowo",
                
                devicesTitle: "Inteligentne urządzenia",
                devicesDescription: "Kontroluj oświetlenie, czujniki i urządzenia inteligentnego domu",
                scenariosTitle: "Automatyzacja",
                scenariosDescription: "Twórz i zarządzaj scenariuszami automatyzacji inteligentnego domu",
                settingsTitle: "Ustawienia",
                settingsDescription: "Konfiguruj asystenta i podłączone usługi",
                analyticsTitle: "Analityka",
                analyticsDescription: "Wyświetl zużycie energii i statystyki aktywności urządzeń",
                
                hubModalTitle: "Zarządzanie hubami",
                hubUrlLabel: "Adres huba",
                hubNameLabel: "Nazwa huba",
                hubTypeLabel: "Typ huba",
                connectedHubsTitle: "Podłączone huby",
                connectButton: "Połącz hub",
                cancelButton: "Anuluj",
                
                devicesModalTitle: "Inteligentne urządzenia",
                scanDevicesButton: "Skanuj urządzenia",
                refreshDevicesButton: "Odśwież",
                
                settingsModalTitle: "Ustawienia",
                voiceSettingsTitle: "Asystent głosowy",
                sttProviderLabel: "Rozpoznawanie mowy",
                ttsProviderLabel: "Synteza mowy",
                wakeWordsLabel: "Słowa aktywujące",
                integrationSettingsTitle: "Integracje",
                openaiKeyLabel: "Klucz API OpenAI",
                spotifyClientIdLabel: "Spotify Client ID",
                saveSettingsButton: "Zapisz ustawienia",
                cancelSettingsButton: "Anuluj",
                
                scenariosModalTitle: "Scenariusze automatyzacji",
                scenariosComingSoonTitle: "Wkrótce",
                scenariosComingSoonDescription: "Zaawansowane scenariusze automatyzacji będą dostępne w następnej aktualizacji.",
                
                analyticsModalTitle: "Analityka i statystyki",
                analyticsComingSoonTitle: "Analityka wkrótce",
                analyticsComingSoonDescription: "Szczegółowa analityka zużycia energii i urządzeń będzie dostępna wkrótce.",
                
                hubConnected: "Hub pomyślnie podłączony",
                hubConnectionFailed: "Nie udało się połączyć z hubem",
                devicesScanStarted: "Rozpoczęto skanowanie urządzeń",
                settingsSaved: "Ustawienia zostały pomyślnie zapisane",
                settingsSaveFailed: "Nie udało się zapisać ustawień",
                
                localHubType: "Lokalny hub",
                cloudHubType: "Chmurowy hub",
                remoteHubType: "Zdalny hub",
                
                active: "Aktywny",
                inactive: "Nieaktywny",
                connecting: "Łączenie...",
                connected: "Połączony",
                disconnected: "Rozłączony",
                error: "Błąd"
            }
        };
    }

    async loadHubs() {
        // Load saved hubs from localStorage
        const savedHubs = localStorage.getItem('connectedHubs');
        if (savedHubs) {
            this.hubs = JSON.parse(savedHubs);
        } else {
            // Default local hub
            this.hubs = [{
                id: 'local',
                name: 'Local Hub',
                url: 'http://localhost:8000',
                type: 'local',
                status: 'connected',
                isDefault: true
            }];
            this.saveHubs();
        }
        
        // Set current hub if not set
        if (!this.currentHub && this.hubs.length > 0) {
            this.currentHub = this.hubs.find(h => h.isDefault) || this.hubs[0];
        }
    }

    saveHubs() {
        localStorage.setItem('connectedHubs', JSON.stringify(this.hubs));
    }

    setCurrentHub(hubId) {
        const hub = this.hubs.find(h => h.id === hubId);
        if (hub) {
            this.currentHub = hub;
            localStorage.setItem('currentHub', hubId);
            this.updateHubUI();
            this.updateStatus();
        }
    }

    updateHubUI() {
        if (this.currentHub) {
            const hubButton = document.getElementById('currentHub');
            const hubStatus = document.getElementById('hubStatus');
            
            if (hubButton) hubButton.textContent = this.currentHub.name;
            if (hubStatus) {
                hubStatus.className = `hub-status ${this.currentHub.status}`;
            }
        }
    }

    setupEventListeners() {
        // Language selector
        const languageSelect = document.getElementById('languageSelect');
        if (languageSelect) {
            languageSelect.addEventListener('change', (e) => {
                this.setLanguage(e.target.value);
            });
        }

        // Close modals on click outside
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('modal-overlay')) {
                this.closeModal(e.target.id);
            }
        });

        // Escape key to close modals
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                const activeModal = document.querySelector('.modal-overlay.active');
                if (activeModal) {
                    this.closeModal(activeModal.id);
                }
            }
        });
    }

    setupTheme() {
        const savedTheme = localStorage.getItem('theme') || 'light';
        this.setTheme(savedTheme);
    }

    setTheme(theme) {
        this.currentTheme = theme;
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('theme', theme);
        
        // Update theme toggle button
        const themeToggle = document.querySelector('.theme-toggle');
        if (themeToggle) {
            themeToggle.textContent = theme === 'dark' ? '☀️' : '🌙';
        }
    }

    toggleTheme() {
        const newTheme = this.currentTheme === 'light' ? 'dark' : 'light';
        this.setTheme(newTheme);
    }

    setLanguage(lang) {
        this.currentLanguage = lang;
        localStorage.setItem('language', lang);
        const languageSelect = document.getElementById('languageSelect');
        if (languageSelect) languageSelect.value = lang;
        
        // Update all translated elements
        const translations = this.translations[lang];
        if (translations) {
            Object.keys(translations).forEach(key => {
                const element = document.getElementById(key);
                if (element) {
                    if (element.tagName === 'INPUT' && element.type === 'button') {
                        element.value = translations[key];
                    } else if (element.tagName === 'INPUT' && element.placeholder !== undefined) {
                        // Don't change placeholder for now
                    } else {
                        element.textContent = translations[key];
                    }
                }
            });
        }

        // Update placeholder texts
        this.updatePlaceholders(lang);
    }

    updatePlaceholders(lang) {
        const placeholders = {
            en: {
                hubUrl: "http://192.168.1.100:8000",
                hubName: "Living Room Hub",
                wakeWords: "Hey Assistant, OK Home",
                openaiKey: "sk-...",
                spotifyClientId: "Your Spotify Client ID"
            },
            ru: {
                hubUrl: "http://192.168.1.100:8000",
                hubName: "Хаб гостиной",
                wakeWords: "Привет ассистент, Окей дом",
                openaiKey: "sk-...",
                spotifyClientId: "Ваш Spotify Client ID"
            },
            pl: {
                hubUrl: "http://192.168.1.100:8000",
                hubName: "Hub pokoju dziennego",
                wakeWords: "Hej asystencie, OK dom",
                openaiKey: "sk-...",
                spotifyClientId: "Twój Spotify Client ID"
            }
        };

        const langPlaceholders = placeholders[lang] || placeholders.en;
        Object.keys(langPlaceholders).forEach(id => {
            const element = document.getElementById(id);
            if (element && element.placeholder !== undefined) {
                element.placeholder = langPlaceholders[id];
            }
        });
    }

    async updateStatus() {
        try {
            const baseUrl = this.currentHub ? this.currentHub.url : '';
            
            // Check system status
            const healthResponse = await fetch(`${baseUrl}/health`);
            const systemOnline = healthResponse.ok;
            
            // Update voice status
            try {
                const voiceResponse = await fetch(`${baseUrl}/voice/status`);
                const voiceData = await voiceResponse.json();
                
                const voiceStatusIndicator = document.getElementById('voiceStatusIndicator');
                if (voiceStatusIndicator) {
                    if (voiceData.enabled && voiceData.available) {
                        voiceStatusIndicator.className = 'status-indicator online';
                    } else if (voiceData.enabled) {
                        voiceStatusIndicator.className = 'status-indicator warning';
                    } else {
                        voiceStatusIndicator.className = 'status-indicator offline';
                    }
                }
            } catch (e) {
                const voiceStatusIndicator = document.getElementById('voiceStatusIndicator');
                if (voiceStatusIndicator) {
                    voiceStatusIndicator.className = 'status-indicator offline';
                }
            }

            // Update device status
            try {
                const devicesResponse = await fetch(`${baseUrl}/devices`);
                const devicesData = await devicesResponse.json();
                const deviceCount = devicesData.devices ? devicesData.devices.length : 0;
                
                const deviceCountEl = document.getElementById('deviceCount');
                const deviceStatus = document.getElementById('deviceStatus');
                
                if (deviceCountEl) deviceCountEl.textContent = deviceCount;
                if (deviceStatus) {
                    deviceStatus.className = deviceCount > 0 ? 'status-indicator online' : 'status-indicator offline';
                }
            } catch (e) {
                const deviceCountEl = document.getElementById('deviceCount');
                const deviceStatus = document.getElementById('deviceStatus');
                
                if (deviceCountEl) deviceCountEl.textContent = '0';
                if (deviceStatus) deviceStatus.className = 'status-indicator offline';
            }

            // Update hub count
            const hubCountEl = document.getElementById('hubCount');
            if (hubCountEl) hubCountEl.textContent = this.hubs.length;

        } catch (error) {
            console.error('Status update failed:', error);
        }
    }

    translate(key) {
        return this.translations[this.currentLanguage][key] || key;
    }

    async loadDevices() {
        try {
            const baseUrl = this.currentHub ? this.currentHub.url : '';
            const response = await fetch(`${baseUrl}/devices`);
            const data = await response.json();
            this.devices = data.devices || [];
        } catch (error) {
            console.error('Failed to load devices:', error);
            this.devices = [];
        }
    }

    renderDevices() {
        const devicesList = document.getElementById('devicesList');
        if (!devicesList) return;
        
        devicesList.innerHTML = '';

        if (this.devices.length === 0) {
            devicesList.innerHTML = `
                <div style="text-align: center; padding: var(--space-8); color: var(--gray-500);">
                    <div style="font-size: var(--text-3xl); margin-bottom: var(--space-4);">📱</div>
                    <p>No devices found. Click "Scan for Devices" to discover smart home devices.</p>
                </div>
            `;
            return;
        }

        this.devices.forEach(device => {
            const deviceCard = document.createElement('div');
            deviceCard.className = 'device-card';
            deviceCard.style.cssText = `
                background: var(--gray-50);
                border-radius: var(--rounded-lg);
                padding: var(--space-4);
                border: 1px solid var(--gray-200);
            `;
            
            deviceCard.innerHTML = `
                <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: var(--space-3);">
                    <div>
                        <div style="font-weight: 600; margin-bottom: var(--space-1);">${device.name || device.device_id}</div>
                        <div style="font-size: var(--text-sm); color: var(--gray-600);">${device.type || 'Unknown'}</div>
                    </div>
                    <span class="status-indicator ${device.is_online ? 'online' : 'offline'}"></span>
                </div>
                <div style="font-size: var(--text-sm); color: var(--gray-600); margin-bottom: var(--space-3);">
                    Protocol: ${device.protocol || 'Unknown'}
                </div>
                <div style="display: flex; gap: var(--space-2); flex-wrap: wrap;">
                    ${this.generateDeviceControls(device)}
                </div>
            `;
            
            devicesList.appendChild(deviceCard);
        });
    }

    generateDeviceControls(device) {
        const capabilities = device.capabilities || [];
        let controls = '';

        if (capabilities.includes('on_off') || capabilities.includes('power_control')) {
            controls += `
                <button class="btn btn-primary" style="font-size: var(--text-xs); padding: var(--space-2) var(--space-3);" 
                        onclick="ui.controlDevice('${device.device_id}', 'power', {state: true})">
                    ON
                </button>
                <button class="btn btn-secondary" style="font-size: var(--text-xs); padding: var(--space-2) var(--space-3);" 
                        onclick="ui.controlDevice('${device.device_id}', 'power', {state: false})">
                    OFF
                </button>
            `;
        }

        if (capabilities.includes('brightness_control')) {
            controls += `
                <input type="range" min="0" max="100" value="50" 
                       style="flex: 1; min-width: 100px;"
                       onchange="ui.controlDevice('${device.device_id}', 'brightness', {value: this.value})"
                       title="Brightness">
            `;
        }

        if (capabilities.includes('color_control')) {
            controls += `
                <input type="color" 
                       style="width: 40px; height: 32px; border: none; border-radius: var(--rounded-md); cursor: pointer;"
                       onchange="ui.setDeviceColor('${device.device_id}', this.value)"
                       title="Color">
            `;
        }

        return controls;
    }

    async controlDevice(deviceId, command, params) {
        try {
            const baseUrl = this.currentHub ? this.currentHub.url : '';
            const response = await fetch(`${baseUrl}/devices/${deviceId}/action`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ command: command, params: params })
            });

            if (response.ok) {
                await this.loadDevices();
                this.renderDevices();
                this.showNotification('Device command sent successfully', 'success');
            } else {
                this.showNotification('Failed to control device', 'error');
            }
        } catch (error) {
            console.error('Device control error:', error);
            this.showNotification('Device control error', 'error');
        }
    }

    setDeviceColor(deviceId, colorHex) {
        const r = parseInt(colorHex.slice(1, 3), 16);
        const g = parseInt(colorHex.slice(3, 5), 16);
        const b = parseInt(colorHex.slice(5, 7), 16);
        
        this.controlDevice(deviceId, 'color', {color: {r, g, b}});
    }

    async scanDevices() {
        const scanBtn = document.getElementById('scanDevicesButton');
        const spinner = document.getElementById('scanSpinner');
        
        if (scanBtn) {
            scanBtn.disabled = true;
            if (spinner) spinner.classList.remove('hidden');
        }

        try {
            const baseUrl = this.currentHub ? this.currentHub.url : '';
            const response = await fetch(`${baseUrl}/devices/scan`, {method: 'POST'});
            
            if (response.ok) {
                this.showNotification(this.translate('devicesScanStarted'), 'success');
                
                setTimeout(async () => {
                    await this.loadDevices();
                    this.renderDevices();
                }, 3000);
            }
        } catch (error) {
            console.error('Device scan failed:', error);
            this.showNotification('Device scan failed', 'error');
        } finally {
            if (scanBtn) {
                scanBtn.disabled = false;
                if (spinner) spinner.classList.add('hidden');
            }
        }
    }

    async refreshDevices() {
        await this.loadDevices();
        this.renderDevices();
        this.showNotification('Devices refreshed', 'success');
    }

    async toggleVoice() {
        const voiceBtn = document.getElementById('voiceButton');
        const voiceInstructions = document.getElementById('voiceInstructions');

        if (this.isVoiceListening) {
            this.isVoiceListening = false;
            if (voiceBtn) {
                voiceBtn.classList.remove('listening');
                voiceBtn.textContent = '🎤';
            }
            if (voiceInstructions) {
                voiceInstructions.textContent = this.translate('voiceInstructions');
            }
        } else {
            this.isVoiceListening = true;
            if (voiceBtn) {
                voiceBtn.classList.add('listening');
                voiceBtn.textContent = '🔴';
            }
            if (voiceInstructions) {
                voiceInstructions.textContent = this.translate('listening');
            }

            try {
                const baseUrl = this.currentHub ? this.currentHub.url : '';
                const response = await fetch(`${baseUrl}/voice/listen`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({timeout: 5.0})
                });

                const data = await response.json();
                
                if (data.text) {
                    this.showNotification(`Voice: "${data.text}"`, 'success');
                    // Here you could process the voice command
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
    }

    // Modal Management
    showModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.add('active');
            
            // Load data for specific modals
            if (modalId === 'devicesModal') {
                this.renderDevices();
            } else if (modalId === 'hubModal') {
                this.renderHubsList();
            }
        }
    }

    closeModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.remove('active');
        }
    }

    renderHubsList() {
        const hubsList = document.getElementById('hubsList');
        if (!hubsList) return;
        
        hubsList.innerHTML = '';

        this.hubs.forEach(hub => {
            const hubItem = document.createElement('div');
            hubItem.style.cssText = `
                padding: var(--space-3);
                background: var(--gray-50);
                border-radius: var(--rounded-md);
                display: flex;
                align-items: center;
                justify-content: space-between;
                margin-bottom: var(--space-2);
            `;
            
            hubItem.innerHTML = `
                <div>
                    <div style="font-weight: 500;">${hub.name}</div>
                    <div style="font-size: var(--text-sm); color: var(--gray-600);">${hub.url}</div>
                </div>
                <div style="display: flex; align-items: center; gap: var(--space-2);">
                    <span class="status-indicator ${hub.status}"></span>
                    <span style="font-size: var(--text-sm);">${this.translate(hub.status)}</span>
                    ${hub.id !== 'local' ? `<button class="btn btn-secondary" style="font-size: var(--text-xs); padding: var(--space-1) var(--space-2);" onclick="ui.removeHub('${hub.id}')">Remove</button>` : ''}
                </div>
            `;
            
            hubsList.appendChild(hubItem);
        });
    }

    async connectHub() {
        const hubUrl = document.getElementById('hubUrl').value;
        const hubName = document.getElementById('hubName').value;
        const hubType = document.getElementById('hubType').value;
        const connectBtn = document.getElementById('connectButton');
        const spinner = document.getElementById('connectSpinner');

        if (!hubUrl || !hubName) {
            this.showNotification('Please fill in all fields', 'error');
            return;
        }

        if (connectBtn) connectBtn.disabled = true;
        if (spinner) spinner.classList.remove('hidden');

        try {
            // Test connection to hub
            const response = await fetch(`${hubUrl}/health`);
            
            if (response.ok) {
                const newHub = {
                    id: Date.now().toString(),
                    name: hubName,
                    url: hubUrl,
                    type: hubType,
                    status: 'connected',
                    isDefault: false
                };

                this.hubs.push(newHub);
                this.saveHubs();
                this.renderHubsList();
                
                // Clear form
                document.getElementById('hubUrl').value = '';
                document.getElementById('hubName').value = '';
                
                this.showNotification(this.translate('hubConnected'), 'success');
            } else {
                this.showNotification(this.translate('hubConnectionFailed'), 'error');
            }
        } catch (error) {
            console.error('Hub connection failed:', error);
            this.showNotification(this.translate('hubConnectionFailed'), 'error');
        } finally {
            if (connectBtn) connectBtn.disabled = false;
            if (spinner) spinner.classList.add('hidden');
        }
    }

    removeHub(hubId) {
        this.hubs = this.hubs.filter(h => h.id !== hubId);
        this.saveHubs();
        this.renderHubsList();
        
        if (this.currentHub && this.currentHub.id === hubId) {
            this.setCurrentHub(this.hubs[0]?.id || 'local');
        }
        
        this.showNotification('Hub removed', 'success');
    }

    async saveSettings() {
        const saveBtn = document.getElementById('saveSettingsButton');
        const spinner = document.getElementById('saveSpinner');
        
        if (saveBtn) saveBtn.disabled = true;
        if (spinner) spinner.classList.remove('hidden');

        try {
            const settings = {
                voice: {
                    stt_provider: document.getElementById('sttProvider').value,
                    tts_provider: document.getElementById('ttsProvider').value,
                    wake_words: document.getElementById('wakeWords').value.split(',').map(w => w.trim())
                },
                integrations: {
                    openai: {
                        api_key: document.getElementById('openaiKey').value
                    },
                    spotify: {
                        client_id: document.getElementById('spotifyClientId').value
                    }
                }
            };

            const baseUrl = this.currentHub ? this.currentHub.url : '';
            const response = await fetch(`${baseUrl}/settings`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(settings)
            });

            if (response.ok) {
                this.showNotification(this.translate('settingsSaved'), 'success');
                this.closeModal('settingsModal');
            } else {
                this.showNotification(this.translate('settingsSaveFailed'), 'error');
            }
        } catch (error) {
            console.error('Settings save failed:', error);
            this.showNotification(this.translate('settingsSaveFailed'), 'error');
        } finally {
            if (saveBtn) saveBtn.disabled = false;
            if (spinner) spinner.classList.add('hidden');
        }
    }

    showNotification(message, type = 'info') {
        const container = document.getElementById('notificationContainer');
        if (!container) return;

        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.innerHTML = `
            <div style="display: flex; align-items: center; gap: var(--space-2);">
                <span>${type === 'success' ? '✅' : type === 'error' ? '❌' : 'ℹ️'}</span>
                <span>${message}</span>
            </div>
        `;

        container.appendChild(notification);

        // Show notification
        setTimeout(() => notification.classList.add('show'), 100);

        // Hide and remove notification
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => container.removeChild(notification), 300);
        }, 4000);
    }

    checkFirstTimeSetup() {
        const isFirstTime = !localStorage.getItem('hasCompletedSetup');
        if (isFirstTime) {
            // Could show onboarding modal here
            localStorage.setItem('hasCompletedSetup', 'true');
        }
    }
}

// Global functions for HTML onclick handlers
function showHubModal() {
    ui.showModal('hubModal');
}

function showDevicesModal() {
    ui.showModal('devicesModal');
}

function showSettingsModal() {
    ui.showModal('settingsModal');
}

function showScenariosModal() {
    ui.showModal('scenariosModal');
}

function showAnalyticsModal() {
    ui.showModal('analyticsModal');
}

function closeModal(modalId) {
    ui.closeModal(modalId);
}

function toggleTheme() {
    ui.toggleTheme();
}

function connectHub() {
    ui.connectHub();
}

function scanDevices() {
    ui.scanDevices();
}

function refreshDevices() {
    ui.refreshDevices();
}

function saveSettings() {
    ui.saveSettings();
}

// Initialize the UI when page loads
let ui;
document.addEventListener('DOMContentLoaded', () => {
    ui = new PremiumHomeAssistantUI();
});

// Service Worker registration for PWA
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/static/sw.js')
            .then(registration => {
                console.log('SW registered: ', registration);
            })
            .catch(registrationError => {
                console.log('SW registration failed: ', registrationError);
            });
    });
}