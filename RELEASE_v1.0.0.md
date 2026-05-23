# v1.0.0 — Первый релиз

**Unblock Helper** — обход блокировок **YouTube** и **Discord** на Windows через DPI ([zapret](https://github.com/Flowseal/zapret-discord-youtube)). Без VPN: локальный обход на уровне провайдера.

---

## Что нового

### Десктоп-приложение
- GUI на **CustomTkinter** (`start-desktop.bat`)
- Установка движка, запуск/остановка обхода, выбор стратегии
- Проверка доступности YouTube и Discord в один клик
- Автоподбор рабочей стратегии под вашего провайдера
- **Discord Fix** — если клиент завис на «Checking for updates…»

### Командная строка
- CLI: `main.py` с командами `dpi-install`, `dpi-start`, `dpi-stop`, `dpi-auto`, `check`, `discord-fix`
- Bat-файлы для быстрого запуска без знания Python

### Ядро
- Автозагрузка [zapret-discord-youtube](https://github.com/Flowseal/zapret-discord-youtube) с GitHub Releases
- Управление 19+ стратегиями (`general.bat`, `ALT`, `FAKE TLS`, …)
- Дополнительные домены Discord CDN для обновлений (`updates.discord.com`, `dl.discordapp.net`, …)

---

## Быстрый старт

1. Скачайте архив **Source code (zip)** или клонируйте репозиторий.
2. Установите [Python 3.10+](https://www.python.org/downloads/).
3. Запустите **`start-desktop.bat`** → в UAC нажмите **«Да»**.
4. **Установить движок** → **Запустить обход** → **Проверить сайты**.

Альтернатива без GUI: **`start-dpi.bat`**.

---

## Требования

| | |
|---|---|
| ОС | Windows 10 / 11 |
| Python | 3.10+ |
| Права | Администратор (WinDivert) |
| Интернет | Для первой установки движка (~1.4 MB) |

---

## Состав релиза

```
unblock-helper/
├── desktop/app.py          # GUI
├── main.py, dpi.py         # CLI и DPI-движок
├── checker.py              # Проверка сайтов
├── discord_fix.py          # Исправление Discord
├── start-desktop.bat       # Запуск GUI
├── start-dpi.bat           # Запуск обхода
├── start-dpi-auto.bat      # Автоподбор
├── fix-discord.bat         # Discord Fix
└── requirements-desktop.txt
```

> Папки `zapret-cache/` и `.venv/` создаются при первом запуске и в репозиторий не входят.

---

## Известные ограничения

- Работает **только на Windows** (WinDivert / winws).
- Одновременно с **VPN / WARP** может конфликтовать — отключите их перед использованием.
- Антивирус может ругаться на `winws.exe` — добавьте `zapret-cache` в исключения ([пояснение zapret](https://github.com/bol-van/zapret/issues/393)).
- На разных провайдерах нужны разные стратегии — используйте **Автоподбор**, если `general.bat` не помогает.

---

## Сторонний код

DPI-движок скачивается отдельно при установке:

- [Flowseal/zapret-discord-youtube](https://github.com/Flowseal/zapret-discord-youtube)
- [bol-van/zapret](https://github.com/bol-van/zapret)

Обёртка Unblock Helper — **MIT**.

---

## Отказ от ответственности

Используйте в соответствии с законодательством вашей страны. Проект предназначен для восстановления доступа к сервисам в условиях сетевых ограничений; авторы не несут ответственности за неправомерное использование.

---

**Полная документация:** [README.md](README.md)
