import { SHIP_TYPE_INFO, shipIcon, hpClass } from "/static/shared/ships.js";

const $ = (id) => document.getElementById(id);
const state = { data: null, gid: "", token: "" };

// Набор доступных действий для каждого типа корабля
function getActions(ship) {
    const list = [{ id: "pass", label: "💤 Ждать", coords: false }];
    if (ship.move_range > 0) list.push({ id: "move", label: "🚶 Ход", coords: true });
    if (ship.can_shoot) list.push({ id: "shoot", label: "🎯 Огонь", coords: true });
    if (ship.can_place_mine) list.push({ id: "mine", label: "💣 Мина", coords: true });
    return list;
}

function renderMyShips(data) {
    const container = $("my-ships");
    container.innerHTML = Object.values(data.my_ships).map(s => {
        const actions = getActions(s);
        const options = actions.map(a => `<option value="${a.id}">${a.label}</option>`).join("");
        
        return `
            <div class="ship-card" id="ship-${s.id}">
                <div class="ship-header">
                    <span class="ico">${shipIcon(s.type)}</span>
                    <strong>${s.id}</strong>
                    <span class="hp ${hpClass(s.hits, s.max_hits)}">${s.max_hits - s.hits}/${s.max_hits}</span>
                </div>
                <div class="action-form">
                    <select class="act-select" onchange="toggleCoords('${s.id}')">
                        ${options}
                    </select>
                    <div class="coords-row hidden" id="coords-${s.id}">
                        <input type="number" class="cx" placeholder="X" min="0" max="9">
                        <input type="number" class="cy" placeholder="Y" min="0" max="9">
                        <input type="number" class="cz" placeholder="Z" min="0" max="9">
                    </div>
                    <button class="primary" onclick="sendAction('${s.id}')">ОК</button>
                </div>
            </div>
        `;
    }).join("");
}

window.toggleCoords = (sid) => {
    const select = document.querySelector(`#ship-${sid} .act-select`);
    const row = $(`coords-${sid}`);
    const isCoords = ["move", "shoot", "mine"].includes(select.value);
    row.classList.toggle("hidden", !isCoords);
};

window.sendAction = async (sid) => {
    const card = $(`ship-${sid}`);
    const type = card.querySelector(".act-select").value;
    const payload = { type };
    
    if (["move", "shoot", "mine"].includes(type)) {
        payload.x = parseInt(card.querySelector(".cx").value);
        payload.y = parseInt(card.querySelector(".cy").value);
        payload.z = parseInt(card.querySelector(".cz").value);
    }

    const r = await fetch(`/api/play/${state.gid}/action/${sid}?token=${state.token}`, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(payload)
    });
    if (r.ok) alert("Приказ принят!");
};