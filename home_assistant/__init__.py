"""
Home Assistant AI - Универсальный умный дом с AI reasoning.

Этот пакет предоставляет полнофункциональную платформу для управления
умным домом с поддержкой множества протоколов связи и интеллектуальным
ассистентом на базе LLM.
"""

__version__ = "0.1.0"
__author__ = "Даниил Василевский"
__email__ = "user@example.com"

from .core.config import HomeAssistantConfig
from .core.lifecycle import HomeAssistant

__all__ = ["HomeAssistant", "HomeAssistantConfig"]