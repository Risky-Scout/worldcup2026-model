// Market X-Ray — shared JS helpers
// Plain script (no ES modules) — matches existing WoO page pattern

// ── Math helpers ─────────────────────────────────────────────────────────────
function americanToDecimal(american) {
  if (american > 0) return 1 + american / 100;
  return 1 + 100 / Math.abs(american);
}

function decimalToAmerican(decimal) {
  if (decimal <= 1) return 0;
  if (decimal >= 2) return Math.round((decimal - 1) * 100);
  return Math.round(-100 / (decimal - 1));
}

function probToAmerican(p) {
  if (p <= 0 || p >= 1) return 0;
  if (p >= 0.5) return Math.round(-100 * p / (1 - p));
  return Math.round(100 * (1 - p) / p);
}

function removeVig(rawProbs) {
  // rawProbs: {home: decimal, draw: decimal, away: decimal}
  const impliedSum = Object.values(rawProbs).reduce((s, d) => s + 1 / d, 0);
  const result = {};
  for (const [k, d] of Object.entries(rawProbs)) {
    result[k] = (1 / d) / impliedSum;
  }
  return result;
}

function calculateEV(modelProb, marketDecimal) {
  return modelProb * (marketDecimal - 1) * 100 - (1 - modelProb) * 100;
}

function formatAmericanOdds(american) {
  if (american == null) return '—';
  return american > 0 ? '+' + american : '' + american;
}

function formatEdgePP(pp) {
  if (pp == null || isNaN(pp)) return '—';
  return (pp > 0 ? '+' : '') + pp.toFixed(1) + ' pp';
}

function formatEV(ev) {
  if (ev == null || isNaN(ev)) return '—';
  return (ev > 0 ? '+' : '') + ev.toFixed(1) + '%';
}

function formatPct(p) {
  if (p == null || isNaN(p)) return '—';
  return (p * 100).toFixed(1) + '%';
}

function esc(s) {
  return String(s ?? '').replace(/[&<>"']/g, c =>
    ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
}

// ── Action label → CSS class ─────────────────────────────────────────────────
function actionClass(action) {
  const map = {
    'BET':          'action-bet',
    'SMALL BET':    'action-small-bet',
    'LEAN':         'action-lean',
    'WAIT':         'action-wait',
    'PASS':         'action-pass',
    'DO NOT CHASE': 'action-do-not-chase',
    'HEDGE / REDUCE': 'action-hedge',
  };
  return map[action] || 'action-pass';
}

function actionBadge(action, large) {
  const cls = actionClass(action);
  const szCls = large ? ' lg' : '';
  return `<span class="action-badge ${cls}${szCls}">${esc(action)}</span>`;
}

// ── Confidence badge ─────────────────────────────────────────────────────────
function confidenceBadge(grade) {
  if (!grade) return '<span class="conf-badge conf-D">D</span>';
  const letter = grade[0];
  return `<span class="conf-badge conf-${letter}">${esc(grade)}</span>`;
}

// ── Confidence sort order ────────────────────────────────────────────────────
function confidenceOrder(grade) {
  const order = { 'A': 0, 'B': 1, 'C': 2, 'D': 3 };
  return order[grade ? grade[0] : 'D'] ?? 3;
}

// ── Probability comparison bar HTML ─────────────────────────────────────────
function probBarHTML(modelProb, marketProb) {
  const mPct = Math.min(100, Math.round((modelProb || 0) * 100));
  const mkPct = Math.min(100, Math.round((marketProb || 0) * 100));
  return `
    <div class="prob-bar-wrap">
      <div class="prob-bar" title="Model: ${mPct}%">
        <div class="prob-bar-model" style="width:${mPct}%"></div>
      </div>
      <div class="prob-bar" title="Market: ${mkPct}%">
        <div class="prob-bar-market" style="width:${mkPct}%"></div>
      </div>
      <div class="prob-bar-labels">
        <span style="color:var(--gold)">M ${mPct}%</span>
        <span style="color:var(--blue)">Mkt ${mkPct}%</span>
      </div>
    </div>`;
}

// ── Data fetch with timeout ──────────────────────────────────────────────────
async function fetchWithTimeout(url, timeoutMs) {
  timeoutMs = timeoutMs || 8000;
  try {
    const r = await fetch(url + '?t=' + Date.now(), {
      signal: AbortSignal.timeout(timeoutMs),
    });
    if (r.ok) return r.json();
  } catch (e) {}
  return null;
}

// ── Fetch wc-xray.json with fallback chain ────────────────────────────────────
async function loadXrayData() {
  const urls = [
    './wc-xray.json',
    '../wc-xray.json',
    '../worldcup/wc-xray.json',
    '/tools/odds-scanner/predictions/worldcup/wc-xray.json',
  ];
  for (const url of urls) {
    const data = await fetchWithTimeout(url);
    if (data) return data;
  }
  return null;
}

// ── Markets table renderer ────────────────────────────────────────────────────
function renderMarketsTable(markets, container, options) {
  options = options || {};
  if (!markets || !markets.length) {
    container.innerHTML = '<div class="loading-state" style="padding:24px;">No markets to display.</div>';
    return;
  }

  // Group by type if requested
  let groups = {};
  if (options.group) {
    for (const m of markets) {
      const g = marketGroup(m.market_id);
      if (!groups[g]) groups[g] = [];
      groups[g].push(m);
    }
  } else {
    groups = { '': markets };
  }

  const thead = `<thead><tr>
    <th>Market</th><th>Selection</th>
    <th>Model%</th><th>Mkt%</th>
    <th>Fair Odds</th><th>Best Mkt</th>
    <th>Edge</th><th>EV/100</th>
    <th>Conf</th><th>Action</th>
  </tr></thead>`;

  let tbody = '<tbody>';
  for (const [groupName, rows] of Object.entries(groups)) {
    if (groupName && options.group) {
      tbody += `<tr><td colspan="10" class="market-group-header">${esc(groupName)}</td></tr>`;
    }
    rows.forEach((m, i) => {
      const edgeCls = m.edge_pp > 0 ? 'edge-pos' : (m.edge_pp < 0 ? 'edge-neg' : 'edge-zero');
      const rowId = `mkt-row-${options.prefix || ''}${i}`;
      const detailId = `mkt-detail-${options.prefix || ''}${i}`;
      tbody += `<tr class="market-row" id="${rowId}" onclick="toggleDetailRow('${rowId}','${detailId}',this)">
        <td><strong style="color:var(--text)">${esc(m.market_label)}</strong></td>
        <td style="color:var(--text-dim)">${esc(m.selection_label || '')}</td>
        <td>${formatPct(m.model_probability)}</td>
        <td>${formatPct(m.market_no_vig_probability)}</td>
        <td style="font-weight:600">${formatAmericanOdds(m.model_fair_american)}</td>
        <td style="color:var(--blue)">${formatAmericanOdds(m.market_odds_american)}</td>
        <td class="${edgeCls}">${formatEdgePP(m.edge_pp)}</td>
        <td>${m.ev_per_100 != null ? formatEV(m.ev_per_100) : '—'}</td>
        <td>${confidenceBadge(m.confidence)}</td>
        <td>${actionBadge(m.action)}</td>
      </tr>
      <tr class="detail-row" id="${detailId}">
        <td colspan="10">
          <div class="detail-panel">
            <div class="detail-note">${esc(m.trader_note || '')}</div>
            ${probBarHTML(m.model_probability, m.market_no_vig_probability)}
          </div>
        </td>
      </tr>`;
    });
  }
  tbody += '</tbody>';

  container.innerHTML = `<table class="xray-table" style="width:100%">${thead}${tbody}</table>`;
}

function toggleDetailRow(rowId, detailId, rowEl) {
  const detail = document.getElementById(detailId);
  if (!detail) return;
  const isOpen = detail.classList.contains('open');
  document.querySelectorAll('.detail-row.open').forEach(r => {
    r.classList.remove('open');
    const prevRow = document.getElementById(r.id.replace('detail', 'row'));
    if (prevRow) prevRow.classList.remove('expanded');
  });
  if (!isOpen) {
    detail.classList.add('open');
    rowEl.classList.add('expanded');
  }
}

// ── Market group classifier ──────────────────────────────────────────────────
function marketGroup(market_id) {
  if (!market_id) return 'Other';
  if (['home_win','draw','away_win'].includes(market_id)) return '1X2';
  if (market_id.startsWith('over_') || market_id.startsWith('under_')) return 'Totals';
  if (market_id.startsWith('home_over') || market_id.startsWith('home_under') ||
      market_id.startsWith('away_over') || market_id.startsWith('away_under')) return 'Team Totals';
  if (market_id.startsWith('btts')) return 'BTTS';
  if (market_id.startsWith('draw_no_bet')) return 'DNB';
  if (market_id.startsWith('double_chance')) return 'Double Chance';
  if (market_id.startsWith('asian_handicap')) return 'Asian Handicap';
  if (market_id.startsWith('clean_sheet')) return 'Clean Sheet';
  return 'Other';
}

// ── Line movement renderer ────────────────────────────────────────────────────
function renderLineMovement(lineMovement, container) {
  if (!lineMovement) { container.innerHTML = '<em class="clv-pending">No movement data.</em>'; return; }
  const { snapshots_available, open_edge_pp, current_edge_pp, edge_change, note } = lineMovement;
  const changeCls = edge_change > 0 ? 'edge-pos' : (edge_change < 0 ? 'edge-neg' : 'edge-zero');
  container.innerHTML = `
    <div style="display:flex;gap:32px;flex-wrap:wrap;margin-bottom:10px;">
      <div><div class="filter-label">Snapshots</div><div style="font-size:20px;font-weight:600;font-family:'JetBrains Mono',monospace">${snapshots_available ?? '—'}</div></div>
      <div><div class="filter-label">Open Edge</div><div style="font-size:20px;font-weight:600;font-family:'JetBrains Mono',monospace">${formatEdgePP(open_edge_pp)}</div></div>
      <div><div class="filter-label">Current Edge</div><div style="font-size:20px;font-weight:600;font-family:'JetBrains Mono',monospace">${formatEdgePP(current_edge_pp)}</div></div>
      <div><div class="filter-label">Change</div><div class="font-size:20px;font-weight:600;font-family:'JetBrains Mono',monospace ${changeCls}">${edge_change != null ? formatEdgePP(edge_change) : '—'}</div></div>
    </div>
    <div style="font-family:'JetBrains Mono',monospace;font-size:12px;color:var(--text-dim)">${esc(note || '')}</div>`;
}

// ── What changed renderer ─────────────────────────────────────────────────────
function renderWhatChanged(changes, container) {
  if (!changes || !changes.length) {
    container.innerHTML = '<div style="font-family:\'JetBrains Mono\',monospace;font-size:12px;color:var(--text-muted)">No changes since last update.</div>';
    return;
  }
  let html = '';
  for (const c of changes) {
    let fields = '';
    for (const [field, diff] of Object.entries(c.changes || {})) {
      fields += `<span class="change-field">${esc(field)}</span>: <span class="change-prev">${esc(String(diff.prev))}</span><span class="change-arrow">→</span><span class="change-curr">${esc(String(diff.curr))}</span>  `;
    }
    html += `<div class="change-item"><strong style="color:var(--text)">${esc(c.market_label)}</strong><br>${fields}</div>`;
  }
  container.innerHTML = html;
}

// ── CLV signals renderer ──────────────────────────────────────────────────────
function renderCLVSignals(signals, container) {
  if (!signals || !signals.length) {
    container.innerHTML = '<div style="font-family:\'JetBrains Mono\',monospace;font-size:12px;color:var(--text-muted)">No CLV signals for this match.</div>';
    return;
  }
  let rows = '';
  for (const s of signals) {
    const closeCell = s.closing_timestamp
      ? `<td>${esc(s.closing_source || '—')}</td>`
      : `<td class="clv-pending">CLV Pending</td>`;
    const beatCell = s.beat_close != null ? `<td>${s.beat_close ? '✓' : '✗'}</td>` : `<td class="clv-pending">—</td>`;
    rows += `<tr>
      <td>${esc(s.market_label)}</td>
      <td>${s.prediction_timestamp ? s.prediction_timestamp.slice(0,16) : '—'}</td>
      <td>${s.model_fair_odds != null ? s.model_fair_odds.toFixed(3) : '—'}</td>
      ${closeCell}
      ${beatCell}
    </tr>`;
  }
  container.innerHTML = `<table class="clv-table">
    <thead><tr><th>Market</th><th>Signal Time</th><th>Fair Odds</th><th>Close / Source</th><th>Beat Close?</th></tr></thead>
    <tbody>${rows}</tbody>
  </table>`;
}

// ── iframe auto-resize ────────────────────────────────────────────────────────
(function () {
  if (window.self === window.top) return;
  let lastSentHeight = 0;

  function sendHeight() {
    try {
      const root = document.getElementById('app-root') || document.body;
      const h = Math.ceil(root.getBoundingClientRect().height || document.documentElement.scrollHeight);
      if (h > 0 && Math.abs(h - lastSentHeight) > 2) {
        lastSentHeight = h;
        window.parent.postMessage({ frameHeight: h }, 'https://wizardofodds.com');
      }
    } catch (e) {}
  }

  window.addEventListener('load', sendHeight);
  document.addEventListener('DOMContentLoaded', sendHeight);
  document.addEventListener('click', () => setTimeout(sendHeight, 150));
  if (window.MutationObserver) {
    new MutationObserver(sendHeight).observe(document.body, { attributes: true, childList: true, subtree: true });
  }
  if (window.ResizeObserver) {
    new ResizeObserver(sendHeight).observe(document.body);
  }
  setInterval(sendHeight, 1000);
})();
