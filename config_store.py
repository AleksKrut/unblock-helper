"""Чтение и запись config.json."""

from __future__ import annotations

import json

from app_paths import CONFIG_EXAMPLE, CONFIG_PATH


def load_config() -> dict:
    if CONFIG_PATH.is_file():
        with CONFIG_PATH.open(encoding="utf-8") as f:
            return json.load(f)
    if CONFIG_EXAMPLE.is_file():
        with CONFIG_EXAMPLE.open(encoding="utf-8") as f:
            return json.load(f)
    return {"dpi_strategy": "general (ALT).bat"}


def save_config(cfg: dict) -> None:
    with CONFIG_PATH.open("w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


def get_strategy() -> str:
    return load_config().get("dpi_strategy", "general (ALT).bat")


def set_strategy(name: str) -> None:
    cfg = load_config()
    cfg["dpi_strategy"] = name
    save_config(cfg)
