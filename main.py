#!/usr/bin/env python3
"""Unblock Helper — обход блокировок YouTube и Discord на Windows (DPI / zapret)."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

from checker import all_ok, format_results, run_checks
from discord_fix import run_full_fix
from dpi import (
    auto_find,
    install as dpi_install,
    is_admin as dpi_is_admin,
    list_strategies,
    request_admin,
    start as dpi_start,
    status_text as dpi_status_text,
    stop as dpi_stop,
    get_bundle_root,
)

ROOT = Path(__file__).resolve().parent
CONFIG_PATH = ROOT / "config.json"


def load_config() -> dict:
    if CONFIG_PATH.is_file():
        with CONFIG_PATH.open(encoding="utf-8") as f:
            return json.load(f)
    example = ROOT / "config.example.json"
    if example.is_file():
        with example.open(encoding="utf-8") as f:
            return json.load(f)
    return {"dpi_strategy": "general.bat"}


async def cmd_check() -> int:
    results = await run_checks()
    print(format_results(results, "напрямую"))
    if not all_ok(results):
        print("\nПодсказка: start-dpi.bat или start-dpi-auto.bat (от администратора)")
        return 1
    return 0


def cmd_dpi_install(force: bool) -> int:
    ok, msg = dpi_install(force=force)
    print(msg)
    return 0 if ok else 1


def cmd_dpi_start(strategy: str | None, as_admin: bool) -> int:
    if as_admin and not dpi_is_admin():
        extra = ["dpi-start", "--admin"]
        if strategy:
            extra.extend(["--strategy", strategy])
        request_admin(extra)
        return 0

    strategy = strategy or load_config().get("dpi_strategy")
    ok, msg = dpi_start(strategy)
    print(msg)
    if ok:
        print()
        print(dpi_status_text())
        print("\nПроверка: python main.py check")
    return 0 if ok else 1


def cmd_dpi_stop() -> int:
    ok, msg = dpi_stop()
    print(msg)
    return 0 if ok else 1


def cmd_dpi_status() -> None:
    print(dpi_status_text())
    root = get_bundle_root()
    if root:
        print("\nСтратегии:")
        for s in list_strategies(root):
            print(f"  - {s}")


def cmd_dpi_list() -> int:
    root = get_bundle_root()
    if not root:
        print("Движок не установлен: python main.py dpi-install")
        return 1
    for s in list_strategies(root):
        print(s)
    return 0


def cmd_dpi_auto(as_admin: bool) -> int:
    if as_admin and not dpi_is_admin():
        request_admin(["dpi-auto", "--admin"])
        return 0

    ok, msg = auto_find(lambda: all_ok(asyncio.run(run_checks())))
    print(msg)
    if ok:
        asyncio.run(cmd_check())
        return 0
    return 1


def cmd_discord_fix(as_admin: bool, use_hosts: bool, strategy: str | None) -> int:
    if as_admin and not dpi_is_admin():
        extra = ["discord-fix", "--admin"]
        if use_hosts:
            extra.append("--hosts")
        if strategy:
            extra.extend(["--strategy", strategy])
        request_admin(extra)
        return 0
    return run_full_fix(use_hosts=use_hosts, strategy=strategy)


def cmd_menu() -> None:
    print(
        """
=== Unblock Helper ===

  A - Установить DPI-движок
  B - Запустить обход
  C - Остановить обход
  D - Статус
  E - Автоподбор стратегии
  F - Исправить Discord (updates)
  1 - Проверить сайты
  0 - Выход

Быстрый запуск: start-dpi.bat | start-dpi-auto.bat | fix-discord.bat
"""
    )
    cfg = load_config()
    actions = {
        "A": lambda: cmd_dpi_install(False),
        "B": lambda: cmd_dpi_start(cfg.get("dpi_strategy"), True),
        "C": cmd_dpi_stop,
        "D": lambda: (cmd_dpi_status(), 0)[1],
        "E": lambda: cmd_dpi_auto(True),
        "F": lambda: cmd_discord_fix(True, False, None),
        "1": lambda: asyncio.run(cmd_check()),
        "0": lambda: sys.exit(0),
    }
    fn = actions.get(input("Выбор: ").strip().upper())
    if fn:
        code = fn()
        if isinstance(code, int) and code:
            sys.exit(code)
    else:
        print("Неизвестный пункт.")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Обход блокировок YouTube и Discord")
    sub = p.add_subparsers(dest="command")

    sub.add_parser("menu").set_defaults(func=lambda _: (cmd_menu(), 0)[1])

    sub.add_parser("check", help="Проверить YouTube / Discord").set_defaults(
        func=lambda _: asyncio.run(cmd_check()),
    )

    dpi_i = sub.add_parser("dpi-install", help="Скачать zapret-discord-youtube")
    dpi_i.add_argument("--force", action="store_true")
    dpi_i.set_defaults(func=lambda a: cmd_dpi_install(a.force))

    dpi_s = sub.add_parser("dpi-start", help="Запустить обход DPI")
    dpi_s.add_argument("--strategy", "-s")
    dpi_s.add_argument("--admin", action="store_true")
    dpi_s.set_defaults(func=lambda a: cmd_dpi_start(a.strategy, a.admin))

    sub.add_parser("dpi-stop").set_defaults(func=lambda _: cmd_dpi_stop())
    sub.add_parser("dpi-status").set_defaults(func=lambda _: (cmd_dpi_status(), 0)[1])
    sub.add_parser("dpi-list").set_defaults(func=lambda _: cmd_dpi_list())

    dpi_a = sub.add_parser("dpi-auto", help="Подобрать рабочую стратегию")
    dpi_a.add_argument("--admin", action="store_true")
    dpi_a.set_defaults(func=lambda a: cmd_dpi_auto(a.admin))

    dfix = sub.add_parser("discord-fix", help="Discord: Checking for updates")
    dfix.add_argument("--admin", action="store_true")
    dfix.add_argument("--hosts", action="store_true")
    dfix.add_argument("--strategy", "-s")
    dfix.set_defaults(
        func=lambda a: cmd_discord_fix(a.admin, a.hosts, a.strategy),
    )

    return p


def main() -> None:
    args = build_parser().parse_args()
    if not args.command:
        cmd_menu()
        return
    code = args.func(args)
    if code:
        sys.exit(code)


if __name__ == "__main__":
    main()
