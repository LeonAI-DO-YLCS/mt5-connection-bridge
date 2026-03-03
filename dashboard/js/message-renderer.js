/**
 * MT5 Bridge Dashboard — Canonical Message Renderer
 *
 * Renders MessageEnvelope responses as structured toast-style notifications
 * instead of raw browser `alert()` calls. Falls back gracefully when the
 * response is a legacy plain-text error string.
 *
 * Usage:
 *   import { showEnvelope, showSuccess, showError } from "./message-renderer.js";
 *   showEnvelope(envelopeOrError);        // auto-detects envelope vs legacy
 *   showSuccess("Trade executed", data);  // quick success toast
 *   showError("Something broke");         // quick error toast
 */

/* ── Severity → colour mapping ─────────────────────────────────────── */
const SEVERITY_STYLES = {
  low:      { bg: "#e8f5e9", border: "#43a047", icon: "✅", text: "#1b5e20" },
  medium:   { bg: "#fff3e0", border: "#ef6c00", icon: "⚠️", text: "#e65100" },
  high:     { bg: "#fce4ec", border: "#c62828", icon: "🚨", text: "#b71c1c" },
  critical: { bg: "#f3e5f5", border: "#6a1b9a", icon: "🔥", text: "#4a148c" },
};

const SUCCESS_STYLE = { bg: "#e8f5e9", border: "#2e7d32", icon: "✅", text: "#1b5e20" };

/* ── Container (lazy-created) ──────────────────────────────────────── */
let _container = null;

function getContainer() {
  if (_container) return _container;
  _container = document.createElement("div");
  _container.id = "msgToastContainer";
  Object.assign(_container.style, {
    position: "fixed",
    top: "20px",
    right: "20px",
    zIndex: "9999",
    display: "flex",
    flexDirection: "column",
    gap: "10px",
    maxWidth: "460px",
    width: "100%",
    pointerEvents: "none",
  });
  document.body.appendChild(_container);
  return _container;
}

/* ── Core render function ─────────────────────────────────────────── */
function renderToast(html, style, autoCloseMs = 8000) {
  const toast = document.createElement("div");
  toast.className = "msg-toast";
  Object.assign(toast.style, {
    background: style.bg,
    border: `2px solid ${style.border}`,
    borderRadius: "10px",
    padding: "14px 18px",
    color: style.text,
    fontFamily: "'Inter', system-ui, sans-serif",
    fontSize: "13px",
    lineHeight: "1.5",
    boxShadow: "0 4px 20px rgba(0,0,0,0.15)",
    opacity: "0",
    transform: "translateX(40px)",
    transition: "opacity 0.3s ease, transform 0.3s ease",
    pointerEvents: "auto",
    position: "relative",
    wordBreak: "break-word",
  });
  toast.innerHTML = html;

  // Close button
  const closeBtn = document.createElement("button");
  closeBtn.textContent = "×";
  Object.assign(closeBtn.style, {
    position: "absolute",
    top: "6px",
    right: "10px",
    background: "none",
    border: "none",
    fontSize: "18px",
    cursor: "pointer",
    color: style.text,
    opacity: "0.6",
    lineHeight: "1",
  });
  closeBtn.addEventListener("click", () => dismiss(toast));
  toast.appendChild(closeBtn);

  getContainer().appendChild(toast);

  // Animate in
  requestAnimationFrame(() => {
    toast.style.opacity = "1";
    toast.style.transform = "translateX(0)";
  });

  // FR-018: Copy tracking ID to clipboard
  toast.querySelectorAll(".msg-copy-tid").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      const tid = btn.getAttribute("data-tid");
      navigator.clipboard.writeText(tid).then(() => {
        btn.textContent = "✔";
        setTimeout(() => { btn.textContent = "📋"; }, 1500);
      }).catch(() => {
        btn.textContent = "!";
      });
    });
  });

  // Auto-dismiss
  if (autoCloseMs > 0) {
    setTimeout(() => dismiss(toast), autoCloseMs);
  }
}

function dismiss(toast) {
  toast.style.opacity = "0";
  toast.style.transform = "translateX(40px)";
  setTimeout(() => toast.remove(), 300);
}

/* ── Public API ────────────────────────────────────────────────────── */

/**
 * Show a canonical MessageEnvelope or fall back to a legacy error.
 * @param {object|Error|string} source — the envelope body, an Error, or a string
 */
export function showEnvelope(source) {
  const env = _parseEnvelope(source);
  if (!env) {
    // Legacy fallback — just show a basic error toast
    showError(typeof source === "string" ? source : source?.message || "Unknown error");
    return;
  }

  const style = env.ok
    ? SUCCESS_STYLE
    : (SEVERITY_STYLES[env.severity] || SEVERITY_STYLES.medium);

  const parts = [
    `<div style="font-weight:700;font-size:14px;margin-bottom:4px;">${style.icon} ${_esc(env.title)}</div>`,
    `<div>${_esc(env.message)}</div>`,
  ];

  if (env.action && env.action !== "No action required.") {
    parts.push(`<div style="margin-top:6px;font-style:italic;opacity:0.85;">💡 ${_esc(env.action)}</div>`);
  }

  if (env.tracking_id) {
    const tid = _esc(env.tracking_id);
    parts.push(
      `<div style="margin-top:8px;font-size:11px;opacity:0.6;font-family:monospace;display:flex;align-items:center;gap:6px;">` +
      `<span>Tracking: ${tid} · Code: ${_esc(env.code)}</span>` +
      `<button class="msg-copy-tid" data-tid="${tid}" title="Copy tracking ID" style="` +
      `background:none;border:1px solid currentColor;border-radius:4px;padding:1px 5px;` +
      `cursor:pointer;font-size:10px;color:inherit;opacity:0.8;">📋</button>` +
      `</div>`
    );
  }

  // FR-019: Collapsible Details section showing context key-value pairs
  if (env.context && typeof env.context === "object" && Object.keys(env.context).length > 0) {
    let ctxRows = "";
    for (const [k, v] of Object.entries(env.context)) {
      ctxRows += `<div style="display:flex;gap:8px;padding:2px 0;">` +
        `<span style="font-weight:600;min-width:100px;">${_esc(k)}:</span>` +
        `<span>${_esc(String(v))}</span></div>`;
    }
    parts.push(
      `<details style="margin-top:6px;font-size:11px;cursor:pointer;">` +
      `<summary style="opacity:0.7;user-select:none;">Details</summary>` +
      `<div style="margin-top:4px;padding:6px 8px;background:rgba(0,0,0,0.05);border-radius:4px;font-family:monospace;">` +
      `${ctxRows}</div></details>`
    );
  }

  // Longer display for critical errors
  const autoClose = env.severity === "critical" ? 15000 : (env.ok ? 5000 : 8000);
  renderToast(parts.join(""), style, autoClose);
}

/**
 * Quick success toast. Optionally pass result data for extra details.
 * @param {string} message
 * @param {object} [data]
 */
export function showSuccess(message, data) {
  let extra = "";
  if (data?.ticket_id) {
    extra += ` Ticket: <strong>${data.ticket_id}</strong>`;
  }
  if (data?.filled_price) {
    extra += ` @ ${data.filled_price}`;
  }
  renderToast(
    `<div style="font-weight:700;font-size:14px;">${SUCCESS_STYLE.icon} ${_esc(message)}</div>${extra ? `<div style="margin-top:4px;">${extra}</div>` : ""}`,
    SUCCESS_STYLE,
    5000,
  );
}

/**
 * Quick error toast (for legacy code paths).
 * @param {string} message
 */
export function showError(message) {
  const style = SEVERITY_STYLES.medium;
  renderToast(
    `<div style="font-weight:700;font-size:14px;">${style.icon} Error</div><div>${_esc(message)}</div>`,
    style,
    8000,
  );
}

/**
 * Try to extract a canonical envelope from an API error.
 * Works with:
 *  - Direct envelope objects (from response JSON)
 *  - Error objects whose message is JSON-stringified envelope
 *  - Error objects whose message is JSON-stringified legacy detail
 * @param {*} source
 * @returns {object|null}
 */
function _parseEnvelope(source) {
  if (!source) return null;

  // Direct envelope object
  if (typeof source === "object" && "code" in source && "tracking_id" in source) {
    return source;
  }

  // Error whose message might be JSON
  const raw = source?.message || (typeof source === "string" ? source : null);
  if (!raw) return null;

  try {
    const parsed = JSON.parse(raw);
    if (parsed && typeof parsed === "object" && "code" in parsed && "tracking_id" in parsed) {
      return parsed;
    }
  } catch {
    // Not JSON — legacy error string
  }
  return null;
}

/** Escape HTML entities to prevent XSS in toast content. */
function _esc(str) {
  if (!str) return "";
  const d = document.createElement("div");
  d.textContent = String(str);
  return d.innerHTML;
}
