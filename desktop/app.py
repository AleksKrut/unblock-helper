#!/usr/bin/env python3
"""Unblock Helper — полноценное десктоп-приложение."""

from __future__ import annotations

import asyncio
import os
import subprocess
import sys
import threading
import traceback
import webbrowser
from pathlib import Path

# Пути до импорта остальных модулей
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app_paths import (  # noqa: E402
    LOG_DIR,
    LOG_FILE,
    ROOT as APP_ROOT,
    ZAPRET_CACHE,
    is_frozen,
)
from config_store import get_strategy, load_config, set_strategy  # noqa: E402

REFRESH_MS = 3000
APP_VERSION = "1.1.0"


def _write_log(text: str) -> None:
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        with LOG_FILE.open("a", encoding="utf-8") as f:
            f.write(text.rstrip() + "\n")
    except OSError:
        pass


def run_async(coro):
    return asyncio.run(coro)


def relaunch_as_admin() -> None:
    import ctypes

    exe = sys.executable
    params = "" if is_frozen() else f'"{Path(__file__).resolve()}"'
    ctypes.windll.shell32.ShellExecuteW(None, "runas", exe, params or None, str(APP_ROOT), 1)
    sys.exit(0)


def _show_fatal(msg: str) -> None:
    _write_log(msg)
    if sys.platform == "win32":
        import ctypes

        ctypes.windll.user32.MessageBoxW(
            0, f"{msg}\n\n{LOG_FILE}", "Unblock Helper", 0x10,
        )


def _open_folder(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    os.startfile(str(path))  # noqa: S606 — Windows only


def main() -> None:
    from desktop.instance import acquire, release_stale, show_already_running

    release_stale()
    if not acquire():
        show_already_running()
        return

    try:
        import customtkinter as ctk
    except ImportError as exc:
        _show_fatal(f"Установите зависимости:\npip install -r requirements.txt\n\n{exc}")
        return

    from checker import CheckResult, all_ok, run_checks
    from discord_fix import run_full_fix
    from dpi import (
        auto_find,
        get_bundle_root,
        install as dpi_install,
        is_admin,
        is_winws_running,
        list_strategies,
        load_state,
        start as dpi_start,
        status_text,
        stop as dpi_stop,
    )

    class UnblockApp(ctk.CTk):
        def __init__(self) -> None:
            super().__init__()
            self.title("Unblock Helper")
            self.geometry("580x720")
            self.minsize(520, 640)

            ctk.set_appearance_mode("dark")
            ctk.set_default_color_theme("blue")

            self._busy = False
            self._closing = False
            self._refresh_job: str | None = None
            self._progress: ctk.CTkProgressBar | None = None

            self.protocol("WM_DELETE_WINDOW", self._on_close)
            self._build()
            self.after(200, self._safe_refresh)
            self._schedule_refresh()
            self._log("Unblock Helper готов. Установите движок и запустите обход.")

        def _alive(self) -> bool:
            return not self._closing and self.winfo_exists()

        def _on_close(self) -> None:
            self._closing = True
            if self._refresh_job:
                try:
                    self.after_cancel(self._refresh_job)
                except Exception:
                    pass
            self.destroy()

        def _build(self) -> None:
            top = ctk.CTkFrame(self, fg_color="transparent")
            top.pack(fill="x", padx=16, pady=(12, 4))
            ctk.CTkLabel(
                top, text="Unblock Helper", font=ctk.CTkFont(size=24, weight="bold"),
            ).pack(side="left")
            ctk.CTkLabel(top, text=f"v{APP_VERSION}", text_color="gray").pack(side="left", padx=8)
            self.dot = ctk.CTkLabel(top, text="●", font=ctk.CTkFont(size=18))
            self.dot.pack(side="right")
            self.lbl_status = ctk.CTkLabel(top, text="…")
            self.lbl_status.pack(side="right", padx=6)

            self.lbl_admin = ctk.CTkLabel(
                self,
                text="",
                font=ctk.CTkFont(size=12),
            )
            self.lbl_admin.pack(fill="x", padx=16)
            self._update_admin_banner()

            self.tabs = ctk.CTkTabview(self)
            self.tabs.pack(fill="both", expand=True, padx=12, pady=8)
            self.tabs.add("Обход")
            self.tabs.add("Discord")
            self.tabs.add("Сервисы")

            self._tab_bypass(self.tabs.tab("Обход"))
            self._tab_discord(self.tabs.tab("Discord"))
            self._tab_tools(self.tabs.tab("Сервисы"))

            self._progress = ctk.CTkProgressBar(self, mode="indeterminate")
            self._progress.pack(fill="x", padx=16, pady=(0, 4))
            self._progress.stop()
            self._progress.pack_forget()

            log_fr = ctk.CTkFrame(self, fg_color="transparent")
            log_fr.pack(fill="both", expand=True, padx=16, pady=(0, 12))
            ctk.CTkLabel(log_fr, text="Журнал", anchor="w").pack(fill="x")
            self.log = ctk.CTkTextbox(log_fr, height=120, font=ctk.CTkFont(family="Consolas", size=11))
            self.log.pack(fill="both", expand=True, pady=(4, 0))
            self.log.configure(state="disabled")

        def _update_admin_banner(self) -> None:
            if is_admin():
                self.lbl_admin.configure(
                    text="Права администратора: да",
                    text_color="#3fb950",
                )
            else:
                self.lbl_admin.configure(
                    text="Нет прав администратора — обход DPI недоступен.  [Перезапуск от админа]",
                    text_color="#f0883e",
                )

        def _tab_bypass(self, parent) -> None:
            ch = ctk.CTkFrame(parent, fg_color="transparent")
            ch.pack(fill="both", expand=True, padx=8, pady=8)

            ctk.CTkLabel(ch, text="Доступность", font=ctk.CTkFont(weight="bold")).pack(anchor="w")
            self.checks: dict[str, ctk.CTkLabel] = {}
            for name in ("YouTube", "Discord", "Discord API"):
                row = ctk.CTkFrame(ch, fg_color="transparent")
                row.pack(fill="x", pady=2)
                ctk.CTkLabel(row, text=name, width=110, anchor="w").pack(side="left")
                lb = ctk.CTkLabel(row, text="—", anchor="w")
                lb.pack(side="left", fill="x")
                self.checks[name] = lb

            ctk.CTkButton(ch, text="Проверить сайты", command=self._on_check).pack(fill="x", pady=(8, 12))

            ctk.CTkLabel(ch, text="Стратегия DPI", font=ctk.CTkFont(weight="bold")).pack(anchor="w")
            self.var_strategy = ctk.StringVar(value=get_strategy())
            self.cmb_strategy = ctk.CTkComboBox(
                ch, variable=self.var_strategy, values=self._strategies(), state="readonly",
            )
            self.cmb_strategy.pack(fill="x", pady=4)
            ctk.CTkButton(ch, text="Обновить список стратегий", command=self._reload_strategies).pack(
                fill="x", pady=(0, 10),
            )

            g = ctk.CTkFrame(ch, fg_color="transparent")
            g.pack(fill="x")
            g.columnconfigure((0, 1), weight=1)

            self.btn_install = ctk.CTkButton(g, text="Установить движок", command=self._on_install)
            self.btn_install.grid(row=0, column=0, padx=3, pady=3, sticky="ew")
            self.btn_reinstall = ctk.CTkButton(
                g, text="Переустановить", fg_color="#555", command=self._on_reinstall,
            )
            self.btn_reinstall.grid(row=0, column=1, padx=3, pady=3, sticky="ew")

            self.btn_start = ctk.CTkButton(
                g, text="Запустить обход", fg_color="#1a7f37", hover_color="#146c2e",
                command=self._on_start,
            )
            self.btn_start.grid(row=1, column=0, padx=3, pady=3, sticky="ew")
            self.btn_stop = ctk.CTkButton(
                g, text="Остановить", fg_color="#8b2e2e", hover_color="#6e2424",
                command=self._on_stop,
            )
            self.btn_stop.grid(row=1, column=1, padx=3, pady=3, sticky="ew")

            self.btn_auto = ctk.CTkButton(
                ch, text="Автоподбор стратегии (рекомендуется)", command=self._on_auto,
            )
            self.btn_auto.pack(fill="x", pady=(10, 0))

        def _tab_discord(self, parent) -> None:
            ch = ctk.CTkFrame(parent, fg_color="transparent")
            ch.pack(fill="both", expand=True, padx=8, pady=8)
            ctk.CTkLabel(
                ch,
                text="Если Discord завис на «Checking for updates…»:",
                wraplength=480,
                justify="left",
            ).pack(anchor="w", pady=(0, 8))
            ctk.CTkLabel(
                ch,
                text="1. Выключите VPN / WARP\n2. Нажмите «Исправить Discord»\n3. Закройте Discord полностью (трей → Quit)\n4. Откройте Discord снова",
                justify="left",
                text_color="gray",
            ).pack(anchor="w", pady=(0, 12))

            self.var_hosts = ctk.BooleanVar(value=False)
            ctk.CTkCheckBox(
                ch, text="Дополнительно: записи в hosts (редко нужно)", variable=self.var_hosts,
            ).pack(anchor="w", pady=4)

            ctk.CTkButton(
                ch, text="Исправить Discord", height=40, command=self._on_discord_fix,
            ).pack(fill="x", pady=8)
            ctk.CTkButton(
                ch, text="Скачать Discord", command=lambda: webbrowser.open("https://discord.com/download"),
            ).pack(fill="x", pady=4)

        def _tab_tools(self, parent) -> None:
            ch = ctk.CTkFrame(parent, fg_color="transparent")
            ch.pack(fill="both", expand=True, padx=8, pady=8)
            for label, url in (
                ("Открыть YouTube", "https://www.youtube.com"),
                ("Открыть Discord", "https://discord.com"),
            ):
                ctk.CTkButton(
                    ch, text=label, command=lambda u=url: webbrowser.open(u),
                ).pack(fill="x", pady=4)

            ctk.CTkButton(
                ch, text="Папка логов", command=lambda: _open_folder(LOG_DIR),
            ).pack(fill="x", pady=4)
            ctk.CTkButton(
                ch, text="Папка DPI-движка", command=lambda: _open_folder(ZAPRET_CACHE),
            ).pack(fill="x", pady=4)
            ctk.CTkButton(
                ch, text="Перезапуск от администратора", command=relaunch_as_admin,
            ).pack(fill="x", pady=4)
            ctk.CTkButton(
                ch, text="Завершить зависший процесс GUI", command=self._kill_stale,
            ).pack(fill="x", pady=4)

            ctk.CTkLabel(
                ch,
                text=status_text(),
                justify="left",
                font=ctk.CTkFont(family="Consolas", size=11),
                wraplength=500,
            ).pack(fill="x", pady=12)

        def _strategies(self) -> list[str]:
            root = get_bundle_root()
            return list_strategies(root) if root else [
                "general.bat", "general (ALT).bat", "general (ALT2).bat",
            ]

        def _reload_strategies(self) -> None:
            self.cmb_strategy.configure(values=self._strategies())
            self._log("Список стратегий обновлён.")

        def _log(self, msg: str) -> None:
            if not self._alive():
                return

            def append() -> None:
                if not self._alive():
                    return
                self.log.configure(state="normal")
                self.log.insert("end", msg.rstrip() + "\n")
                self.log.see("end")
                self.log.configure(state="disabled")

            try:
                self.after(0, append)
            except Exception:
                pass

        def _set_busy(self, on: bool) -> None:
            self._busy = on
            if not self._alive():
                return
            if on:
                self._progress.pack(fill="x", padx=16, pady=(0, 4), before=self.log.master)
                self._progress.start()
            else:
                self._progress.stop()
                self._progress.pack_forget()
            st = "disabled" if on else "normal"
            for w in (
                self.btn_install, self.btn_reinstall, self.btn_start,
                self.btn_stop, self.btn_auto, self.cmb_strategy,
            ):
                try:
                    w.configure(state=st)
                except Exception:
                    pass

        def _run_bg(self, fn, done=None) -> None:
            if self._busy:
                return
            self._set_busy(True)

            def work() -> None:
                try:
                    result = fn()
                except Exception as exc:  # noqa: BLE001
                    result = exc

                def finish() -> None:
                    if not self._alive():
                        return
                    self._set_busy(False)
                    if isinstance(result, Exception):
                        self._log(f"Ошибка: {result}")
                    elif done:
                        done(result)
                    self._safe_refresh()

                self.after(0, finish)

            threading.Thread(target=work, daemon=True).start()

        def _require_admin(self) -> bool:
            if is_admin():
                return True
            self._log("Нужны права администратора. Вкладка «Сервисы» → Перезапуск.")
            return False

        def _schedule_refresh(self) -> None:
            if self._alive():
                self._refresh_job = self.after(REFRESH_MS, self._schedule_refresh)
                self._safe_refresh()

        def _safe_refresh(self) -> None:
            if not self._alive():
                return
            try:
                running = is_winws_running()
                st = load_state()
                ver = st.get("version", "—")
                if running:
                    self.dot.configure(text_color="#3fb950")
                    self.lbl_status.configure(text=f"DPI активен · {ver}")
                elif get_bundle_root():
                    self.dot.configure(text_color="#d29922")
                    self.lbl_status.configure(text=f"Остановлен · {ver}")
                else:
                    self.dot.configure(text_color="#6e7681")
                    self.lbl_status.configure(text="Движок не установлен")
                act = st.get("active_strategy")
                if act:
                    self.var_strategy.set(act)
            except Exception as exc:
                _write_log(str(exc))

        def _set_checks(self, results: list[CheckResult]) -> None:
            for r in results:
                lb = self.checks.get(r.name)
                if not lb:
                    continue
                if r.ok:
                    lb.configure(
                        text=f"OK · {r.status} · {r.elapsed_ms:.0f} ms", text_color="#3fb950",
                    )
                else:
                    d = f"{r.status}" if r.status else (r.error or "?")[:50]
                    lb.configure(text=f"Недоступно · {d}", text_color="#f85149")

        def _on_check(self) -> None:
            self._log("Проверка…")
            self._run_bg(
                lambda: run_async(run_checks()),
                lambda res: (
                    self._set_checks(res),
                    self._log(f"Итого: {sum(1 for r in res if r.ok)}/{len(res)}"),
                ),
            )

        def _on_install(self) -> None:
            if not self._require_admin():
                return
            self._run_bg(
                lambda: dpi_install(force=False, log=self._log),
                lambda r: self._log(r[1]),
            )

        def _on_reinstall(self) -> None:
            if not self._require_admin():
                return
            self._run_bg(
                lambda: dpi_install(force=True, log=self._log),
                lambda r: (self._reload_strategies(), self._log(r[1])),
            )

        def _on_start(self) -> None:
            if not self._require_admin():
                return
            s = self.var_strategy.get()
            set_strategy(s)
            self._log(f"Запуск {s}")
            self._run_bg(
                lambda: dpi_start(s),
                lambda r: self._log(r[1]),
            )

        def _on_stop(self) -> None:
            self._run_bg(lambda: dpi_stop(), lambda r: self._log(r[1]))

        def _on_auto(self) -> None:
            if not self._require_admin():
                return
            self._log("Автоподбор…")

            def task():
                return auto_find(
                    lambda: all_ok(run_async(run_checks())),
                    log=self._log,
                )

            def done(res):
                ok, msg = res
                self._log(msg)
                if ok:
                    act = load_state().get("active_strategy")
                    if act:
                        set_strategy(act)
                        self.var_strategy.set(act)
                    self._on_check()

            self._run_bg(task, done)

        def _on_discord_fix(self) -> None:
            if not self._require_admin():
                return
            s = self.var_strategy.get()
            lines: list[str] = []

            def task():
                code = run_full_fix(
                    use_hosts=self.var_hosts.get(),
                    strategy=s,
                    log=lambda m: lines.append(m),
                )
                return code == 0, lines

            def done(res):
                ok, logs = res
                for ln in logs:
                    self._log(ln)
                self._log("Готово." if ok else "Не удалось — попробуйте автоподбор.")

            self._run_bg(task, done)

        def _kill_stale(self) -> None:
            from desktop.instance import release_stale

            release_stale(force=True)
            self._log("Зависшие процессы завершены. Можно перезапустить приложение.")

    try:
        UnblockApp().mainloop()
    except Exception:
        _show_fatal(traceback.format_exc())


if __name__ == "__main__":
    main()
