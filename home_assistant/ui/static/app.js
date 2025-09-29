// Home Assistant AI Web Interface
class HomeAssistantUI {
    constructor() {
        this.currentLanguage = 'en';
        this.isVoiceListening = false;
        this.devices = [];
        this.translations = {};
        
        this.init();
    }

    async init() {
        await this.loadTranslations();
        this.setupEventListeners();
        this.updateStatus();
        this.loadDevices();
        
        // Set default language
        const savedLang = localStorage.getItem('language') || 'en';
        this.setLanguage(savedLang);
        
        // Auto-refresh status every 30 seconds
        setInterval(() => this.updateStatus(), 30000);
    }

    async loadTranslations() {
        // Inline translations for simplicity
        this.translations = {
            en: {
                appTitle: "Home Assistant AI",
                appSubtitle: "Your intelligent home automation companion",
                systemOnline: "System Online",
                voiceAssistant: "Voice Assistant",
                devicesConnected: "Devices Connected",
                tabDashboard: "Dashboard",
                tabDevices: "Devices",
                tabVoice: "Voice",
                tabScenarios: "Scenarios",
                tabSettings: "Settings",
                dashboardTitle: "Dashboard",
                voiceInstructions: "Click to talk to your assistant",
                welcomeMessage: "Hello! I'm your Home Assistant AI. How can I help you today?",
                devicesTitle: "Device Management",
                scanBtn: "Scan for Devices",
                voiceTitle: "Voice Settings",
                sttProviderLabel: "Speech-to-Text Provider:",
                ttsProviderLabel: "Text-to-Speech Provider:",
                wakeWordsLabel: "Wake Words (comma separated):",
                saveVoiceBtn: "Save Settings",
                scenariosTitle: "Automation Scenarios",
                scenariosComingSoon: "Coming soon: Create custom automation scenarios",
                settingsTitle: "Settings",
                spotifyClientIdLabel: "Spotify Client ID:",
                spotifyClientSecretLabel: "Spotify Client Secret:",
                openaiApiKeyLabel: "OpenAI API Key:",
                saveSettingsBtn: "Save Settings",
                sendBtn: "Send",
                listening: "Listening...",
                processing: "Processing...",
                online: "Online",
                offline: "Offline",
                partial: "Partial"
            },
            ru: {
                appTitle: "Домашний Ассистент ИИ",
                appSubtitle: "Ваш умный компаньон для автоматизации дома",
                systemOnline: "Система онлайн",
                voiceAssistant: "Голосовой ассистент",
                devicesConnected: "Устройства подключены",
                tabDashboard: "Панель",
                tabDevices: "Устройства",
                tabVoice: "Голос",
                tabScenarios: "Сценарии",
                tabSettings: "Настройки",
                dashboardTitle: "Панель управления",
                voiceInstructions: "Нажмите, чтобы поговорить с ассистентом",
                welcomeMessage: "Привет! Я ваш Домашний Ассистент ИИ. Как я могу помочь?",
                devicesTitle: "Управление устройствами",
                scanBtn: "Поиск устройств",
                voiceTitle: "Настройки голоса",
                sttProviderLabel: "Провайдер распознавания речи:",
                ttsProviderLabel: "Провайдер синтеза речи:",
                wakeWordsLabel: "Ключевые слова (через запятую):",
                saveVoiceBtn: "Сохранить настройки",
                scenariosTitle: "Сценарии автоматизации",
                scenariosComingSoon: "Скоро: Создание пользовательских сценариев автоматизации",
                settingsTitle: "Настройки",
                spotifyClientIdLabel: "Spotify Client ID:",
                spotifyClientSecretLabel: "Spotify Client Secret:",
                openaiApiKeyLabel: "OpenAI API ключ:",
                saveSettingsBtn: "Сохранить настройки",
                sendBtn: "Отправить",
                listening: "Слушаю...",
                processing: "Обрабатываю...",
                online: "Онлайн",
                offline: "Оффлайн",
                partial: "Частично"
            },
            pl: {
                appTitle: "Domowy Asystent AI",
                appSubtitle: "Twój inteligentny towarzysz automatyzacji domu",
                systemOnline: "System online",
                voiceAssistant: "Asystent głosowy",
                devicesConnected: "Urządzenia podłączone",
                tabDashboard: "Panel",
                tabDevices: "Urządzenia",
                tabVoice: "Głos",
                tabScenarios: "Scenariusze",
                tabSettings: "Ustawienia",
                dashboardTitle: "Panel kontrolny",
                voiceInstructions: "Kliknij, aby porozmawiać z asystentem",
                welcomeMessage: "Cześć! Jestem twoim Domowym Asystentem AI. Jak mogę pomóc?",
                devicesTitle: "Zarządzanie urządzeniami",
                scanBtn: "Skanuj urządzenia",
                voiceTitle: "Ustawienia głosu",
                sttProviderLabel: "Dostawca rozpoznawania mowy:",
                ttsProviderLabel: "Dostawca syntezy mowy:",
                wakeWordsLabel: "Słowa aktywujące (oddzielone przecinkami):",
                saveVoiceBtn: "Zapisz ustawienia",
                scenariosTitle: "Scenariusze automatyzacji",
                scenariosComingSoon: "Wkrótce: Tworzenie niestandardowych scenariuszy automatyzacji",
                settingsTitle: "Ustawienia",
                spotifyClientIdLabel: "Spotify Client ID:",
                spotifyClientSecretLabel: "Spotify Client Secret:",
                openaiApiKeyLabel: "Klucz API OpenAI:",
                saveSettingsBtn: "Zapisz ustawienia",
                sendBtn: "Wyślij",
                listening: "Słucham...",
                processing: "Przetwarzam...",
                online: "Online",
                offline: "Offline",
                partial: "Częściowo"
            }
        };
    }

    setupEventListeners() {
        // Language selector
        document.getElementById('languageSelect').addEventListener('change', (e) => {
            this.setLanguage(e.target.value);
        });

        // Enter key in chat input
        document.getElementById('chatInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.sendMessage();
            }
        });
    }

    setLanguage(lang) {
        this.currentLanguage = lang;
        localStorage.setItem('language', lang);
        document.getElementById('languageSelect').value = lang;
        
        // Update all translated elements
        const translations = this.translations[lang];
        if (translations) {
            Object.keys(translations).forEach(key => {
                const element = document.getElementById(key);
                if (element) {
                    if (element.tagName === 'INPUT' && element.type !== 'text' && element.type !== 'password') {
                        element.value = translations[key];
                    } else {
                        element.textContent = translations[key];
                    }
                }
            });
        }

        // Update placeholder texts
        const chatInput = document.getElementById('chatInput');
        if (chatInput) {
            const placeholders = {
                en: "Type your message or use voice...",
                ru: "Введите сообщение или используйте голос...",
                pl: "Wpisz wiadomość lub użyj głosu..."
            };
            chatInput.placeholder = placeholders[lang] || placeholders.en;
        }
    }

    async updateStatus() {
        try {
            // Check system status
            const healthResponse = await fetch('/health');
            const systemOnline = healthResponse.ok;
            
            // Update system status
            const systemStatus = document.getElementById('systemStatus');
            const systemStatusText = document.getElementById('systemStatusText');
            if (systemOnline) {
                systemStatus.className = 'status-icon online';
                systemStatusText.textContent = this.translate('systemOnline');
            } else {
                systemStatus.className = 'status-icon offline';
                systemStatusText.textContent = this.translate('offline');
            }

            // Check voice status
            try {
                const voiceResponse = await fetch('/voice/status');
                const voiceData = await voiceResponse.json();
                const voiceStatus = document.getElementById('voiceStatus');
                const voiceStatusText = document.getElementById('voiceStatusText');
                
                if (voiceData.enabled && voiceData.available) {
                    voiceStatus.className = 'status-icon online';
                    voiceStatusText.textContent = this.translate('voiceAssistant') + ' - ' + this.translate('online');
                } else if (voiceData.enabled) {
                    voiceStatus.className = 'status-icon partial';
                    voiceStatusText.textContent = this.translate('voiceAssistant') + ' - ' + this.translate('partial');
                } else {
                    voiceStatus.className = 'status-icon offline';
                    voiceStatusText.textContent = this.translate('voiceAssistant') + ' - ' + this.translate('offline');
                }
            } catch (e) {
                const voiceStatus = document.getElementById('voiceStatus');
                const voiceStatusText = document.getElementById('voiceStatusText');
                voiceStatus.className = 'status-icon offline';
                voiceStatusText.textContent = this.translate('voiceAssistant') + ' - ' + this.translate('offline');
            }

            // Check device status
            try {
                const devicesResponse = await fetch('/devices');
                const devicesData = await devicesResponse.json();
                const deviceCount = devicesData.devices ? devicesData.devices.length : 0;
                
                const deviceStatus = document.getElementById('deviceStatus');
                const deviceStatusText = document.getElementById('deviceStatusText');
                
                if (deviceCount > 0) {
                    deviceStatus.className = 'status-icon online';
                    deviceStatusText.textContent = `${deviceCount} ${this.translate('devicesConnected')}`;
                } else {
                    deviceStatus.className = 'status-icon offline';
                    deviceStatusText.textContent = `0 ${this.translate('devicesConnected')}`;
                }
            } catch (e) {
                const deviceStatus = document.getElementById('deviceStatus');
                const deviceStatusText = document.getElementById('deviceStatusText');
                deviceStatus.className = 'status-icon offline';
                deviceStatusText.textContent = `0 ${this.translate('devicesConnected')}`;
            }
        } catch (error) {
            console.error('Status update failed:', error);
        }
    }

    translate(key) {
        return this.translations[this.currentLanguage][key] || key;
    }

    async loadDevices() {
        try {
            const response = await fetch('/devices');
            const data = await response.json();
            this.devices = data.devices || [];
            this.renderDevices();
        } catch (error) {
            console.error('Failed to load devices:', error);
        }
    }

    renderDevices() {
        const deviceGrid = document.getElementById('deviceGrid');
        deviceGrid.innerHTML = '';

        this.devices.forEach(device => {
            const deviceCard = document.createElement('div');
            deviceCard.className = 'device-card';
            
            deviceCard.innerHTML = `
                <div class="device-header">
                    <div class="device-name">${device.name || device.device_id}</div>
                    <div class="device-type">${device.type || 'Unknown'}</div>
                </div>
                <div class="device-info">
                    <p>Protocol: ${device.protocol || 'Unknown'}</p>
                    <p>Status: ${device.is_online ? 'Online' : 'Offline'}</p>
                </div>
                <div class="device-controls">
                    ${this.generateDeviceControls(device)}
                </div>
            `;
            
            deviceGrid.appendChild(deviceCard);
        });
    }

    generateDeviceControls(device) {
        const capabilities = device.capabilities || [];
        let controls = '';

        if (capabilities.includes('on_off') || capabilities.includes('power_control')) {
            controls += `
                <button class="control-btn primary" onclick="ui.controlDevice('${device.device_id}', 'power', {state: true})">
                    Turn On
                </button>
                <button class="control-btn secondary" onclick="ui.controlDevice('${device.device_id}', 'power', {state: false})">
                    Turn Off
                </button>
            `;
        }

        if (capabilities.includes('brightness_control')) {
            controls += `
                <input type="range" min="0" max="100" value="50" 
                       onchange="ui.controlDevice('${device.device_id}', 'brightness', {value: this.value})"
                       title="Brightness">
            `;
        }

        if (capabilities.includes('color_control')) {
            controls += `
                <input type="color" 
                       onchange="ui.setDeviceColor('${device.device_id}', this.value)"
                       title="Color">
            `;
        }

        return controls;
    }

    async controlDevice(deviceId, command, params) {
        try {
            const response = await fetch(`/devices/${deviceId}/action`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    command: command,
                    params: params
                })
            });

            if (response.ok) {
                // Refresh devices after successful command
                await this.loadDevices();
            } else {
                console.error('Device control failed:', response.statusText);
            }
        } catch (error) {
            console.error('Device control error:', error);
        }
    }

    setDeviceColor(deviceId, colorHex) {
        // Convert hex to RGB
        const r = parseInt(colorHex.slice(1, 3), 16);
        const g = parseInt(colorHex.slice(3, 5), 16);
        const b = parseInt(colorHex.slice(5, 7), 16);
        
        this.controlDevice(deviceId, 'color', {color: {r, g, b}});
    }

    async scanDevices() {
        const scanBtn = document.getElementById('scanBtn');
        const originalText = scanBtn.textContent;
        scanBtn.textContent = 'Scanning...';
        scanBtn.disabled = true;

        try {
            const response = await fetch('/devices/scan', {method: 'POST'});
            if (response.ok) {
                // Wait a bit for scan to complete
                setTimeout(async () => {
                    await this.loadDevices();
                    scanBtn.textContent = originalText;
                    scanBtn.disabled = false;
                }, 3000);
            }
        } catch (error) {
            console.error('Device scan failed:', error);
            scanBtn.textContent = originalText;
            scanBtn.disabled = false;
        }
    }

    async toggleVoice() {
        const voiceBtn = document.getElementById('voiceBtn');
        const voiceInstructions = document.getElementById('voiceInstructions');

        if (this.isVoiceListening) {
            // Stop listening
            this.isVoiceListening = false;
            voiceBtn.classList.remove('listening');
            voiceBtn.textContent = '🎤';
            voiceInstructions.textContent = this.translate('voiceInstructions');
        } else {
            // Start listening
            this.isVoiceListening = true;
            voiceBtn.classList.add('listening');
            voiceBtn.textContent = '🔴';
            voiceInstructions.textContent = this.translate('listening');

            try {
                const response = await fetch('/voice/listen', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({timeout: 5.0})
                });

                const data = await response.json();
                
                if (data.text) {
                    // Process the voice command
                    this.addChatMessage(data.text, 'user');
                    await this.processMessage(data.text);
                }
            } catch (error) {
                console.error('Voice listening failed:', error);
            } finally {
                this.isVoiceListening = false;
                voiceBtn.classList.remove('listening');
                voiceBtn.textContent = '🎤';
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
        
        // Add processing indicator
        const processingDiv = document.createElement('div');
        processingDiv.className = 'chat-message assistant';
        processingDiv.innerHTML = `<em>${this.translate('processing')}</em>`;
        chatContainer.appendChild(processingDiv);
        chatContainer.scrollTop = chatContainer.scrollHeight;

        try {
            const response = await fetch('/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    message: message,
                    session_id: 'web_session'
                })
            });

            const data = await response.json();
            
            // Remove processing indicator
            chatContainer.removeChild(processingDiv);
            
            if (data.response) {
                this.addChatMessage(data.response, 'assistant');
                
                // If voice is available, speak the response
                try {
                    await fetch('/voice/speak', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({text: data.response, blocking: false})
                    });
                } catch (voiceError) {
                    // Voice not available, continue without speaking
                }
            }
        } catch (error) {
            // Remove processing indicator
            chatContainer.removeChild(processingDiv);
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

    async saveVoiceSettings() {
        const sttProvider = document.getElementById('sttProvider').value;
        const ttsProvider = document.getElementById('ttsProvider').value;
        const wakeWords = document.getElementById('wakeWords').value;

        const settings = {
            stt_provider: sttProvider,
            tts_provider: ttsProvider,
            wake_words: wakeWords.split(',').map(w => w.trim())
        };

        try {
            const response = await fetch('/voice/settings', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(settings)
            });

            if (response.ok) {
                alert('Voice settings saved successfully!');
            } else {
                alert('Failed to save voice settings.');
            }
        } catch (error) {
            console.error('Failed to save voice settings:', error);
            alert('Failed to save voice settings.');
        }
    }

    async saveSettings() {
        const spotifyClientId = document.getElementById('spotifyClientId').value;
        const spotifyClientSecret = document.getElementById('spotifyClientSecret').value;
        const openaiApiKey = document.getElementById('openaiApiKey').value;

        const settings = {
            spotify: {
                client_id: spotifyClientId,
                client_secret: spotifyClientSecret
            },
            openai: {
                api_key: openaiApiKey
            }
        };

        try {
            const response = await fetch('/settings', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(settings)
            });

            if (response.ok) {
                alert('Settings saved successfully!');
            } else {
                alert('Failed to save settings.');
            }
        } catch (error) {
            console.error('Failed to save settings:', error);
            alert('Failed to save settings.');
        }
    }
}

// Tab functionality
function showTab(tabName) {
    // Hide all tab contents
    const contents = document.querySelectorAll('.tab-content');
    contents.forEach(content => content.classList.add('hidden'));

    // Remove active class from all tabs
    const tabs = document.querySelectorAll('.tab');
    tabs.forEach(tab => tab.classList.remove('active'));

    // Show selected tab content
    document.getElementById(tabName).classList.remove('hidden');

    // Add active class to selected tab
    event.target.classList.add('active');
}

// Keyboard shortcut handlers
function handleChatKeypress(event) {
    if (event.key === 'Enter') {
        ui.sendMessage();
    }
}

// Initialize the UI when page loads
let ui;
document.addEventListener('DOMContentLoaded', () => {
    ui = new HomeAssistantUI();
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