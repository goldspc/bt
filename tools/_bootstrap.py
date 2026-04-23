"""Shared sys.path setup for the utility scripts in this folder.

Вспомогательные скрипты из `tools/` (LAN-клиент/ГМ, симулятор, турнир, демо)
импортируют `shared_simple`, `protocol`, `server_full_visibility`, которые
лежат в соседней папке `game/`. Этот модуль добавляет её в ``sys.path`` —
просто импортируй его первым:

    import _bootstrap  # noqa: F401

Тогда команды вроде ``python tools/simulate_game.py`` работают из корня репо
без установки пакета.
"""
from __future__ import annotations

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_GAME_DIR = os.path.normpath(os.path.join(_HERE, os.pardir, "game"))
if _GAME_DIR not in sys.path:
    sys.path.insert(0, _GAME_DIR)
