"""
Обход DPI (как zapret): загрузка zapret-discord-youtube и управление стратегиями.

Движок — open-source winws из https://github.com/Flowseal/zapret-discord-youtube
(лицензия проекта — см. их репозиторий).
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import time
import urllib.request
import zipfile
from pathlib import Path

from app_paths import ROOT, STATE_PATH, ZAPRET_CACHE

GITHUB_API = "https://api.github.com/repos/Flowseal/zapret-discord-youtube/releases/latest"
WINWS_IMAGE = "winws.exe"

# Порядок перебора при автоподборе (сначала самые популярные)
PREFERRED_STRATEGIES = [
    "general.bat",
    "general (ALT).bat",
    "general (ALT2).bat",
    "general (ALT3).bat",
    "general (ALT4).bat",
    "general (ALT5).bat",
    "general (ALT6).bat",
    "general (ALT7).bat",
    "general (ALT8).bat",
    "general (FAKE TLS AUTO).bat",
    "general (SIMPLE FAKE).bat",
]


def is_admin() -> bool:
    if sys.platform != "win32":
        return False
    import ctypes

    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def request_admin(extra_args: list[str] | None = None) -> None:
    """Перезапуск с правами администратора (нужны для WinDivert)."""
    import ctypes

    from app_paths import is_frozen

    if is_frozen():
        exe = sys.executable
        params = " ".join(f'"{a}"' if " " in a else a for a in (extra_args or []))
    else:
        args = [str(Path(sys.argv[0]).resolve()), *(extra_args or sys.argv[1:])]
        if Path(sys.argv[0]).suffix.lower() in (".py", ""):
            exe = sys.executable
            params = " ".join(f'"{a}"' if " " in a else a for a in [exe, *args])
        else:
            exe = str(Path(sys.argv[0]).resolve())
            params = " ".join(f'"{a}"' if " " in a else a for a in args[1:])

    ctypes.windll.shell32.ShellExecuteW(None, "runas", exe, params or None, str(ROOT), 1)
    sys.exit(0)


def load_state() -> dict:
    if STATE_PATH.is_file():
        with STATE_PATH.open(encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_state(state: dict) -> None:
    with STATE_PATH.open("w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def fetch_latest_release() -> dict:
    req = urllib.request.Request(
        GITHUB_API,
        headers={"Accept": "application/vnd.github+json", "User-Agent": "unblock-helper"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode())


def _pick_zip_url(release: dict) -> tuple[str, str]:
    tag = release.get("tag_name", "unknown")
    for asset in release.get("assets", []):
        name = asset.get("name", "")
        if name.endswith(".zip"):
            return asset["browser_download_url"], tag
    raise RuntimeError(f"ZIP-архив не найден в релизе {tag}")


def download_file(url: str, dest: Path, on_progress=None) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": "unblock-helper"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        total = int(resp.headers.get("Content-Length", 0))
        done = 0
        chunk = 256 * 1024
        with dest.open("wb") as out:
            while True:
                data = resp.read(chunk)
                if not data:
                    break
                out.write(data)
                done += len(data)
                if on_progress and total:
                    on_progress(done, total)


def find_bundle_root(search_in: Path) -> Path | None:
    if (search_in / "bin" / WINWS_IMAGE).is_file():
        return search_in
    for child in sorted(search_in.iterdir()):
        if child.is_dir():
            found = find_bundle_root(child)
            if found:
                return found
    return None


def get_bundle_root() -> Path | None:
    state = load_state()
    path = state.get("bundle_root")
    if path:
        p = Path(path)
        if (p / "bin" / WINWS_IMAGE).is_file():
            return p
    if ZAPRET_CACHE.is_dir():
        found = find_bundle_root(ZAPRET_CACHE)
        if found:
            state["bundle_root"] = str(found)
            save_state(state)
            return found
    return None


def _ensure_binaries(zip_path: Path, dest: Path) -> Path | None:
    """Распаковка; при блокировке AV — повтор bin/ из архива."""
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(dest)

    bundle = find_bundle_root(dest)
    if bundle and (bundle / "bin" / WINWS_IMAGE).is_file():
        return bundle

    print("  Повторная распаковка bin/ (winws.exe)...")
    with zipfile.ZipFile(zip_path, "r") as zf:
        for member in zf.namelist():
            norm = member.replace("\\", "/")
            if norm.startswith("bin/"):
                zf.extract(member, dest)

    return find_bundle_root(dest)


def list_strategies(root: Path | None = None) -> list[str]:
    root = root or get_bundle_root()
    if not root:
        return []
    bats = sorted(
        p.name
        for p in root.glob("general*.bat")
        if p.is_file() and "service" not in p.name.lower()
    )
    ordered: list[str] = []
    for name in PREFERRED_STRATEGIES:
        if name in bats:
            ordered.append(name)
    for name in bats:
        if name not in ordered:
            ordered.append(name)
    return ordered


def install(
    force: bool = False,
    log: callable[[str], None] | None = None,
) -> tuple[bool, str]:
    def say(msg: str) -> None:
        if log:
            log(msg)
        else:
            print(msg)

    root = get_bundle_root()
    if root and not force:
        state = load_state()
        ver = state.get("version", "?")
        return True, f"DPI-движок уже установлен (v{ver}): {root}"

    say("Загрузка последнего релиза zapret-discord-youtube...")
    try:
        release = fetch_latest_release()
        url, tag = _pick_zip_url(release)
    except Exception as exc:
        return False, f"Не удалось получить релиз: {exc}"

    zip_path = ZAPRET_CACHE / f"zapret-{tag}.zip"
    if force and zip_path.is_file():
        zip_path.unlink()

    def progress(done: int, total: int) -> None:
        if not total:
            return
        pct = done * 100 // total
        msg = f"Скачано: {pct}% ({done // 1024} KB)"
        if log:
            log(msg)
        else:
            print(f"\r  {msg}", end="", flush=True)

    try:
        if not zip_path.is_file():
            download_file(url, zip_path, on_progress=progress)
            if not log:
                print()
    except Exception as exc:
        return False, f"Ошибка загрузки: {exc}"

    if ZAPRET_CACHE.exists() and force:
        import shutil

        shutil.rmtree(ZAPRET_CACHE, ignore_errors=True)
    ZAPRET_CACHE.mkdir(parents=True, exist_ok=True)

    say("Распаковка...")
    try:
        bundle = _ensure_binaries(zip_path, ZAPRET_CACHE)
    except Exception as exc:
        return False, f"Ошибка распаковки: {exc}"

    if not bundle or not (bundle / "bin" / WINWS_IMAGE).is_file():
        return (
            False,
            "Не найден bin/winws.exe. Добавьте папку unblock-helper в исключения антивируса и "
            "запустите: python main.py dpi-install --force",
        )

    strategies = list_strategies(bundle)
    save_state(
        {
            "version": tag,
            "bundle_root": str(bundle),
            "strategies": strategies,
            "active_strategy": load_state().get("active_strategy"),
        }
    )
    return (
        True,
        f"Установлено v{tag}. Стратегий: {len(strategies)}. Путь: {bundle}",
    )


def is_winws_running() -> bool:
    r = subprocess.run(
        ["tasklist", "/FI", f"IMAGENAME eq {WINWS_IMAGE}", "/NH"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
    )
    return WINWS_IMAGE.lower() in (r.stdout or "").lower()


def stop() -> tuple[bool, str]:
    if not is_winws_running():
        return True, "DPI-обход не запущен."
    r = subprocess.run(
        ["taskkill", "/IM", WINWS_IMAGE, "/F"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
    )
    if r.returncode == 0:
        state = load_state()
        state["active_strategy"] = None
        save_state(state)
        return True, "DPI-обход остановлен (winws.exe)."
    err = (r.stderr or r.stdout or "").strip()
    return False, err or "Не удалось остановить winws.exe"


def _parse_winws_cmdline(bat_path: Path) -> str | None:
    text = bat_path.read_text(encoding="utf-8", errors="replace")
    # Одна длинная строка winws с продолжениями ^
    m = re.search(r'winws\.exe\s+(.+?)(?:\r?\n(?!\s*--)|\Z)', text, re.DOTALL | re.I)
    if not m:
        return None
    args = m.group(1)
    args = args.replace("^\r\n", " ").replace("^\n", " ")
    args = re.sub(r"\s+", " ", args).strip()
    # Подставить переменные %~dp0
    root = bat_path.parent
    bin_dir = root / "bin"
    lists = root / "lists"

    def repl(match: re.Match) -> str:
        key = match.group(1).upper()
        if key in ("BIN",):
            return str(bin_dir).rstrip("\\") + "\\"
        if key in ("LISTS",):
            return str(lists).rstrip("\\") + "\\"
        return str(root).rstrip("\\") + "\\"

    args = re.sub(r"%~dp0", lambda _: str(root).rstrip("\\") + "\\", args, flags=re.I)
    args = re.sub(r"%BIN%", str(bin_dir).rstrip("\\") + "\\", args, flags=re.I)
    args = re.sub(r"%LISTS%", str(lists).rstrip("\\") + "\\", args, flags=re.I)
    return args


def start(strategy: str | None = None, *, use_bat: bool = True) -> tuple[bool, str]:
    if not is_admin():
        return (
            False,
            "Нужны права администратора. Запустите: python main.py dpi-start --admin",
        )

    root = get_bundle_root()
    if not root:
        ok, msg = install()
        if not ok:
            return False, msg
        root = get_bundle_root()
    assert root

    strategies = list_strategies(root)
    if not strategies:
        return False, f"Стратегии general*.bat не найдены в {root}"

    if strategy is None:
        strategy = load_state().get("active_strategy") or strategies[0]

    if strategy not in strategies:
        # нечёткое совпадение
        low = strategy.lower()
        match = next((s for s in strategies if low in s.lower()), None)
        if not match:
            return False, f"Стратегия «{strategy}» не найдена. Доступно: {', '.join(strategies[:5])}..."
        strategy = match

    if is_winws_running():
        stop()

    bat_path = root / strategy
    winws = root / "bin" / WINWS_IMAGE
    if not winws.is_file():
        return False, f"Не найден {winws}"

    if use_bat and bat_path.is_file():
        # Как в оригинале: cmd запускает bat, bat делает start /min winws
        proc = subprocess.Popen(
            ["cmd", "/c", str(bat_path)],
            cwd=str(root),
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        time.sleep(2.5)
        if proc.poll() not in (None, 0) and not is_winws_running():
            return False, f"Батник завершился с кодом {proc.returncode}"
    else:
        args_line = _parse_winws_cmdline(bat_path)
        if not args_line:
            return False, f"Не удалось разобрать команду из {bat_path.name}"
        import shlex

        cmd = [str(winws), *shlex.split(args_line, posix=False)]
        subprocess.Popen(
            cmd,
            cwd=str(root / "bin"),
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        time.sleep(2.5)

    if not is_winws_running():
        return (
            False,
            f"winws.exe не запустился ({strategy}). Попробуйте другую стратегию или service.bat из bundle.",
        )

    state = load_state()
    state["active_strategy"] = strategy
    save_state(state)
    return True, f"DPI-обход запущен: {strategy}"


def status_text() -> str:
    state = load_state()
    lines = [
        "--- DPI (zapret) ---",
        f"Версия: {state.get('version', 'не установлен')}",
        f"Процесс winws: {'запущен' if is_winws_running() else 'остановлен'}",
    ]
    if state.get("active_strategy"):
        lines.append(f"Стратегия: {state['active_strategy']}")
    root = get_bundle_root()
    if root:
        lines.append(f"Каталог: {root}")
        strats = list_strategies(root)
        lines.append(f"Доступно стратегий: {len(strats)}")
    return "\n".join(lines)


def auto_find(
    check_fn,
    wait_sec: float = 4.0,
    log: callable[[str], None] | None = None,
) -> tuple[bool, str]:
    """
    Перебирает стратегии, пока check_fn() не вернёт True.
    check_fn — синхронная функция без аргументов.
    """
    if not is_admin():
        return False, "Для автоподбора нужен запуск от администратора."

    def say(msg: str) -> None:
        if log:
            log(msg)
        else:
            print(msg)

    ok, msg = install(log=log)
    if not ok:
        return False, msg
    say(msg)

    root = get_bundle_root()
    assert root
    strategies = list_strategies(root)
    if not strategies:
        return False, "Нет стратегий для перебора."

    say(f"Перебор {len(strategies)} стратегий...")

    for i, name in enumerate(strategies, 1):
        say(f"[{i}/{len(strategies)}] {name}")
        stop()
        ok, start_msg = start(name)
        if not ok:
            say(f"  пропуск: {start_msg}")
            continue
        time.sleep(wait_sec)
        if check_fn():
            save_state({**load_state(), "active_strategy": name})
            return True, f"Рабочая стратегия: {name}"
        say("  сайты недоступны")

    stop()
    return False, "Ни одна стратегия не помогла. Попробуйте обновить движок (переустановка)."
