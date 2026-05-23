"""Один экземпляр GUI."""

from __future__ import annotations

import atexit
import os
import sys
import tempfile
from pathlib import Path

PID_FILE = Path(tempfile.gettempdir()) / "unblock-helper-desktop.pid"


def _pid_alive(pid: int) -> bool:
    if sys.platform != "win32":
        return False
    import ctypes

    PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
    handle = ctypes.windll.kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
    if not handle:
        return False
    code = ctypes.c_ulong()
    ctypes.windll.kernel32.GetExitCodeProcess(handle, ctypes.byref(code))
    ctypes.windll.kernel32.CloseHandle(handle)
    return code.value == 259


def release_stale(force: bool = False) -> None:
    """Завершить зависшие python/pythonw с desktop\\app.py."""
    if sys.platform != "win32":
        return
    import subprocess

    for img in ("python.exe", "pythonw.exe", "UnblockHelper.exe"):
        r = subprocess.run(
            ["tasklist", "/FI", f"IMAGENAME eq {img}", "/FO", "CSV", "/NH"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        for line in (r.stdout or "").splitlines():
            if not line.strip():
                continue
            parts = line.split(",")
            if len(parts) < 2:
                continue
            try:
                pid = int(parts[1].strip('"'))
            except ValueError:
                continue
            if pid == os.getpid():
                continue
            wr = subprocess.run(
                [
                    "wmic", "process", "where", f"ProcessId={pid}",
                    "get", "CommandLine", "/FORMAT:VALUE",
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            cmd = wr.stdout or ""
            if ("desktop" in cmd and "app.py" in cmd) or "UnblockHelper" in cmd:
                if force or not _pid_alive(pid):
                    subprocess.run(
                        ["taskkill", "/PID", str(pid), "/F"],
                        capture_output=True,
                        creationflags=subprocess.CREATE_NO_WINDOW,
                    )
    try:
        PID_FILE.unlink(missing_ok=True)
    except OSError:
        pass


def acquire() -> bool:
    if PID_FILE.is_file():
        try:
            old = int(PID_FILE.read_text(encoding="utf-8").strip())
        except ValueError:
            old = 0
        if old and old != os.getpid() and _pid_alive(old):
            return False
        PID_FILE.unlink(missing_ok=True)

    PID_FILE.write_text(str(os.getpid()), encoding="utf-8")

    def _release() -> None:
        try:
            if PID_FILE.is_file() and PID_FILE.read_text(encoding="utf-8").strip() == str(os.getpid()):
                PID_FILE.unlink()
        except OSError:
            pass

    atexit.register(_release)
    return True


def show_already_running() -> None:
    if sys.platform != "win32":
        return
    import ctypes

    ctypes.windll.user32.MessageBoxW(
        0,
        "Unblock Helper уже запущен.\n\n"
        "Проверьте панель задач.\n"
        "Или: вкладка «Сервисы» → «Завершить зависший процесс».",
        "Unblock Helper",
        0x40,
    )
