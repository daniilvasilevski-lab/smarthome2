#!/bin/bash
# Скрипт для запуска Home Assistant AI

set -e

# Проверка виртуального окружения
if [ ! -d "venv" ]; then
    echo "❌ Виртуальное окружение не найдено. Запустите scripts/setup.sh"
    exit 1
fi

# Активация виртуального окружения
echo "🔧 Активация виртуального окружения..."
source venv/bin/activate

# Проверка конфигурации
if [ ! -f "config/config.yaml" ]; then
    echo "❌ Файл конфигурации не найден. Скопируйте config/config.example.yaml в config/config.yaml"
    exit 1
fi

echo "🏠 Запуск Home Assistant AI..."
echo "📊 Логи будут сохранены в logs/home_assistant.log"
echo "🌐 API будет доступен на http://localhost:8000"
echo "📖 Документация API: http://localhost:8000/docs"
echo ""
echo "Для остановки нажмите Ctrl+C"
echo ""

# Создание директории для логов
mkdir -p logs

# Запуск системы
python -m home_assistant 2>&1 | tee logs/home_assistant.log
