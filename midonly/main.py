"""MidOnly.GG - Dota 2 1x1 Mid Lobby Platform."""

from __future__ import annotations

import json
import random
import string
import time
from dataclasses import dataclass, field
from typing import Dict, List

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

app = FastAPI(title="MidOnly 1x1 - Pro UI")

BASE_DIR = Path(__file__).resolve().parent

# ---------------------------------------------------------------------------
# In-memory state
# ---------------------------------------------------------------------------

@dataclass
class ChatMessage:
    user: str
    text: str
    ts: float = field(default_factory=time.time)

@dataclass
class Lobby:
    id: str
    title: str
    host: str
    hero: str
    hero_icon: str
    rules: str
    players: List[str] = field(default_factory=list)
    chat: List[ChatMessage] = field(default_factory=list)

def _gen_id(n: int = 4) -> str:
    return "".join(random.choices(string.digits, k=n))

HEROES = [
    ("Shadow Fiend", "nevermore"),
    ("Invoker", "invoker"),
    ("Storm Spirit", "storm_spirit"),
    ("Queen of Pain", "queenofpain"),
    ("Templar Assassin", "templar_assassin"),
    ("Lina", "lina"),
    ("Puck", "puck"),
    ("Ember Spirit", "ember_spirit"),
    ("Tinker", "tinker"),
    ("Zeus", "zuus"),
    ("Outworld Destroyer", "obsidian_destroyer"),
    ("Huskar", "huskar"),
]

LOBBIES: Dict[str, Lobby] = {}
GLOBAL_CHAT: List[ChatMessage] = [
    ChatMessage("Yura Borisov", "Го 1х1, лобби #241."),
    ChatMessage("Alisa", "Патч 7.35 уже скоро?"),
    ChatMessage("MidKing", "Ищу достойного соперника на SF, 5k+"),
    ChatMessage("pro_player", "Кто хочет потренировать Invoker?"),
]

# Seed a few lobbies
for i, (hero_name, hero_key) in enumerate(HEROES[:5]):
    lid = str(241 + i)
    LOBBIES[lid] = Lobby(
        id=lid,
        title=f"#{lid} [RU] Mid Solo",
        host=random.choice(["Alexander Petrov", "MidKing", "Tsipp", "pro_player"]),
        hero=hero_name,
        hero_icon=f"https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/{hero_key}.png",
        rules="First Blood / Tower | No Bottle, No Raindrops | Руны: запрещены | Лес: запрещён",
    )

# ---------------------------------------------------------------------------
# WebSocket chat hub
# ---------------------------------------------------------------------------

class ConnectionManager:
    def __init__(self):
        self.active: List[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.append(ws)

    def disconnect(self, ws: WebSocket):
        self.active.remove(ws)

    async def broadcast(self, message: dict):
        for ws in list(self.active):
            try:
                await ws.send_json(message)
            except Exception:
                pass

manager = ConnectionManager()

@app.websocket("/ws/chat")
async def chat_ws(ws: WebSocket):
    await manager.connect(ws)
    try:
        while True:
            data = await ws.receive_json()
            user = data.get("user", "Аноним")
            text = data.get("text", "")
            if not text.strip():
                continue
            msg = ChatMessage(user=user, text=text)
            GLOBAL_CHAT.append(msg)
            if len(GLOBAL_CHAT) > 200:
                GLOBAL_CHAT.pop(0)
            await manager.broadcast({"type": "chat", "user": msg.user, "text": msg.text})
    except WebSocketDisconnect:
        manager.disconnect(ws)

# ---------------------------------------------------------------------------
# REST API
# ---------------------------------------------------------------------------

@app.get("/api/lobbies")
async def list_lobbies():
    return [
        {
            "id": lb.id,
            "title": lb.title,
            "host": lb.host,
            "hero": lb.hero,
            "hero_icon": lb.hero_icon,
            "rules": lb.rules,
            "player_count": len(lb.players),
        }
        for lb in LOBBIES.values()
    ]

@app.get("/api/lobby/{lobby_id}")
async def get_lobby(lobby_id: str):
    lb = LOBBIES.get(lobby_id)
    if not lb:
        return {"error": "not found"}
    return {
        "id": lb.id,
        "title": lb.title,
        "host": lb.host,
        "hero": lb.hero,
        "hero_icon": lb.hero_icon,
        "rules": lb.rules,
        "player_count": len(lb.players),
    }

@app.post("/api/lobbies")
async def create_lobby(data: dict):
    lid = _gen_id()
    hero_name, hero_key = random.choice(HEROES)
    if data.get("hero"):
        for h_name, h_key in HEROES:
            if h_key == data["hero"]:
                hero_name, hero_key = h_name, h_key
                break
    lb = Lobby(
        id=lid,
        title=data.get("title", f"#{lid} [RU] Mid Solo"),
        host=data.get("host", "Player"),
        hero=hero_name,
        hero_icon=f"https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/{hero_key}.png",
        rules=data.get("rules", "First Blood / Tower | No Bottle, No Raindrops | Руны: запрещены | Лес: запрещён"),
    )
    LOBBIES[lid] = lb
    return {"id": lid, "title": lb.title}

@app.get("/api/chat/history")
async def chat_history():
    return [{"user": m.user, "text": m.text} for m in GLOBAL_CHAT[-50:]]

@app.get("/api/heroes")
async def hero_list():
    return [{"name": n, "key": k} for n, k in HEROES]

# ---------------------------------------------------------------------------
# Main page
# ---------------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
async def index():
    html_path = BASE_DIR / "templates" / "index.html"
    return HTMLResponse(html_path.read_text(encoding="utf-8"))

# ---------------------------------------------------------------------------
# Static files
# ---------------------------------------------------------------------------

app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
