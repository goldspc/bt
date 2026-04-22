"""Role-aware serialization of game state for clients."""
from __future__ import annotations
from typing import Dict, List, Optional
from shared_simple import Team
from .engine import TEAM_LETTER
from .state import (
    Game,
    Player,
    PHASE_LOBBY,
    ROLE_CAPTAIN,
)

def game_lobby_view(game: Game) -> dict:
    return {
        "gid": game.gid,
        "public_id": game.public_id,
        "mode": game.mode,
        "phase": game.phase,
        "turn": game.turn,
        "teams": [t.lobby_view() for t in game.teams.values()],
        "players": [p.public_view() for p in game.players.values()],
        "planning_deadline": game.planning_deadline,
        "all_ready": game.all_teams_ready() if game.phase == PHASE_LOBBY else False,
    }

def game_play_view(game: Game, player: Player) -> dict:
    tstate = game.teams[player.team] if player.team else None
    out = {
        "phase": game.phase,
        "turn": game.turn,
        "role": player.role,
        "team": TEAM_LETTER.get(player.team) if player.team else None,
        "planning_deadline": game.planning_deadline,
    }
    if player.role == ROLE_CAPTAIN and tstate:
        out["my_ships"] = game.engine.team_ships(player.team) if game.engine else {}
        out["intel"] = tstate.captain_intel
        out["orders"] = tstate.orders
    else:
        all_ships = game.engine.team_ships(player.team) if (game.engine and player.team) else {}
        out["my_ships"] = {sid: s for sid, s in all_ships.items() if sid in player.assigned_ships}
        out["intel"] = {}
        out["orders"] = tstate.orders if tstate else {}
    return out

def gm_view(game: Game) -> dict:
    out = {
        "gid": game.gid,
        "public_id": game.public_id,
        "join_key": game.join_key,
        "mode": game.mode,
        "phase": game.phase,
        "turn": game.turn,
        "teams": [t.lobby_view() for t in game.teams.values()],
        "players": [p.public_view() for p in game.players.values()],
        "planning_deadline": game.planning_deadline,
    }
    if game.engine is not None:
        out["ships"] = game.engine.ships_snapshot()
        gs = game.engine.game_state
        out["holograms"] = list(gs.get("holograms", {}).values())
        out["mines"] = list(gs.get("mines", []))
        out["game_over"] = gs.get("game_over", False)
        out["winner"] = gs.get("winner")
    return out