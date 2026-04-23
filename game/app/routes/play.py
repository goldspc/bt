"""Player-facing HTTP + WebSocket routes."""
from __future__ import annotations
import json
from typing import Optional
from fastapi import (APIRouter, Body, HTTPException, Query, Request,
                     WebSocket, WebSocketDisconnect)
from pydantic import BaseModel, Field

# Роль «радист» исключена из игры: капитан получает все данные разведки сам.
from ..auth import SESSION_COOKIE, is_gm_cookie_valid
from ..state import (MANAGER, PHASE_LOBBY, PHASE_PLANNING, ROLE_CAPTAIN, ROLE_CREW)
from ..views import game_lobby_view, game_play_view
from ..ws import HUB
from .admin import _broadcast_state

router = APIRouter()

class JoinPayload(BaseModel):
    name: str = Field(min_length=1, max_length=24)


def _reject_if_gm(request: Request) -> None:
    """Запретить GM-сессии выступать в качестве обычного игрока.

    Если браузер уже несёт валидный GM-cookie — это та же машина, что запускала
    игру, и из её текущей авторизации нельзя подключаться к своему же матчу
    как рядовой игрок (читерство — GM видит всё).
    """
    if is_gm_cookie_valid(request.cookies.get(SESSION_COOKIE)):
        raise HTTPException(
            status_code=403,
            detail=("В этом браузере активна сессия мастера игры. "
                    "Разлогиньтесь в /admin, чтобы подключаться как игрок."),
        )


@router.get("/resolve")
async def resolve_game(request: Request,
                        code: str = Query(...), key: str = Query(...)) -> dict:
    _reject_if_gm(request)
    g = MANAGER.resolve_by_public(code, key)
    if g is None:
        raise HTTPException(status_code=404, detail="Игра не найдена")
    # После старта игры новых подключений не принимаем: иначе игрок может
    # нажать «назад» и переприсоединиться уже в запущенную сессию, минуя
    # лобби — мастер не должен получать сюрпризов в середине боя.
    if g.phase != PHASE_LOBBY:
        raise HTTPException(
            status_code=409,
            detail="Игра уже началась, новые подключения запрещены.",
        )
    return {"gid": g.gid, "public_id": g.public_id, "mode": g.mode}

def _must_get(gid: str):
    g = MANAGER.get(gid)
    if g is None:
        raise HTTPException(status_code=404, detail="Игра не найдена")
    return g

def _auth_player(game, token: Optional[str]):
    if not token:
        raise HTTPException(status_code=401, detail="Нужен токен")
    p = game.player_by_token(token)
    if not p:
        raise HTTPException(status_code=401, detail="Неверный токен")
    return p

# Маршруты для действий (ход, выстрел и т.д.) остаются прежними...
# Но функции share_intel и promote_suggestion (которые были в конце вашего файла) 
# нужно УДАЛИТЬ, так как они относились к роли Радиста.

@router.websocket("/{gid}/ws")
async def player_socket(ws: WebSocket, gid: str, token: str) -> None:
    # Браузер с активным GM-cookie не имеет права открывать player-сокет:
    # это антихит для случая «мастер запускает игру и в той же сессии
    # подключается как обычный игрок».
    cookies = dict(ws.cookies) if ws.cookies else {}
    if is_gm_cookie_valid(cookies.get(SESSION_COOKIE)):
        await ws.close(code=4403)
        return
    g = MANAGER.get(gid)
    if g is None:
        await ws.close(code=4404)
        return
    p = g.player_by_token(token)
    if p is None:
        await ws.close(code=4401)
        return
    await ws.accept()
    await HUB.register_player(gid, p.pid, ws)
    try:
        # Отправляем начальное состояние
        await ws.send_text(json.dumps({
            "type": "state", 
            "data": game_play_view(g, p)
        }, default=str))
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        await HUB.unregister_player(gid, p.pid)