# Unblock Helper

**Обход блокировок YouTube и Discord на Windows** — без VPN, через DPI (как [zapret](https://github.com/Flowseal/zapret-discord-youtube)).

Утилита скачивает движок [zapret-discord-youtube](https://github.com/Flowseal/zapret-discord-youtube), запускает обход, подбирает стратегию и помогает с зависанием Discord на «Checking for updates…».

---

## Возможности

- Автоматическая установка DPI-движка с GitHub
- Запуск / остановка обхода одной командой
- Автоподбор стратегии под вашего провайдера
- Проверка доступности YouTube и Discord
- **Discord Fix** — домены обновлений, очистка кэша, перезапуск DPI

## Требования

- Windows 10 / 11
- Python 3.10+
- Права **администратора** (WinDivert)

## Быстрый старт

1. Клонируйте репозиторий и откройте папку в терминале.
2. Запустите **`start-dpi.bat`** → в UAC нажмите «Да».
3. При первом запуске скачается движок (~1.4 MB).
4. Откройте YouTube и Discord в браузере или десктоп-клиенте.

| Файл | Назначение |
|------|------------|
| `start-dpi.bat` | Запуск обхода |
| `start-dpi-auto.bat` | Автоподбор стратегии |
| `fix-discord.bat` | Discord завис на обновлениях |
| `start.bat` | Интерактивное меню |

Если не работает — **`start-dpi-auto.bat`**.

## Установка вручную

```powershell
git clone https://github.com/YOUR_USERNAME/unblock-helper.git
cd unblock-helper

py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

python main.py dpi-install
python main.py dpi-start --admin
python main.py check
```

Скопируйте `config.example.json` → `config.json` и при необходимости укажите стратегию:

```json
{
  "dpi_strategy": "general (ALT).bat"
}
```

## Команды CLI

| Команда | Описание |
|---------|----------|
| `python main.py dpi-install` | Скачать / обновить движок |
| `python main.py dpi-start --admin` | Запустить обход |
| `python main.py dpi-stop` | Остановить |
| `python main.py dpi-auto --admin` | Подобрать стратегию |
| `python main.py dpi-list` | Список `general*.bat` |
| `python main.py check` | Проверка сайтов |
| `python main.py discord-fix --admin` | Исправить Discord |

## Discord завис на «Checking for updates…»

1. Выключите VPN / WARP (мешают zapret).
2. Запустите **`fix-discord.bat`** от администратора.
3. Полностью закройте Discord (трей → Quit) и откройте снова.

## Структура проекта

```
unblock-helper/
├── main.py              # CLI и меню
├── dpi.py               # Загрузка и управление zapret
├── checker.py           # Проверка YouTube / Discord
├── discord_fix.py       # Исправление Discord
├── data/
│   └── discord-hosts.txt
├── start-dpi.bat
├── start-dpi-auto.bat
├── fix-discord.bat
└── config.example.json
```

Папки **`zapret-cache/`** и **`.venv/`** создаются локально и в git не попадают.

## Антивирус

`winws.exe` использует [WinDivert](https://github.com/bol-van/zapret/issues/393) для перехвата пакетов — некоторые антивирусы дают ложное срабатывание. Добавьте папку `zapret-cache` в исключения.

## Сторонний код

| Проект | Лицензия | Роль |
|--------|----------|------|
| [Flowseal/zapret-discord-youtube](https://github.com/Flowseal/zapret-discord-youtube) | см. репозиторий | DPI-движок, скачивается при установке |
| [bol-van/zapret](https://github.com/bol-van/zapret) | см. репозиторий | winws, WinDivert |

Код **Unblock Helper** (Python-обёртка) — [MIT](LICENSE).

## Отказ от ответственности

Используйте в соответствии с законодательством вашей страны. Авторы не несут ответственности за неправомерное использование.

## Лицензия

MIT — см. [LICENSE](LICENSE).
