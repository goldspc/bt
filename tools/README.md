# tools/ — вспомогательные скрипты

Это необязательная часть проекта: LAN-клиенты на Tkinter, старая панель ГМа,
симулятор матчей, турнирный прогон и UI-демо. Для веб-версии (той, что
запускают игроки и друзья) они не нужны — см. [`../game/`](../game/).

```
tools/
├── _bootstrap.py          # общий sys.path-хук (добавляет ../game/ в path)
├── client_player_fixed.py # Tkinter-клиент для LAN-сервера
├── game_master_gui.py     # Tkinter-панель мастера (LAN-режим, legacy)
├── simulate_game.py       # headless-симулятор одного матча
├── run_tournament.py      # прогоняет серию симуляций, пишет summary.md
├── demo_ui.py             # демо-рендер UI-компонентов клиента
└── ui_theme.py            # единая Tkinter-тема для клиентов выше
```

## Зависимости

Tkinter уже идёт в стандартной поставке Python для Windows / macOS. На Linux
может потребоваться `sudo apt install python3-tk`.

## Запуск

Скрипты рассчитаны на запуск **из корня репозитория** (`bt/`) или напрямую
из папки `tools/`. `_bootstrap.py` сам добавляет `../game/` в `sys.path`, так
что импорты `shared_simple`, `protocol`, `server_full_visibility` работают
без `pip install`.

### LAN-версия (старый Tkinter-стек)

Это отдельный, не webовый контур игры. Его удобно запускать, когда все
сидят в одной Wi-Fi или Radmin VPN.

1. Запусти сервер (TCP):

   ```bash
   cd game
   python server_full_visibility.py        # по умолчанию 0.0.0.0:5000
   ```

2. На каждой клиентской машине:

   ```bash
   cd tools
   python client_player_fixed.py
   ```

   В окне подключения введи IP хоста и порт `5000`.

3. Мастер игры — на любой машине в сети:

   ```bash
   python tools/game_master_gui.py
   ```

### Симулятор

```bash
python tools/simulate_game.py
```

Логи матча складываются в `game_logs/` рядом с запуском.

### Турнир (N партий подряд)

```bash
python tools/run_tournament.py --games 20 --mode advanced --max-turns 30
```

Сводка — `game_logs/summary.md`.

### UI-демо без сервера

```bash
python tools/demo_ui.py map
```

Полезно для валидации вида карты без поднятого сервера.
