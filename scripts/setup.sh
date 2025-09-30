#!/bin/bash
# Скрипт для первичной настройки Home Assistant AI

set -e

echo "🏠 Настройка Home Assistant AI..."

# Проверка Python версии
python_version=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1-2)
required_version="3.9"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Требуется Python $required_version или выше, установлена версия $python_version"
    exit 1
fi

echo "✅ Python $python_version обнаружен"

# Создание виртуального окружения
if [ ! -d "venv" ]; then
    echo "📦 Создание виртуального окружения..."
    python3 -m venv venv
fi

# Активация виртуального окружения
echo "🔧 Активация виртуального окружения..."
source venv/bin/activate

# Обновление pip
echo "⬆️ Обновление pip..."
pip install --upgrade pip

# Установка зависимостей
echo "📚 Установка зависимостей..."
pip install -e .

# Установка dev зависимостей
echo "🛠️ Установка зависимостей для разработки..."
pip install -e ".[development]"

# Создание необходимых директорий
echo "📁 Создание директорий..."
mkdir -p data config logs

# Копирование примеров конфигурации
if [ ! -f ".env" ]; then
    echo "📋 Создание файла .env..."
    cp .env.example .env
    echo "⚠️ Не забудьте отредактировать .env файл"
fi

if [ ! -f "config/config.yaml" ]; then
    echo "📋 Создание файла конфигурации..."
    cp config/config.example.yaml config/config.yaml
    echo "⚠️ Не забудьте отредактировать config/config.yaml"
fi

# Проверка установки
echo "🧪 Проверка установки..."
python -c "import home_assistant; print('✅ Home Assistant AI успешно установлен!')"

echo ""
echo "🎉 Настройка завершена!"
echo ""
echo "Для запуска системы выполните:"
echo "  source venv/bin/activate"
echo "  python -m home_assistant"
echo ""
echo "Или используйте скрипт быстрого запуска:"
echo "  ./scripts/run.sh"
echo ""
echo "Документация: docs/README.md"
