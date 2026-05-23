"""Пути проекта: исходники, EXE (PyInstaller), данные."""

from __future__ import annotations

import sys
from pathlib import Path


def is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def get_root() -> Path:
    """Каталог с config, zapret-cache, logs."""
    if is_frozen():
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def get_resource_root() -> Path:
    """Каталог с упакованными data/ (только EXE)."""
    if is_frozen():
        return Path(getattr(sys, "_MEIPASS", get_root()))
    return get_root()


ROOT = get_root()
RESOURCE_ROOT = get_resource_root()
DATA_DIR = RESOURCE_ROOT / "data"
ZAPRET_CACHE = ROOT / "zapret-cache"
STATE_PATH = ROOT / "zapret-state.json"
CONFIG_PATH = ROOT / "config.json"
CONFIG_EXAMPLE = ROOT / "config.example.json"
LOG_DIR = ROOT / "logs"
LOG_FILE = LOG_DIR / "desktop.log"
DISCORD_HOSTS_FILE = DATA_DIR / "discord-hosts.txt"
