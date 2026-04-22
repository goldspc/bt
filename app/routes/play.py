"""Player-facing HTTP + WebSocket routes."""
from __future__ import annotations
import json
from typing import Optional
from fastapi import (APIRouter, Body, HTTPException, Query, Request,
                     WebSocket, WebSocketDisconnect)
from pydantic import BaseModel, Field

# УДАЛЕНО: ROLE_RADIST
from ..state import (MANAGER, PHASE_LOBBY, PHASE_PLANNING, ROLE_CAPTAIN, ROLE_CREW)
from ..views import game_lobby_view, game_play_view
from ..ws import HUB
from .admin import _broadcast_state

router = APIRouter()

class JoinPayload(BaseModel):
    name: str = Field(min_length=1, max_length=24)

@router.get("/resolve")
async def resolve_game(code: str = Query(...), key: str = Query(...)) -> dict:
    g = MANAGER.resolve_by_public(code, key)
    if g is None:
        raise HTTPException(status_code=404, detail="Игра не найдена")
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