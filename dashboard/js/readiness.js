/**
 * MT5 Bridge — Readiness Panel UI Component (Phase 2).
 *
 * Renders a readiness status panel in the Execute tab that shows
 * the aggregate result of GET /readiness.
 */

// ── State ───────────────────────────────────────────────────────────────────

let _lastReadiness = null;
let _panelEl = null;
let _warningAcknowledged = false;

const STATUS_ICONS = {
  ready: '✅',
  degraded: '⚠️',
  blocked: '🚫',
};

const CHECK_ICONS = {
  pass: '✅',
  warn: '⚠️',
  fail: '❌',
  unknown: '❓',
};

// ── Public API ──────────────────────────────────────────────────────────────

/**
 * Returns true if the readiness status is blocked (Submit should be disabled).
 */
export function isReadinessBlocked() {
  if (!_lastReadiness) return true; // No data yet → don't allow
  return _lastReadiness.overall_status === 'blocked';
}

/**
 * Returns true if the readiness status is degraded (warnings need ack).
 */
export function isReadinessDegraded() {
  if (!_lastReadiness) return false;
  return _lastReadiness.overall_status === 'degraded' && !_warningAcknowledged;
}

/**
 * Returns true if the operator has acknowledged degraded warnings.
 */
export function isWarningAcknowledged() {
  return _warningAcknowledged;
}

/**
 * Mount or update the readiness panel in the given container.
 * @param {HTMLElement} containerEl - The DOM element to render into
 * @param {object} formContext - { operation, symbol, direction, volume }
 */
export async function renderReadinessPanel(containerEl, formContext = {}) {
  _panelEl = containerEl;
  _warningAcknowledged = false;

  try {
    const params = new URLSearchParams();
    if (formContext.operation) params.set('operation', formContext.operation);
    if (formContext.symbol) params.set('symbol', formContext.symbol);
    if (formContext.direction) params.set('direction', formContext.direction);
    if (formContext.volume) params.set('volume', formContext.volume);

    const qs = params.toString();
    const url = `/readiness${qs ? '?' + qs : ''}`;

    const apiKey = sessionStorage.getItem('mt5_bridge_api_key') || '';
    const resp = await fetch(url, {
      headers: { 'X-API-KEY': apiKey },
    });

    if (!resp.ok) {
      _renderError(containerEl, `Readiness check failed (HTTP ${resp.status})`);
      _lastReadiness = null;
      return;
    }

    _lastReadiness = await resp.json();
    _renderPanel(containerEl, _lastReadiness, formContext);
  } catch (err) {
    _renderError(containerEl, `Cannot reach readiness endpoint: ${err.message}`);
    _lastReadiness = null;
  }
}

/**
 * Manually refresh the readiness panel.
 */
export async function refreshReadiness(formContext = {}) {
  if (_panelEl) {
    await renderReadinessPanel(_panelEl, formContext);
  }
}

// ── Rendering ───────────────────────────────────────────────────────────────

function _renderPanel(el, data, formContext) {
  const icon = STATUS_ICONS[data.overall_status] || '❓';
  const statusLabel = data.overall_status.charAt(0).toUpperCase() + data.overall_status.slice(1);
  const freshness = _formatTime(data.evaluated_at);

  let html = `
    <div class="readiness-panel readiness-${data.overall_status}">
      <div class="readiness-header">
        <span class="readiness-status-badge">${icon} ${statusLabel}</span>
        <span class="readiness-freshness">
          Evaluated ${freshness}
          <button class="readiness-refresh-btn" title="Refresh readiness">↻</button>
        </span>
      </div>
  `;

  // Blockers
  if (data.blockers && data.blockers.length > 0) {
    html += '<div class="readiness-blockers">';
    html += '<h4 class="readiness-section-title">🚫 Blockers</h4>';
    for (const b of data.blockers) {
      html += `
        <div class="readiness-blocker-card">
          <div class="readiness-check-message">${_escapeHtml(b.user_message)}</div>
          <div class="readiness-check-action">${_escapeHtml(b.action)}</div>
        </div>
      `;
    }
    html += '</div>';
  }

  // Warnings
  if (data.warnings && data.warnings.length > 0) {
    html += '<div class="readiness-warnings">';
    html += '<h4 class="readiness-section-title">⚠️ Warnings</h4>';
    for (const w of data.warnings) {
      html += `
        <div class="readiness-warning-card">
          <div class="readiness-check-message">${_escapeHtml(w.user_message)}</div>
          <div class="readiness-check-action">${_escapeHtml(w.action)}</div>
        </div>
      `;
    }
    if (!_warningAcknowledged) {
      html += `
        <label class="readiness-ack-label">
          <input type="checkbox" class="readiness-ack-checkbox" />
          I acknowledge the warnings and wish to proceed
        </label>
      `;
    }
    html += '</div>';
  }

  // Detailed check list (collapsible)
  html += `
    <details class="readiness-details">
      <summary>All Checks (${data.checks.length})</summary>
      <div class="readiness-check-list">
  `;
  for (const c of data.checks) {
    const cIcon = CHECK_ICONS[c.status] || '❓';
    html += `
      <div class="readiness-check-item readiness-check-${c.status}">
        <span class="readiness-check-icon">${cIcon}</span>
        <span class="readiness-check-id">${_escapeHtml(c.check_id)}</span>
        <span class="readiness-check-msg">${_escapeHtml(c.user_message)}</span>
      </div>
    `;
  }
  html += '</div></details></div>';

  el.innerHTML = html;

  // Bind refresh button
  const refreshBtn = el.querySelector('.readiness-refresh-btn');
  if (refreshBtn) {
    refreshBtn.addEventListener('click', () => refreshReadiness(formContext));
  }

  // Bind ack checkbox
  const ackCb = el.querySelector('.readiness-ack-checkbox');
  if (ackCb) {
    ackCb.addEventListener('change', (e) => {
      _warningAcknowledged = e.target.checked;
      // Dispatch custom event so execute tab can update submit button state
      el.dispatchEvent(new CustomEvent('readiness-ack-change', { bubbles: true }));
    });
  }
}

function _renderError(el, message) {
  el.innerHTML = `
    <div class="readiness-panel readiness-error">
      <div class="readiness-header">
        <span class="readiness-status-badge">⚠️ Error</span>
      </div>
      <div class="readiness-error-message">${_escapeHtml(message)}</div>
    </div>
  `;
}

// ── Helpers ─────────────────────────────────────────────────────────────────

function _formatTime(isoStr) {
  if (!isoStr) return 'unknown';
  try {
    const d = new Date(isoStr);
    return d.toLocaleTimeString();
  } catch {
    return isoStr;
  }
}

function _escapeHtml(str) {
  if (!str) return '';
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}
