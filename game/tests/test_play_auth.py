"""Регрессионные тесты антихит-проверок в play-роутах.

Проверяем два сценария:
1. Браузер с активным GM-cookie не может использовать кабинет игрока
   (/play и /api/play/resolve → 403, 303).
2. После старта игры новые подключения через /api/play/resolve
   блокируются (409) — игрок не может «вернуться назад» и вклиниться
   в уже стартовавшую сессию.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient

os.environ.setdefault("GM_PASSWORD", "admin")

from app.main import app  # noqa: E402
from app.state import MANAGER, PHASE_PLANNING  # noqa: E402


def _gm_client() -> TestClient:
    c = TestClient(app)
    r = c.post("/api/admin/login", data={"password": "admin"})
    assert r.status_code == 200, r.text
    return c


def test_play_page_redirects_when_gm_cookie_present():
    """GM, уже залогиненный в /admin, не должен открывать /play: иначе он
    смог бы подключиться к своей же игре как обычный игрок (читерство)."""
    c = _gm_client()
    r = c.get("/play", follow_redirects=False)
    assert r.status_code == 303
    assert r.headers["location"].startswith("/admin")


def test_play_resolve_rejects_gm_cookie():
    """Тот же антихит, но на API-уровне: /api/play/resolve должен
    отвечать 403, если запрос пришёл из GM-сессии."""
    c = _gm_client()
    gid = c.post("/api/admin/games").json()["gid"]
    g = MANAGER.get(gid)
    assert g is not None

    r = c.get("/api/play/resolve", params={"code": g.public_id, "key": g.join_key})
    assert r.status_code == 403
    assert "мастер" in r.json()["detail"].lower()


def test_play_resolve_rejects_after_game_started():
    """После старта игры новых подключений не принимаем — иначе игрок
    может нажать «назад» и переприсоединиться к уже идущему матчу,
    минуя лобби."""
    c = _gm_client()
    gid = c.post("/api/admin/games").json()["gid"]
    g = MANAGER.get(gid)
    assert g is not None
    g.phase = PHASE_PLANNING  # имитируем старт игры вручную

    # Для чистой проверки резолва идём без GM-cookie (иначе сработает
    # первый фильтр, и мы не увидим 409).
    fresh = TestClient(app)
    r = fresh.get("/api/play/resolve", params={"code": g.public_id, "key": g.join_key})
    assert r.status_code == 409
    assert "уже нач" in r.json()["detail"].lower()
