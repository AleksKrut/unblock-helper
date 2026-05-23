#!/usr/bin/env python3
"""Unblock Helper — десктоп-приложение (Windows)."""

from __future__ import annotations

import asyncio
import json
import sys
import threading
from pathlib import Path

# Корень проекта (unblock-helper/)
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import customtkinter as ctk  # noqa: E402

from checker import CheckResult, all_ok, run_checks  # noqa: E402
from discord_fix import run_full_fix  # noqa: E402
from dpi import (  # noqa: E402
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

CONFIG_PATH = ROOT / "config.json"
CONFIG_EXAMPLE = ROOT / "config.example.json"


def load_config() -> dict:
    if CONFIG_PATH.is_file():
        with CONFIG_PATH.open(encoding="utf-8") as f:
            return json.load(f)
    if CONFIG_EXAMPLE.is_file():
        with CONFIG_EXAMPLE.open(encoding="utf-8") as f:
            return json.load(f)
    return {"dpi_strategy": "general (ALT).bat"}


def save_strategy(name: str) -> None:
    cfg = load_config()
    cfg["dpi_strategy"] = name
    with CONFIG_PATH.open("w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


def run_async(coro):
    return asyncio.run(coro)


def relaunch_as_admin() -> None:
    import ctypes

    script = Path(__file__).resolve()
    params = f'"{script}"'
    ctypes.windll.shell32.ShellExecuteW(
        None, "runas", sys.executable, params, str(ROOT), 1
    )
    sys.exit(0)


class UnblockApp(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Unblock Helper")
        self.geometry("520x640")
        self.minsize(480, 580)

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self._busy = False
        self._build_ui()
        self.after(300, self._refresh_status)
        self._schedule_refresh()

    def _build_ui(self) -> None:
        pad = {"padx": 16, "pady": 6}

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", **pad)
        ctk.CTkLabel(
            header,
            text="Unblock Helper",
            font=ctk.CTkFont(size=22, weight="bold"),
        ).pack(side="left")
        self.status_dot = ctk.CTkLabel(header, text="●", font=ctk.CTkFont(size=20))
        self.status_dot.pack(side="right", padx=4)
        self.status_label = ctk.CTkLabel(header, text="...")
        self.status_label.pack(side="right")

        if not is_admin():
            warn = ctk.CTkFrame(self, fg_color="#5c3d1e", corner_radius=8)
            warn.pack(fill="x", padx=16, pady=(0, 8))
            ctk.CTkLabel(
                warn,
                text="Нужны права администратора для обхода DPI",
                wraplength=460,
            ).pack(side="left", padx=12, pady=10)
            ctk.CTkButton(
                warn,
                text="Перезапуск",
                width=100,
                command=relaunch_as_admin,
            ).pack(side="right", padx=12, pady=8)

        # Карточки проверки
        checks = ctk.CTkFrame(self)
        checks.pack(fill="x", **pad)
        ctk.CTkLabel(checks, text="Доступность", font=ctk.CTkFont(weight="bold")).pack(
            anchor="w", padx=12, pady=(10, 4)
        )
        self.check_labels: dict[str, ctk.CTkLabel] = {}
        for name in ("YouTube", "Discord", "Discord API"):
            row = ctk.CTkFrame(checks, fg_color="transparent")
            row.pack(fill="x", padx=12, pady=2)
            ctk.CTkLabel(row, text=name, width=120, anchor="w").pack(side="left")
            lbl = ctk.CTkLabel(row, text="—", anchor="w")
            lbl.pack(side="left", fill="x", expand=True)
            self.check_labels[name] = lbl
        ctk.CTkButton(
            checks,
            text="Проверить сайты",
            command=self._on_check,
        ).pack(fill="x", padx=12, pady=(8, 12))

        # Стратегия
        strat = ctk.CTkFrame(self)
        strat.pack(fill="x", **pad)
        ctk.CTkLabel(strat, text="Стратегия DPI", font=ctk.CTkFont(weight="bold")).pack(
            anchor="w", padx=12, pady=(10, 4)
        )
        self.strategy_var = ctk.StringVar(value=load_config().get("dpi_strategy", "general.bat"))
        self.strategy_menu = ctk.CTkComboBox(
            strat,
            variable=self.strategy_var,
            values=self._strategy_values(),
            state="readonly",
        )
        self.strategy_menu.pack(fill="x", padx=12, pady=(0, 12))

        # Кнопки управления
        btns = ctk.CTkFrame(self, fg_color="transparent")
        btns.pack(fill="x", padx=16, pady=4)
        btns.columnconfigure((0, 1), weight=1)

        self.btn_install = ctk.CTkButton(
            btns, text="Установить движок", command=self._on_install
        )
        self.btn_install.grid(row=0, column=0, padx=4, pady=4, sticky="ew")

        self.btn_start = ctk.CTkButton(
            btns,
            text="Запустить обход",
            fg_color="#1a7f37",
            hover_color="#146c2e",
            command=self._on_start,
        )
        self.btn_start.grid(row=0, column=1, padx=4, pady=4, sticky="ew")

        self.btn_stop = ctk.CTkButton(
            btns,
            text="Остановить",
            fg_color="#8b2e2e",
            hover_color="#6e2424",
            command=self._on_stop,
        )
        self.btn_stop.grid(row=1, column=0, padx=4, pady=4, sticky="ew")

        self.btn_auto = ctk.CTkButton(
            btns, text="Автоподбор", command=self._on_auto
        )
        self.btn_auto.grid(row=1, column=1, padx=4, pady=4, sticky="ew")

        ctk.CTkButton(
            self,
            text="Исправить Discord (Checking for updates…)",
            command=self._on_discord_fix,
        ).pack(fill="x", padx=16, pady=8)

        # Лог
        ctk.CTkLabel(self, text="Журнал", anchor="w").pack(fill="x", padx=16, pady=(8, 0))
        self.log = ctk.CTkTextbox(self, height=160, font=ctk.CTkFont(family="Consolas", size=12))
        self.log.pack(fill="both", expand=True, padx=16, pady=(4, 16))
        self.log.configure(state="disabled")

        self._log("Готово. Установите движок и запустите обход.")

    def _strategy_values(self) -> list[str]:
        root = get_bundle_root()
        if root:
            vals = list_strategies(root)
            if vals:
                return vals
        return ["general.bat", "general (ALT).bat", "general (ALT2).bat"]

    def _log(self, msg: str) -> None:
        def append() -> None:
            self.log.configure(state="normal")
            self.log.insert("end", msg.rstrip() + "\n")
            self.log.see("end")
            self.log.configure(state="disabled")

        self.after(0, append)

    def _set_busy(self, busy: bool) -> None:
        self._busy = busy
        state = "disabled" if busy else "normal"
        for w in (
            self.btn_install,
            self.btn_start,
            self.btn_stop,
            self.btn_auto,
            self.strategy_menu,
        ):
            w.configure(state=state)

    def _run_bg(self, fn, on_done=None) -> None:
        if self._busy:
            return
        self._set_busy(True)

        def work() -> None:
            try:
                result = fn()
            except Exception as exc:  # noqa: BLE001
                result = exc
            self.after(0, lambda: self._done_bg(result, on_done))

        threading.Thread(target=work, daemon=True).start()

    def _done_bg(self, result, on_done) -> None:
        self._set_busy(False)
        if isinstance(result, Exception):
            self._log(f"Ошибка: {result}")
        elif on_done:
            on_done(result)
        self._refresh_status()

    def _schedule_refresh(self) -> None:
        self._refresh_status()
        self.after(4000, self._schedule_refresh)

    def _refresh_status(self) -> None:
        running = is_winws_running()
        state = load_state()
        ver = state.get("version", "—")
        strat = state.get("active_strategy") or "—"

        if running:
            self.status_dot.configure(text_color="#3fb950")
            self.status_label.configure(text=f"DPI активен · v{ver}")
        elif get_bundle_root():
            self.status_dot.configure(text_color="#d29922")
            self.status_label.configure(text=f"Остановлен · v{ver}")
        else:
            self.status_dot.configure(text_color="#8b949e")
            self.status_label.configure(text="Движок не установлен")

        if strat != "—":
            self.strategy_var.set(strat)

        vals = self._strategy_values()
        self.strategy_menu.configure(values=vals)

    def _update_checks(self, results: list[CheckResult]) -> None:
        for r in results:
            lbl = self.check_labels.get(r.name)
            if not lbl:
                continue
            if r.ok:
                lbl.configure(text=f"OK · HTTP {r.status} · {r.elapsed_ms:.0f} ms", text_color="#3fb950")
            else:
                detail = f"HTTP {r.status}" if r.status else (r.error or "ошибка")[:60]
                lbl.configure(text=f"Нет доступа · {detail}", text_color="#f85149")

    def _on_check(self) -> None:
        self._log("Проверка YouTube / Discord...")
        self._run_bg(
            lambda: run_async(run_checks()),
            on_done=lambda res: (
                self._update_checks(res),
                self._log(
                    f"Итого: {sum(1 for r in res if r.ok)}/{len(res)} доступны"
                ),
            ),
        )

    def _on_install(self) -> None:
        if not is_admin():
            self._log("Запустите приложение от администратора.")
            return
        self._log("Загрузка zapret-discord-youtube...")
        self._run_bg(
            lambda: dpi_install(force=False),
            on_done=lambda r: self._log(r[1]),
        )

    def _on_start(self) -> None:
        if not is_admin():
            self._log("Нужны права администратора.")
            return
        strat = self.strategy_var.get()
        save_strategy(strat)
        self._log(f"Запуск: {strat}")
        self._run_bg(
            lambda: dpi_start(strat),
            on_done=lambda r: self._log(r[1]),
        )

    def _on_stop(self) -> None:
        self._run_bg(
            lambda: dpi_stop(),
            on_done=lambda r: self._log(r[1]),
        )

    def _on_auto(self) -> None:
        if not is_admin():
            self._log("Нужны права администратора.")
            return
        self._log("Автоподбор стратегии (может занять несколько минут)...")

        def task():
            ok, msg = auto_find(lambda: all_ok(run_async(run_checks())))
            return ok, msg

        def done(result):
            ok, msg = result
            self._log(msg)
            if ok:
                st = load_state()
                if st.get("active_strategy"):
                    self.strategy_var.set(st["active_strategy"])
                    save_strategy(st["active_strategy"])
                self._on_check()

        self._run_bg(task, on_done=done)

    def _on_discord_fix(self) -> None:
        if not is_admin():
            self._log("Нужны права администратора.")
            return
        self._log("Исправление Discord...")
        strat = self.strategy_var.get()

        logs: list[str] = []

        def task():
            code = run_full_fix(
                use_hosts=False,
                strategy=strat,
                log=lambda m: logs.append(m),
            )
            return code == 0, logs

        def done(result):
            ok, lines = result
            for line in lines:
                self._log(line)
            self._log("Discord Fix завершён." if ok else "Discord Fix не удался.")

        self._run_bg(task, on_done=done)


def main() -> None:
    app = UnblockApp()
    app.mainloop()


if __name__ == "__main__":
    main()
