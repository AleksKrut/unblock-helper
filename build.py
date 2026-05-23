#!/usr/bin/env python3
"""Сборка UnblockHelper.exe (PyInstaller)."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def main() -> int:
    try:
        import PyInstaller  # noqa: F401
    except ImportError:
        print("Установка PyInstaller…")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller>=6.0"])
        import PyInstaller  # noqa: F401

    sep = os.pathsep
    data = ROOT / "data"
    cfg = ROOT / "config.example.json"

    args = [
        str(ROOT / "desktop" / "app.py"),
        "--name=UnblockHelper",
        "--windowed",
        "--noconfirm",
        "--clean",
        f"--distpath={ROOT / 'dist'}",
        f"--workpath={ROOT / 'build'}",
        f"--specpath={ROOT}",
        f"--add-data={data}{sep}data",
        f"--add-data={cfg}{sep}.",
        "--hidden-import=customtkinter",
        "--collect-all=customtkinter",
        "--hidden-import=httpx",
        "--hidden-import=anyio",
    ]

    import PyInstaller.__main__

    print("Сборка…")
    PyInstaller.__main__.run(args)

    out = ROOT / "dist" / "UnblockHelper"
    exe = out / "UnblockHelper.exe"
    if not exe.is_file():
        print("Ошибка: EXE не найден")
        return 1

    shutil.copy2(cfg, out / "config.example.json")
    readme = (
        "Unblock Helper\n\n"
        "1. Запустите UnblockHelper.exe от имени администратора\n"
        "2. Установить движок → Запустить обход\n\n"
        "zapret-cache создаётся рядом с EXE.\n"
    )
    (out / "КАК_ЗАПУСТИТЬ.txt").write_text(readme, encoding="utf-8")

    print(f"\nГотово: {exe}")
    print(f"Папка: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
