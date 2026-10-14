'use strict';

const API = '/api/v1';

// ── HTTP helpers ────────────────────────────────────────────────────────────

async function request(method, path, body) {
  const opts = {
    method,
    headers: { 'Content-Type': 'application/json' },
  };
  if (body !== undefined) opts.body = JSON.stringify(body);
  const res = await fetch(API + path, opts);
  const data = await res.json();
  if (!res.ok) throw data;
  return data;
}

const api = {
  getStatus:        ()             => request('GET',    '/status'),
  getBeverages:     ()             => request('GET',    '/beverages'),
  brew:             (id)           => request('POST',   '/beverages/brew', { beverage_id: id }),
  getContainers:    ()             => request('GET',    '/containers'),
  fillContainer:    (id, level)    => request('PUT',    `/containers/${id}/fill`, { target_level: level }),
  emptyWaste:       ()             => request('DELETE', '/containers/waste'),
  getConfiguration: ()             => request('GET',    '/configuration'),
  applyConfig:      (payload)      => request('POST',   '/configuration', payload),
};

// ── Toast ───────────────────────────────────────────────────────────────────

function toast(msg, kind = 'ok') {
  const rack = document.getElementById('toast-rack');
  const el = document.createElement('div');
  el.className = `toast toast--${kind}`;
  el.textContent = msg;
  rack.appendChild(el);
  setTimeout(() => el.remove(), 3500);
}

function errorMessage(err) {
  if (err.error === 'insufficient_ingredient')
    return `Not enough ${err.container_id}: need ${err.required}${err.unit}, have ${err.available}${err.unit}`;
  if (err.error === 'machine_not_ready')
    return `Machine not ready (${err.machine_state})`;
  if (err.error === 'waste_container_full')
    return `Waste container full (${err.brew_count}/${err.threshold} brews)`;
  if (err.error === 'exceeds_max_capacity')
    return `Exceeds max capacity: ${err.max_capacity}${err.unit}`;
  if (err.error === 'recipe_not_found')
    return `Unknown beverage: ${err.beverage_id}`;
  return err.detail || err.reason || JSON.stringify(err);
}

// ── Machine state ────────────────────────────────────────────────────────────

async function refreshStatus() {
  try {
    const { machine_state } = await api.getStatus();
    const badge = document.getElementById('machine-badge');
    badge.textContent = `● ${machine_state}`;
    badge.className = `badge badge--${machine_state}`;
  } catch (_) {}
}

// ── Tab switching ────────────────────────────────────────────────────────────

function initTabs() {
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));
      btn.classList.add('active');
      document.getElementById(`tab-${btn.dataset.tab}`).classList.add('active');

      if (btn.dataset.tab === 'brew')          loadBeverages();
      if (btn.dataset.tab === 'containers')    loadContainers();
      if (btn.dataset.tab === 'configuration') loadConfiguration();
    });
  });
}

// ── Brew tab ─────────────────────────────────────────────────────────────────

async function loadBeverages() {
  const grid = document.getElementById('beverages-grid');
  grid.innerHTML = '<p class="spinner">Loading…</p>';

  try {
    const [{ beverages }, config] = await Promise.all([api.getBeverages(), api.getConfiguration()]);
    const recipeMap = Object.fromEntries(config.recipes.map(r => [r.beverage_id, r]));
    const unitMap   = Object.fromEntries(config.thresholds.map(t => [t.container_id, t.unit]));

    grid.innerHTML = '';
    beverages.forEach(bev => {
      const recipe = recipeMap[bev.beverage_id];
      const ingredients = recipe
        ? Object.entries(recipe.requirements)
            .map(([cid, amt]) => `${cid.replace('_', ' ')}: ${amt}${unitMap[cid] ?? ''}`)
            .join('<br>')
        : '';

      const card = document.createElement('div');
      card.className = 'card';
      card.innerHTML = `
        <div class="card-title">${bev.name}</div>
        <div class="ingredient-list">${ingredients}</div>
        <button class="btn btn--primary brew-btn" data-id="${bev.beverage_id}">Brew</button>
      `;
      grid.appendChild(card);
    });

    grid.querySelectorAll('.brew-btn').forEach(btn => {
      btn.addEventListener('click', () => brewBeverage(btn.dataset.id, btn));
    });
  } catch (err) {
    grid.innerHTML = `<p class="spinner">Failed to load: ${errorMessage(err)}</p>`;
  }
}

async function brewBeverage(id, btn) {
  btn.disabled = true;
  btn.textContent = 'Brewing…';
  try {
    const result = await api.brew(id);
    toast(`${id} brewed! (${result.status})`, 'ok');
    refreshStatus();
  } catch (err) {
    toast(errorMessage(err), 'error');
    refreshStatus();
  } finally {
    btn.disabled = false;
    btn.textContent = 'Brew';
  }
}

// ── Containers tab ────────────────────────────────────────────────────────────

async function loadContainers() {
  const grid = document.getElementById('containers-grid');
  const wasteWrap = document.getElementById('waste-card-wrap');
  grid.innerHTML = '<p class="spinner">Loading…</p>';
  wasteWrap.innerHTML = '';

  try {
    const data = await api.getContainers();
    grid.innerHTML = '';

    data.ingredients.forEach(c => grid.appendChild(buildContainerCard(c)));
    wasteWrap.appendChild(buildWasteCard(data.waste));
  } catch (err) {
    grid.innerHTML = `<p class="spinner">Failed: ${errorMessage(err)}</p>`;
  }
}

function buildContainerCard(c) {
  const pct = c.max_capacity > 0 ? Math.round((c.level / c.max_capacity) * 100) : 0;
  const card = document.createElement('div');
  card.className = 'card';
  card.innerHTML = `
    <div class="card-title">${formatContainerId(c.container_id)}</div>
    <div class="card-meta">${c.level}${c.unit} / ${c.max_capacity}${c.unit}</div>
    <div class="progress-wrap">
      <div class="progress-bar bar--${c.state}" style="width:${pct}%"></div>
    </div>
    <span class="chip chip--${c.state}">${c.state}</span>
    <div class="fill-row">
      <input type="number" class="fill-input" min="0" max="${c.max_capacity}"
             step="10" value="${c.max_capacity}" placeholder="${c.unit}" />
      <button class="btn btn--primary fill-btn">Fill</button>
    </div>
  `;
  card.querySelector('.fill-btn').addEventListener('click', async (e) => {
    const input = card.querySelector('.fill-input');
    const level = parseFloat(input.value);
    if (isNaN(level) || level < 0) { toast('Enter a valid level', 'warn'); return; }
    e.target.disabled = true;
    try {
      const updated = await api.fillContainer(c.container_id, level);
      toast(`${formatContainerId(c.container_id)} filled to ${updated.level}${updated.unit}`, 'ok');
      refreshStatus();
      loadContainers();
    } catch (err) {
      toast(errorMessage(err), 'error');
    } finally {
      e.target.disabled = false;
    }
  });
  return card;
}

function buildWasteCard(w) {
  const pct = w.full_threshold > 0 ? Math.round((w.brew_count / w.full_threshold) * 100) : 0;
  const wrapper = document.createElement('div');
  wrapper.innerHTML = `
    <div class="section-header" style="margin-bottom:.5rem">
      <h2>Waste Container</h2>
    </div>
    <div class="card">
      <div class="card-body">
        <div class="card-meta">${w.brew_count} / ${w.full_threshold} brews</div>
        <div class="progress-wrap">
          <div class="progress-bar bar--${w.state}" style="width:${pct}%"></div>
        </div>
        <span class="chip chip--${w.state}">${w.state}</span>
      </div>
      <button class="btn btn--danger empty-btn">Empty Waste</button>
    </div>
  `;
  wrapper.querySelector('.empty-btn').addEventListener('click', async (e) => {
    e.target.disabled = true;
    try {
      await api.emptyWaste();
      toast('Waste container emptied', 'ok');
      refreshStatus();
      loadContainers();
    } catch (err) {
      toast(errorMessage(err), 'error');
    } finally {
      e.target.disabled = false;
    }
  });
  return wrapper;
}

// ── Configuration tab ─────────────────────────────────────────────────────────

let _currentConfig = null;

async function loadConfiguration() {
  const panel = document.getElementById('config-panel');
  panel.innerHTML = '<p class="spinner">Loading…</p>';
  try {
    _currentConfig = await api.getConfiguration();
    renderConfig(_currentConfig);
  } catch (err) {
    panel.innerHTML = `<p class="spinner">Failed: ${errorMessage(err)}</p>`;
  }
}

function renderConfig(cfg) {
  const panel = document.getElementById('config-panel');

  // Threshold rows
  const thresholdRows = cfg.thresholds.map(t => `
    <tr>
      <td>${formatContainerId(t.container_id)}</td>
      <td><input class="threshold-input" data-id="${t.container_id}" data-unit="${t.unit}"
                 type="number" min="1" step="5" value="${t.low}" /></td>
      <td>${t.unit}</td>
    </tr>
  `).join('');

  // Recipe rows
  const recipeRows = cfg.recipes.map(r => {
    const reqs = Object.entries(r.requirements)
      .map(([cid, amt]) => `${cid.replace('_', ' ')}: ${amt}`)
      .join(', ');
    return `<tr><td>${r.name}</td><td>${reqs}</td></tr>`;
  }).join('');

  panel.innerHTML = `
    <div class="config-section">
      <h2>Status</h2>
      <div class="config-source">
        Source: <span class="chip chip--${cfg.source === 'remote' ? 'NORMAL' : 'LOW'}">${cfg.source}</span>
      </div>
      <div class="waste-row">
        <label>Waste full threshold (brews):</label>
        <input id="waste-threshold-input" type="number" min="1" step="1" value="${cfg.waste_full_threshold}" />
      </div>
    </div>

    <div class="config-section">
      <h2>Container Thresholds</h2>
      <table>
        <thead><tr><th>Container</th><th>Low threshold</th><th>Unit</th></tr></thead>
        <tbody>${thresholdRows}</tbody>
      </table>
    </div>

    <div class="config-section">
      <h2>Recipes</h2>
      <table>
        <thead><tr><th>Beverage</th><th>Ingredients</th></tr></thead>
        <tbody>${recipeRows}</tbody>
      </table>
    </div>

    <div class="config-actions">
      <button class="btn btn--primary" id="apply-config-btn">Apply Changes</button>
      <button class="btn btn--muted"   id="reset-config-btn">Reset</button>
    </div>
  `;

  document.getElementById('apply-config-btn').addEventListener('click', applyConfiguration);
  document.getElementById('reset-config-btn').addEventListener('click', loadConfiguration);
}

async function applyConfiguration() {
  const btn = document.getElementById('apply-config-btn');
  btn.disabled = true;

  const payload = { thresholds: {} };

  const wasteInput = document.getElementById('waste-threshold-input');
  const wasteVal = parseInt(wasteInput.value, 10);
  if (!isNaN(wasteVal) && wasteVal !== _currentConfig.waste_full_threshold)
    payload.waste_full_threshold = wasteVal;

  document.querySelectorAll('.threshold-input').forEach(input => {
    const id  = input.dataset.id;
    const val = parseFloat(input.value);
    const orig = _currentConfig.thresholds.find(t => t.container_id === id)?.low;
    if (!isNaN(val) && val !== orig)
      payload.thresholds[id] = { low: val };
  });

  if (Object.keys(payload.thresholds).length === 0) delete payload.thresholds;

  if (!payload.waste_full_threshold && !payload.thresholds) {
    toast('No changes to apply', 'warn');
    btn.disabled = false;
    return;
  }

  try {
    const result = await api.applyConfig(payload);
    if (result.status === 'accepted') {
      toast('Configuration applied', 'ok');
      loadConfiguration();
    } else {
      toast(`Rejected: ${result.reason}`, 'error');
    }
  } catch (err) {
    toast(errorMessage(err), 'error');
  } finally {
    btn.disabled = false;
  }
}

// ── Helpers ──────────────────────────────────────────────────────────────────

function formatContainerId(id) {
  return id.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
}

// ── Init ─────────────────────────────────────────────────────────────────────

initTabs();
refreshStatus();
loadBeverages();

// Poll machine status every 5 seconds
setInterval(refreshStatus, 5000);
