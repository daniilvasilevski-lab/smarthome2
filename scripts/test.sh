#!/bin/bash
# Скрипт для запуска тестов

set -e

# Активация виртуального окружения
if [ -d "venv" ]; then
    source venv/bin/activate
fi

echo "🧪 Запуск тестов Home Assistant AI..."

# Проверка стиля кода
echo "📝 Проверка стиля кода..."
echo "  - Форматирование (black)..."
black --check home_assistant/ || echo "⚠️ Требуется форматирование: black home_assistant/"

echo "  - Сортировка импортов (isort)..."
isort --check-only home_assistant/ || echo "⚠️ Требуется сортировка импортов: isort home_assistant/"

echo "  - Линтинг (flake8)..."
flake8 home_assistant/ || echo "⚠️ Обнаружены проблемы линтинга"

echo "  - Проверка типов (mypy)..."
mypy home_assistant/ || echo "⚠️ Обнаружены проблемы с типами"

# Запуск тестов
echo "🔬 Запуск unit тестов..."
pytest tests/ -v --cov=home_assistant --cov-report=html --cov-report=term

echo ""
echo "✅ Тестирование завершено!"
echo "📊 Отчет о покрытии: htmlcov/index.html"
