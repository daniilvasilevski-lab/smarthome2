"""
Точка входа для запуска Home Assistant AI как модуля.

Использование:
    python -m home_assistant
"""

import asyncio
import sys
from pathlib import Path

from .core.lifecycle_main import main

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nПолучен сигнал завершения. Выход...")
        sys.exit(0)
    except Exception as e:
        print(f"Критическая ошибка: {e}")
        sys.exit(1)