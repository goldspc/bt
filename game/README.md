# game/ — веб-версия «Космический бой 10×10×10»

Здесь лежит всё, что нужно, чтобы поднять игровой сервер и пустить игроков.

```
game/
├── app/                       # FastAPI-приложение
│   ├── main.py                # точка входа (uvicorn app.main:app)
│   ├── auth.py                # сессия ГМа (cookie + пароль)
│   ├── state.py               # игры, команды, игроки (в памяти)
│   ├── engine.py              # обёртка над GameServer без TCP
│   ├── views.py               # роль-зависимая сериализация состояния
│   ├── ws.py                  # реестр WebSocket-сокетов
│   └── routes/
│       ├── admin.py           # HTTP/WS для мастера игры
│       └── play.py            # HTTP/WS для игрока
├── static/                    # фронтенд
│   ├── admin/                 # SPA мастера игры (/admin)
│   ├── play/                  # SPA игрока (/play)
│   └── shared/                # общий CSS + каталог кораблей (ships.js)
├── shared_simple.py           # модель Ship/Team/ActionType
├── server_full_visibility.py  # игровые правила (process_turn, видимость, etc.)
├── protocol.py                # length-prefixed JSON (для LAN-клиентов из tools/)
├── pyproject.toml             # зависимости (fastapi, uvicorn, pydantic, …)
├── run_lan.sh                 # запуск в Linux/macOS
├── run_lan.ps1                # запуск в Windows PowerShell
└── tests/                     # pytest-тесты webapp
```

## Быстрый старт

Требуется **Python ≥ 3.10**.

### 1. Поставить зависимости

```bash
cd game
python -m venv .venv
# Linux / macOS
source .venv/bin/activate
# Windows PowerShell
# .\.venv\Scripts\Activate.ps1

pip install -e .[dev]
```

Минимальный набор без dev-инструментов:

```bash
pip install "fastapi>=0.115" "uvicorn[standard]>=0.30" \
            "pydantic>=2.7" "jinja2>=3.1" "itsdangerous>=2.2" "python-multipart>=0.0.9"
```

### 2. Поднять сервер

```bash
# Linux / macOS
./run_lan.sh

# Windows PowerShell
.\run_lan.ps1
```

Скрипт слушает `0.0.0.0:8000`, поэтому к серверу можно подключиться с других
устройств в той же сети.

Адреса:

| URL                                     | Кто заходит                 |
|-----------------------------------------|-----------------------------|
| `http://<IP-хоста>:8000/`               | стартовая страница         |
| `http://<IP-хоста>:8000/admin`          | мастер игры (ГМ)           |
| `http://<IP-хоста>:8000/play?c=XXXX&k=YYYY` | игрок (по ссылке от ГМа) |

### 3. Пароль мастера

Задаётся переменной окружения **`GM_PASSWORD`**. Если её нет, используется
небезопасный дефолт `admin` — только для локальной разработки!

```bash
GM_PASSWORD='очень-секретный' ./run_lan.sh
```

Либо в `run_lan.ps1` исправь `$env:GM_PASSWORD` на свой.

### 4. Тесты

```bash
cd game
pip install pytest httpx
PYTHONPATH=. pytest tests
```

## Как узнать IP хоста

* Windows: `ipconfig` → строка `IPv4-адрес` у активного адаптера.
* Linux: `hostname -I` или `ip -4 addr show`.
* macOS: `ipconfig getifaddr en0` (Wi-Fi) или `en1` (Ethernet).

## Что поменялось в игре

* **Роль радиста удалена.** Капитан сам получает все данные разведки — лишней
  прослойки больше нет.
* **Выпадающий список действий** для корабля теперь показывает все
  доступные команды (атака, перемещение, пропуск хода) и спец-способности
  конкретного корабля (лечение — Факел, фаза — Тишина, голограмма —
  Провокатор, мина — Паук).
* **Фикс читерства:** после старта игры новые подключения блокируются
  (`/api/play/resolve` отдаёт 409), а браузер с активной ГМ-сессией не
  может открыть `/play` и подключиться к своей же игре как обычный игрок
  (редирект на `/admin`).

Инструкции по подключению через **Radmin VPN** и публикации игры **в
интернет** лежат в корневом [`README.md`](../README.md).
