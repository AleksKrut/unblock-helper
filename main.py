#!/usr/bin/env python3
"""CLI Unblock Helper (опционально: UnblockHelper.bat cli …)."""

from __future__ import annotations

import argparse
import asyncio
import sys

from checker import all_ok, format_results, run_checks
from config_store import get_strategy, set_strategy
from discord_fix import run_full_fix
from dpi import (
    auto_find,
    get_bundle_root,
    install as dpi_install,
    is_admin as dpi_is_admin,
    list_strategies,
    request_admin,
    start as dpi_start,
    status_text as dpi_status_text,
    stop as dpi_stop,
)


async def cmd_check() -> int:
    results = await run_checks()
    print(format_results(results, "напрямую"))
    return 0 if all_ok(results) else 1


def main() -> None:
    p = argparse.ArgumentParser(description="Unblock Helper CLI")
    sub = p.add_subparsers(dest="command", required=True)

    sub.add_parser("check").set_defaults(func=lambda _: asyncio.run(cmd_check()))

    i = sub.add_parser("dpi-install")
    i.add_argument("--force", action="store_true")
    i.set_defaults(func=lambda a: print(dpi_install(force=a.force)[1]) or 0)

    s = sub.add_parser("dpi-start")
    s.add_argument("--strategy", "-s")
    s.add_argument("--admin", action="store_true")
    s.set_defaults(
        func=lambda a: (
            request_admin(["dpi-start", "--strategy", a.strategy or get_strategy()])
            if a.admin and not dpi_is_admin()
            else (print(dpi_start(a.strategy or get_strategy())[1]) or 0)
        ),
    )

    sub.add_parser("dpi-stop").set_defaults(
        func=lambda _: print(dpi_stop()[1]) or 0,
    )
    sub.add_parser("dpi-status").set_defaults(
        func=lambda _: print(dpi_status_text()) or 0,
    )
    sub.add_parser("dpi-list").set_defaults(
        func=lambda _: [print(x) for x in list_strategies(get_bundle_root())] if get_bundle_root() else 1,
    )

    a = sub.add_parser("dpi-auto")
    a.add_argument("--admin", action="store_true")
    a.set_defaults(
        func=lambda ar: (
            request_admin(["dpi-auto", "--admin"])
            if ar.admin and not dpi_is_admin()
            else (print(auto_find(lambda: all_ok(asyncio.run(run_checks())))[1]) or 0)
        ),
    )

    d = sub.add_parser("discord-fix")
    d.add_argument("--admin", action="store_true")
    d.add_argument("--hosts", action="store_true")
    d.set_defaults(
        func=lambda ar: (
            request_admin(["discord-fix", "--admin"])
            if ar.admin and not dpi_is_admin()
            else sys.exit(run_full_fix(use_hosts=ar.hosts, strategy=get_strategy()))
        ),
    )

    args = p.parse_args()
    code = args.func(args)
    if code:
        sys.exit(code)


if __name__ == "__main__":
    main()
