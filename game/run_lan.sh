#!/usr/bin/env bash
# Запустить веб-сервер игры на всех интерфейсах, чтобы другие устройства
# в той же локальной сети (Wi-Fi / LAN / Radmin VPN) могли открыть сайт в
# браузере: http://<IP_хоста>:8000
#
# Останови сервер: Ctrl+C.

set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$HERE"

# Чтобы импорты вроде `from shared_simple import ...` работали без установки
# пакета, добавим папку game/ в PYTHONPATH.
export PYTHONPATH="$HERE${PYTHONPATH:+:$PYTHONPATH}"

# Пароль GM можно переопределить через переменную окружения, иначе использует
# дефолтный `admin` (в продакшне обязательно поменяй!).
: "${GM_PASSWORD:=admin}"
export GM_PASSWORD

exec python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
