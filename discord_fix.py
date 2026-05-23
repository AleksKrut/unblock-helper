"""Исправление Discord при зависании на Checking for updates."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

from app_paths import DISCORD_HOSTS_FILE
from dpi import get_bundle_root, start as dpi_start, stop as dpi_stop

DISCORD_STRATEGIES = [
    "general (ALT).bat",
    "general (ALT2).bat",
    "general (FAKE TLS AUTO).bat",
    "general.bat",
]


def _lists_dir() -> Path | None:
    root = get_bundle_root()
    return (root / "lists") if root else None


def _load_extra_hosts() -> list[str]:
    hosts: list[str] = []
    if DISCORD_HOSTS_FILE.is_file():
        for line in DISCORD_HOSTS_FILE.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                hosts.append(line.split()[0])
    return hosts


def patch_user_hostlist() -> tuple[bool, str]:
    lists = _lists_dir()
    if not lists:
        return False, "Сначала установите движок: python main.py dpi-install"

    user_file = lists / "list-general-user.txt"
    existing: set[str] = set()
    if user_file.is_file():
        for line in user_file.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip().lower()
            if line and not line.startswith("#"):
                existing.add(line.split()[0])

    added = [h for h in _load_extra_hosts() if h.lower() not in existing]

    lines: list[str] = []
    if user_file.is_file():
        for line in user_file.read_text(encoding="utf-8", errors="replace").splitlines():
            if "domain.example" in line.lower():
                continue
            lines.append(line.rstrip())
    else:
        lines = ["# Discord (unblock-helper)"]

    lines.extend(added)
    user_file.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")

    if added:
        return True, f"Добавлены домены: {', '.join(added)}"
    return True, "Домены обновлений уже в списке"


def kill_discord() -> None:
    for exe in ("Discord.exe", "Update.exe"):
        subprocess.run(
            ["taskkill", "/IM", exe, "/F"],
            capture_output=True,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
        )


def clear_discord_cache() -> tuple[bool, str]:
    kill_discord()
    removed: list[str] = []

    appdata = Path(os.environ.get("APPDATA", "")) / "discord"
    local = Path(os.environ.get("LOCALAPPDATA", ""))

    for path in (
        appdata / "Cache",
        appdata / "Code Cache",
        appdata / "GPUCache",
        appdata / "component_crx_cache",
        local / "Discord" / "SquirrelTemp",
    ):
        if path.exists():
            try:
                shutil.rmtree(path)
                removed.append(path.name)
            except OSError:
                pass

    if removed:
        return True, f"Очищен кэш: {', '.join(removed)}"
    return True, "Кэш пуст или папки не найдены"


def restart_dpi_for_discord(strategy: str | None = None) -> tuple[bool, str]:
    dpi_stop()
    return dpi_start(strategy or DISCORD_STRATEGIES[0])


def run_full_fix(
    use_hosts: bool = False,
    strategy: str | None = None,
    log: callable[[str], None] | None = None,
) -> int:
    def out(msg: str) -> None:
        if log:
            log(msg)
        else:
            print(msg)

    out("=== Исправление Discord ===")

    ok, msg = patch_user_hostlist()
    out(f"[1] Списки: {msg}")
    if not ok:
        return 1

    if use_hosts:
        ok, msg = _apply_hosts_snippet()
        out(f"[2] Hosts: {msg}")
    else:
        out("[2] Hosts: пропущено")

    ok, msg = clear_discord_cache()
    out(f"[3] Кэш: {msg}")

    strat = strategy or DISCORD_STRATEGIES[0]
    ok, msg = restart_dpi_for_discord(strat)
    out(f"[4] DPI ({strat}): {msg}")
    if not ok:
        out("Попробуйте автоподбор стратегии.")
        return 1

    out("Готово. Перезапустите Discord из меню Пуск.")
    return 0


def _apply_hosts_snippet() -> tuple[bool, str]:
    hosts_path = Path(os.environ.get("SystemRoot", r"C:\Windows")) / "System32" / "drivers" / "etc" / "hosts"
    marker = "# unblock-helper discord"
    entries = [
        "",
        marker,
        "104.16.248.249 updates.discord.com",
        "104.16.248.249 dl.discordapp.net",
        "104.16.248.249 stable.dl2.discordapp.net",
    ]
    try:
        content = hosts_path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return False, f"Нет доступа к hosts: {exc}"
    if marker in content:
        return True, "Записи уже есть"
    try:
        with hosts_path.open("a", encoding="utf-8") as f:
            f.write("\n".join(entries) + "\n")
        return True, "Записи добавлены (нужен перезапуск DNS: ipconfig /flushdns)"
    except OSError as exc:
        return False, str(exc)
