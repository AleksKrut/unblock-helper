# Unblock Helper

**Unblock Helper** — бесплатная утилита для Windows, которая помогает открывать **YouTube** и **Discord** при блокировках на уровне провайдера (DPI). Работает **без VPN**: трафик идёт напрямую, а специальный локальный движок обходит фильтрацию пакетов — по тому же принципу, что и [zapret](https://github.com/bol-van/zapret) / [zapret-discord-youtube](https://github.com/Flowseal/zapret-discord-youtube).

Есть **графический интерфейс**, **командная строка** и готовая **сборка EXE** (Python на целевом ПК не обязателен).

---

## Содержание

- [Как это работает](#как-это-работает)
- [Возможности](#возможности)
- [Требования](#требования)
- [Установка](#установка)
- [Быстрый старт](#быстрый-старт)
- [Графический интерфейс](#графический-интерфейс)
- [UnblockHelper.bat — единый launcher](#unblockhelperbat--единый-launcher)
- [Командная строка (CLI)](#командная-строка-cli)
- [Настройка config.json](#настройка-configjson)
- [Сборка EXE из исходников](#сборка-exe-из-исходников)
- [Структура проекта](#структура-проекта)
- [Решение проблем](#решение-проблем)
- [Частые вопросы](#частые-вопросы)
- [Сторонний код и лицензия](#сторонний-код-и-лицензия)
- [Отказ от ответственности](#отказ-от-ответственности)

---

## Как это работает

1. **Unblock Helper** скачивает официальную сборку [zapret-discord-youtube](https://github.com/Flowseal/zapret-discord-youtube) (файл `winws.exe` + списки доменов + стратегии `general*.bat`).
2. При запуске обхода `winws.exe` через драйвер **WinDivert** перехватывает и модифицирует сетевые пакеты так, чтобы DPI провайдера не распознал соединения с YouTube, Discord и связанными CDN.
3. Браузер и десктопный Discord ходят **без прокси и без VPN** — обход только для нужных доменов.

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────┐
│  Браузер /  │ ──► │  winws.exe       │ ──► │  Интернет   │
│  Discord    │     │  (локально, DPI) │     │  (провайдер)│
└─────────────┘     └──────────────────┘     └─────────────┘
```

> Unblock Helper **не пишет** DPI-движок с нуля — он устанавливает, настраивает и управляет проверенным open-source компонентом.

---

## Возможности

| Функция | Описание |
|---------|----------|
| **Установка движка** | Автозагрузка последнего релиза zapret с GitHub (~1.4 MB) |
| **Запуск / остановка** | Включение и выключение обхода одной кнопкой |
| **Автоподбор стратегии** | Перебор `general.bat`, `ALT`, `FAKE TLS` и др. под вашего провайдера |
| **Проверка сайтов** | Тест доступности YouTube, Discord и API |
| **Discord Fix** | Домены обновлений, очистка кэша, перезапуск DPI при зависании на «Checking for updates…» |
| **GUI** | Вкладки «Обход», «Discord», «Сервисы», журнал операций |
| **EXE** | Портативная сборка без установки Python |

---

## Требования

| | |
|---|---|
| **ОС** | Windows 10 или Windows 11 (64-bit) |
| **Права** | **Администратор** (обязательно для WinDivert) |
| **Python** | 3.10+ — только если запускаете из исходников, не из EXE |
| **Интернет** | Нужен при первой установке движка |
| **Свободное место** | ~50 MB (приложение + `zapret-cache`) |

**Рекомендации:**

- Перед использованием **отключите VPN, Cloudflare WARP** и аналоги — они часто конфликтуют с zapret.
- Добавьте папку `zapret-cache` (или `dist\UnblockHelper`) в **исключения антивируса** — `winws.exe` использует перехват пакетов и может давать ложное срабатывание ([пояснение разработчика zapret](https://github.com/bol-van/zapret/issues/393)).

---

## Установка

### Вариант A — готовый EXE (проще)

1. Скачайте репозиторий или релиз с GitHub.
2. Соберите EXE (один раз) или возьмите готовую папку:
   ```
   dist\UnblockHelper\
   ```
3. Скопируйте **всю папку** `UnblockHelper` на флешку или другой ПК.
4. Запустите **`UnblockHelper.exe`** от имени администратора (ПКМ → «Запуск от имени администратора»).

### Вариант B — из исходников (для разработки)

```powershell
git clone https://github.com/YOUR_USERNAME/unblock-helper.git
cd unblock-helper

py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Запуск:

```powershell
.\UnblockHelper.bat
```

или

```powershell
.\.venv\Scripts\python desktop\app.py
```

---

## Быстрый старт

### За 3 шага

1. Запустите **`UnblockHelper.bat`** (или `UnblockHelper.exe`) → в окне UAC нажмите **«Да»**.
2. Во вкладке **«Обход»**:
   - **Установить движок** (при первом запуске);
   - **Запустить обход**;
   - **Проверить сайты** — все три строки должны стать зелёными (OK).
3. Откройте [youtube.com](https://www.youtube.com) и [discord.com](https://discord.com) или десктопный Discord.

### Если не работает с первого раза

1. Нажмите **«Автоподбор стратегии»** (может занять 5–15 минут).
2. Или вручную выберите другую стратегию, например `general (ALT).bat`, и снова **«Запустить обход»**.
3. Для Discord: вкладка **«Discord»** → **«Исправить Discord»**.

---

## Графический интерфейс

После запуска открывается окно с тремя вкладками.

### Вкладка «Обход»

| Элемент | Назначение |
|---------|------------|
| **Индикатор вверху** | Зелёный — DPI активен; жёлтый — остановлен; серый — движок не установлен |
| **Доступность** | Статус YouTube, Discord, Discord API |
| **Проверить сайты** | HTTP-проверка без браузера |
| **Стратегия DPI** | Выбор `general.bat` / `ALT` / … (зависит от провайдера) |
| **Установить движок** | Первая установка zapret с GitHub |
| **Переустановить** | Полная переустановка (если файлы повреждены или обновился релиз) |
| **Запустить обход** | Старт `winws.exe` с выбранной стратегией |
| **Остановить** | Завершение `winws.exe` |
| **Автоподбор стратегии** | Перебор всех стратегий до успешной проверки |
| **Журнал** | Лог операций внизу окна |

### Вкладка «Discord»

Используйте, если десктопный Discord **зависает на «Checking for updates…»**:

1. Выключите VPN / WARP.
2. Нажмите **«Исправить Discord»**.
3. Полностью закройте Discord (иконка в трее → **Quit Discord**).
4. Снова откройте Discord из меню «Пуск».

Опция **«Записи в hosts»** — дополнительный обход через файл `hosts` (редко нужен).

Кнопка **«Скачать Discord»** открывает официальный установщик.

### Вкладка «Сервисы»

| Кнопка | Действие |
|--------|----------|
| Открыть YouTube / Discord | Ссылки в браузере (при активном обходе) |
| Папка логов | `logs\desktop.log` |
| Папка DPI-движка | `zapret-cache\` |
| Перезапуск от администратора | Повторный запуск с UAC |
| Завершить зависший процесс GUI | Если приложение не открывается повторно |

---

## UnblockHelper.bat — единый launcher

В корне проекта один файл **`UnblockHelper.bat`** заменяет все старые bat-скрипты.

| Команда | Что делает |
|---------|------------|
| `UnblockHelper.bat` | Запуск GUI (EXE, если собран, иначе Python) |
| `UnblockHelper.bat build` | Сборка `dist\UnblockHelper\UnblockHelper.exe` |
| `UnblockHelper.bat cli <команда>` | CLI (см. ниже) |
| `UnblockHelper.bat kill` | Завершить зависший `UnblockHelper.exe` / python |

При запуске без аргументов bat-файл **запрашивает права администратора** (UAC).

**Приоритет запуска:**

1. Если есть `dist\UnblockHelper\UnblockHelper.exe` → запускается EXE.
2. Иначе → Python из `.venv` и `desktop\app.py`.

---

## Командная строка (CLI)

Для автоматизации и скриптов:

```powershell
# Проверка доступности
UnblockHelper.bat cli check

# Установка / обновление движка
UnblockHelper.bat cli dpi-install
UnblockHelper.bat cli dpi-install --force

# Запуск и остановка (нужен админ)
UnblockHelper.bat cli dpi-start --admin
UnblockHelper.bat cli dpi-start --strategy "general (ALT).bat" --admin
UnblockHelper.bat cli dpi-stop

# Статус и список стратегий
UnblockHelper.bat cli dpi-status
UnblockHelper.bat cli dpi-list

# Автоподбор
UnblockHelper.bat cli dpi-auto --admin

# Исправление Discord
UnblockHelper.bat cli discord-fix --admin
UnblockHelper.bat cli discord-fix --admin --hosts
```

Из активированного venv то же самое:

```powershell
python main.py check
python main.py dpi-install
python main.py dpi-start --admin
```

---

## Настройка config.json

При первом сохранении стратегии создаётся файл `config.json` (рядом с EXE или в корне репозитория).

Пример (можно скопировать из `config.example.json`):

```json
{
  "dpi_strategy": "general (ALT).bat"
}
```

| Поле | Описание |
|------|----------|
| `dpi_strategy` | Имя bat-файла стратегии из `zapret-cache` |

После **автоподбора** рабочая стратегия также сохраняется в `zapret-state.json`.

---

## Сборка EXE из исходников

```powershell
cd unblock-helper
UnblockHelper.bat build
```

Или вручную:

```powershell
pip install -r requirements.txt pyinstaller
python build.py
```

**Результат:**

```
dist\UnblockHelper\
├── UnblockHelper.exe      ← запускать от администратора
├── _internal\               ← библиотеки (не удалять)
├── config.example.json
├── КАК_ЗАПУСТИТЬ.txt
├── zapret-cache\            ← создаётся после «Установить движок»
├── zapret-state.json
├── config.json
└── logs\
```

Для распространения отдайте пользователям **всю папку** `UnblockHelper`, не только exe-файл.

Пересборка после изменений в коде:

```powershell
UnblockHelper.bat build
```

---

## Структура проекта

```
unblock-helper/
├── UnblockHelper.bat          # Единый launcher
├── desktop/
│   ├── app.py                 # GUI (CustomTkinter)
│   └── instance.py            # Один экземпляр, сброс зависших процессов
├── main.py                    # CLI
├── dpi.py                     # Загрузка и управление zapret
├── checker.py                 # Проверка YouTube / Discord
├── discord_fix.py             # Исправление Discord
├── app_paths.py               # Пути (исходники / EXE)
├── config_store.py            # config.json
├── build.py                   # PyInstaller
├── data/
│   └── discord-hosts.txt      # Домены для Discord Fix
├── config.example.json
├── requirements.txt
├── LICENSE                    # MIT (обёртка)
├── README.md
│
├── zapret-cache/              # Создаётся локально, не в git
├── zapret-state.json
├── config.json
├── logs/
├── build/                     # Артефакты PyInstaller
└── dist/
    └── UnblockHelper/         # Готовая сборка
```

---

## Решение проблем

### Приложение не открывается повторно после закрытия

```powershell
UnblockHelper.bat kill
```

Затем снова `UnblockHelper.bat`.  
Или: вкладка **«Сервисы»** → **«Завершить зависший процесс GUI»**.

---

### «Нужны права администратора»

- Запускайте через **`UnblockHelper.bat`** и подтверждайте UAC.
- Для EXE: ПКМ на `UnblockHelper.exe` → **Запуск от имени администратора**.

---

### YouTube / Discord не открываются, проверка FAIL

1. Убедитесь, что индикатор **«DPI активен»** (зелёный).
2. Запустите **«Автоподбор стратегии»**.
3. Отключите VPN / WARP / GoodbyeDPI / другой zapret.
4. **Переустановите** движок.
5. Проверьте, что антивирус не удалил `zapret-cache\bin\winws.exe`.

---

### Discord: «Checking for updates…» бесконечно

1. Вкладка **«Discord»** → **«Исправить Discord»**.
2. Полностью закройте Discord (трей → Quit).
3. Обход должен быть **запущен** во время открытия Discord.
4. При необходимости — **автоподбор** другой стратегии.

---

### Антивирус удаляет winws.exe

Добавьте в исключения:

- `zapret-cache\` (рядом с bat/exe)
- или `dist\UnblockHelper\zapret-cache\`

Подробнее: [issue #393 (bol-van/zapret)](https://github.com/bol-van/zapret/issues/393).

---

### Ошибка при установке движка / нет winws.exe

```powershell
UnblockHelper.bat cli dpi-install --force
```

Проверьте интернет и доступ к GitHub. Если GitHub заблокирован — скачайте [zapret-discord-youtube](https://github.com/Flowseal/zapret-discord-youtube/releases) вручную и распакуйте в `zapret-cache`.

---

### Логи

| Файл | Содержимое |
|------|------------|
| `logs\desktop.log` | Ошибки GUI |
| Журнал в окне | Операции в реальном времени |

---

## Частые вопросы

**Нужен ли VPN?**  
Нет. Unblock Helper рассчитан на работу **без VPN**.

**Работает ли на macOS / Linux?**  
Нет, только **Windows** (WinDivert).

**Можно ли оставить обход включённым постоянно?**  
Да. Пока работает `winws.exe`, обход активен. Остановка — кнопка **«Остановить»** или закрытие через диспетчер задач.

**Замедляет ли интернет?**  
Обычно нет заметного влияния на весь трафик — обрабатываются только выбранные домены/IP по правилам zapret.

**Это легально?**  
Зависит от законодательства вашей страны. Используйте на свой страх и риск и в соответствии с местными законами.

**Чем отличается от zapret-discord-youtube?**  
Unblock Helper — **обёртка**: установка, GUI, автоподбор, проверка сайтов, Discord Fix. Ядро обхода — тот же `winws.exe`.

---

## Сторонний код и лицензия

| Компонент | Репозиторий | Роль |
|-----------|-------------|------|
| **zapret-discord-youtube** | [Flowseal/zapret-discord-youtube](https://github.com/Flowseal/zapret-discord-youtube) | DPI-движок, списки, стратегии (скачивается при установке) |
| **zapret** | [bol-van/zapret](https://github.com/bol-van/zapret) | winws, WinDivert |
| **CustomTkinter** | [TomSchimansky/CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) | Интерфейс |
| **httpx** | [encode/httpx](https://github.com/encode/httpx) | Проверка сайтов |

Код **Unblock Helper** (Python-обёртка) распространяется под лицензией **[MIT](LICENSE)**.

---

## Отказ от ответственности

Проект предназначен для восстановления доступа к сервисам в условиях сетевых ограничений. Авторы **не несут ответственности** за неправомерное использование. Соблюдайте законы вашей страны и правила сервисов (YouTube, Discord).

---

## Связь и вклад

- **Issues** — баги и предложения на GitHub  
- **Pull requests** — приветствуются улучшения GUI, документации, совместимости с провайдерами  

Если проект помог — поставьте звезду на GitHub.
