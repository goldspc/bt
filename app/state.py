"""In-memory game state: games, teams, players, captain/crew roles."""
from __future__ import annotations
import secrets
import threading
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from shared_simple import Action, ActionType, ShipType, Team
from .engine import TEAM_FROM_LETTER, TEAM_LETTER, WebEngine

# --- Константы ---
PHASE_LOBBY = "lobby"
PHASE_PLANNING = "planning"
PHASE_FINISHED = "finished"

ROLE_CAPTAIN = "captain"
ROLE_CREW = "crew"

MODE_ADVANCED = "advanced"
MODE_NORMAL = "normal"

DEFAULT_TEAM_NAMES = {
    Team.TEAM_A: "Команда A",
    Team.TEAM_B: "Команда B",
    Team.TEAM_C: "Команда C"
}

MAX_PLAYERS_PER_TEAM = 8
PLANNING_TIMEOUT_SECONDS = 90

def new_token(prefix: str = "") -> str:
    return f"{prefix}{secrets.token_urlsafe(8)}"

def new_public_id() -> str:
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    return "".join(secrets.choice(alphabet) for _ in range(6))

def new_join_key() -> str:
    return "".join(secrets.choice("0123456789") for _ in range(4))

@dataclass
class Player:
    pid: str
    token: str
    name: str
    team: Optional[Team] = None
    role: str = ROLE_CREW
    assigned_ships: List[str] = field(default_factory=list)
    connected: bool = True

    def public_view(self) -> dict:
        return {
            "pid": self.pid,
            "name": self.name,
            "team": TEAM_LETTER.get(self.team) if self.team else None,
            "role": self.role,
            "assigned_ships": list(self.assigned_ships),
            "connected": self.connected,
        }

@dataclass
class TeamState:
    team: Team
    display_name: str
    captain_pid: Optional[str] = None
    player_ids: List[str] = field(default_factory=list)
    pool: List[ShipType] = field(default_factory=list)
    ready: bool = False
    captain_intel: Dict[str, dict] = field(default_factory=dict)
    orders: Dict[str, dict] = field(default_factory=dict)

    def lobby_view(self) -> dict:
        return {
            "letter": TEAM_LETTER[self.team],
            "name": self.display_name,
            "captain_pid": self.captain_pid,
            "player_ids": list(self.player_ids),
            "ready": self.ready,
        }

@dataclass
class Game:
    gid: str
    public_id: str
    join_key: str
    created_at: float
    phase: str = PHASE_LOBBY
    mode: str = MODE_ADVANCED
    teams: Dict[Team, TeamState] = field(default_factory=dict)
    players: Dict[str, Player] = field(default_factory=dict)
    engine: Optional[WebEngine] = None
    planning_deadline: Optional[float] = None
    planning_timeout: int = PLANNING_TIMEOUT_SECONDS
    turn: int = 0

    def __post_init__(self):
        if not self.teams:
            for team in (Team.TEAM_A, Team.TEAM_B, Team.TEAM_C):
                self.teams[team] = TeamState(team=team, display_name=DEFAULT_TEAM_NAMES[team])

    def player_by_token(self, token: str) -> Optional[Player]:
        for p in self.players.values():
            if p.token == token: return p
        return None

    def all_teams_ready(self) -> bool:
        active_teams = [t for t in self.teams.values() if len(t.player_ids) > 0]
        if not active_teams: return False
        return all(t.ready for t in active_teams)

class GameManager:
    def __init__(self):
        self._games: Dict[str, Game] = {}
        self._lock = threading.Lock()

    def create(self, mode: str = MODE_ADVANCED) -> Game:
        with self._lock:
            gid = new_token("g_")
            game = Game(gid=gid, public_id=new_public_id(), join_key=new_join_key(), 
                        created_at=time.time(), mode=mode)
            self._games[gid] = game
            return game

    def get(self, gid: str) -> Optional[Game]:
        return self._games.get(gid)

    def resolve_by_public(self, public_id: str, join_key: str) -> Optional[Game]:
        code = (public_id or "").strip().upper()
        for g in self._games.values():
            if g.public_id == code and g.join_key == join_key:
                return g
        return None

    def list_summary(self) -> List[dict]:
        with self._lock:
            return [{"gid": g.gid, "public_id": g.public_id, "phase": g.phase, "turn": g.turn} 
                    for g in self._games.values()]

# Создаем менеджер ПОСЛЕ того, как класс определен
MANAGER = GameManager()