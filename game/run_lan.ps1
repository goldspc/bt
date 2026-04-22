$ErrorActionPreference = "Stop"

# Run the webapp so other devices on the same Wi-Fi / LAN / Radmin VPN can open it.
# Затем открой в браузере: http://<IP_хоста>:8000
#
# Остановить сервер: Ctrl+C.

# Папка со скриптом — это корень webapp, в ней лежат shared_simple.py,
# protocol.py, server_full_visibility.py. Добавляем её в PYTHONPATH, чтобы
# `python -m uvicorn app.main:app` нашёл `app` и соседние модули.
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir
$env:PYTHONPATH = $ScriptDir

# Пароль GM. В проде обязательно поменяй на свой секрет.
if (-not $env:GM_PASSWORD) { $env:GM_PASSWORD = "admin" }

python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
