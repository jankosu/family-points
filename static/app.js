const $ = s => document.querySelector(s);
$('#day').value = new Date().toISOString().slice(0, 10);

async function api(path, method = 'GET', body) {
  const res = await fetch(path, { method, headers: { 'Content-Type': 'application/json' }, body: body ? JSON.stringify(body) : null });
  const json = await res.json();
  if (!res.ok) throw new Error(json.error);
  return json;
}
function msg(text) { $('#msg').textContent = text; setTimeout(() => { $('#msg').textContent = ''; }, 3500); }
function task(child, t, locked) { return `<label class="task ${t.checked ? 'done' : ''}"><input type="checkbox" ${t.checked ? 'checked' : ''} ${locked ? 'disabled' : ''} onchange="toggle('${child.id}','${t.id}',this.checked)"><span>${t.title}</span><b class="pts">+${t.points}</b></label>`; }
function groupByPeriod(list) { const order = [], map = {}; for (const t of list) { if (!map[t.period]) { map[t.period] = []; order.push(t.period); } map[t.period].push(t); } return order.map(p => ({ period: p, items: map[p] })); }
function periodsHtml(child, list, locked) { return groupByPeriod(list).map(g => `<div class="period-title">${g.period}</div>${g.items.map(t => task(child, t, locked)).join('')}`).join(''); }
let CHILDREN = [];
let REWARDS = [];
function rewardHtml(r) { const duration = r.unit_minutes ? ` / ${r.unit_minutes} min` : ''; return `<div class="reward">${r.title}<br><span>${r.cost} pkt${duration}</span><br><button onclick="openRedeem(${r.id})">Zrealizuj (rodzic)</button><div class="redeem-form" id="redeem-${r.id}"></div></div>`; }
async function load() {
  try {
    const s = await api('/api/state?date=' + $('#day').value); CHILDREN = s.children; REWARDS = s.rewards;
    $('#children').innerHTML = s.children.map(c => `<article class="card"><div class="name">${c.emoji} ${c.name}<span class="score">Saldo: ${c.summary.balance} pkt</span></div><div>Baza: ${c.summary.base_done}/${c.summary.base_total} · dziś: <b>${c.summary.today_points} pkt</b></div><div class="progress"><i style="width:${c.summary.base_done / c.summary.base_total * 100}%"></i></div>${periodsHtml(c, c.tasks.filter(x => x.kind === 'base'), false)}<div class="extra-title">✨ Dodatkowe ${c.summary.base_complete ? '' : '— najpierw Baza'}</div><div class="${c.summary.base_complete ? '' : 'locked'}">${c.tasks.filter(x => x.kind === 'extra').map(t => task(c, t, !c.summary.base_complete)).join('')}</div></article>`).join('');
    $('#rewards').innerHTML = s.rewards.map(rewardHtml).join('');
  } catch (e) { msg(e.message); }
}
async function toggle(child, taskId, on) { try { await api('/api/toggle', 'POST', { day: $('#day').value, child, task: taskId, checked: on }); load(); } catch (e) { msg(e.message); load(); } }
function openRedeem(id) {
  const reward = REWARDS.find(r => r.id === id), box = $(`#redeem-${id}`); if (!reward || !box) return;
  if (box.innerHTML) { box.innerHTML = ''; return; }
  const minutes = reward.unit_minutes ? `<label>Minuty <input id="minutes-${id}" type="number" min="1" step="1" value="${reward.unit_minutes}"></label>` : '';
  const children = CHILDREN.map(c => `<option value="${c.id}">${c.name}</option>`).join('');
  box.innerHTML = `<hr><b>Realizacja nagrody</b>${minutes}<label>Dla kogo <select id="child-${id}">${children}</select></label><label>PIN rodzica <input id="pin-${id}" type="password" inputmode="numeric" autocomplete="off"></label><button onclick="redeem(${id})">Potwierdź realizację</button>`;
}
async function redeem(id) {
  const reward = REWARDS.find(r => r.id === id); let minutes = null;
  if (reward && reward.unit_minutes) { minutes = Number($(`#minutes-${id}`).value); if (!Number.isInteger(minutes) || minutes <= 0) { msg('Podaj poprawną liczbę minut.'); return; } }
  const child = $(`#child-${id}`).value, pin = $(`#pin-${id}`).value;
  try { const res = await api('/api/redeem', 'POST', { id, child, pin, minutes }); msg(`Nagroda zatwierdzona! (${res.cost} pkt)`); load(); } catch (e) { msg(e.message); }
}
async function addReward() { try { await api('/api/reward', 'POST', { title: $('#rtitle').value, cost: Number($('#rcost').value), pin: $('#pin').value }); msg('Dodano nagrodę.'); load(); } catch (e) { msg(e.message); } }
async function showHistory() { try { const child = $('#hchild').value, pin = $('#pin').value; const r = await api('/api/history?child=' + child + '&pin=' + encodeURIComponent(pin)); $('#history').innerHTML = '<table><tr><th>Data</th><th>Zadanie</th><th>Punkty</th></tr>' + r.events.map(e => `<tr><td>${e.date}</td><td>${e.label}</td><td>${e.points > 0 ? '+' : ''}${e.points}</td></tr>`).join('') + '</table>' + (r.events.length ? '' : '<i>Brak historii.</i>'); } catch (e) { msg(e.message); } }
load();
