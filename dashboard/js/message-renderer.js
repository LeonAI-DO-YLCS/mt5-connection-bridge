/**
 * MT5 Bridge Dashboard — Canonical Message Renderer
 *
 * Renders MessageEnvelope responses as structured toast-style notifications
 * instead of raw browser `alert()` calls. Falls back gracefully when the
 * response is a legacy plain-text error string.
 *
 * Usage:
 *   import { showEnvelope, showSuccess, showError, showMessage } from "./message-renderer.js";
 *   showEnvelope(envelopeOrError);        // auto-detects envelope vs legacy
 *   showSuccess("Trade executed", data);  // quick success toast
 *   showError("Something broke");         // quick error toast
 *   showMessage(entry);                   // render a MessageCenterEntry directly
 */

import { copySupportPackage } from "./support-package.js";
import { pushTimelineEntry } from "./operator-timeline.js";

/* ── Badge Helpers ─────────────────────────────────────────────────── */
function _severityLabel(severity) {
  switch (severity) {
    case "critical":
      return `<span class="message-severity-label" style="background:#dc3545;color:#fff;">⛔ CRITICAL</span>`;
    case "high":
      return `<span class="message-severity-label" style="background:#fd7e14;color:#fff;">⚠️ HIGH</span>`;
    case "medium":
      return `<span class="message-severity-label" style="background:#0dcaf0;color:#000;">ℹ️ MEDIUM</span>`;
    case "low":
      return `<span class="message-severity-label" style="background:#6c757d;color:#fff;">💡 LOW</span>`;
    default:
      return `<span class="message-severity-label" style="background:#198754;color:#fff;">✅ OK</span>`;
  }
}

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

  // T010: Use the message center container if it exists in the DOM
  const existing = document.getElementById("messageCenterContainer");
  if (existing) {
    _container = existing;
    return _container;
  }

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
function renderToast(html, style, autoCloseMs = 8000, envData = null) {
  const toast = document.createElement("div");
  toast.className = `msg-toast message-center-item ${style.customClass || ""}`.trim();
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

  // T011: Copy-to-clipboard for general data-copy buttons
  toast.querySelectorAll(".copy-btn[data-copy]").forEach((btn) => {
    const val = btn.getAttribute("data-copy");
    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      navigator.clipboard.writeText(val).then(() => {
        btn.textContent = "Copied!";
        setTimeout(() => { btn.textContent = "📋"; }, 1500);
      });
    });
  });

  // T012: Copy Support Package button
  toast.querySelectorAll(".copy-support-btn").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      if (envData) {
        copySupportPackage({
          tracking_id: envData.tracking_id,
          operation: envData.context?.operation || "unknown",
          symbol: envData.context?.symbol,
          direction: envData.context?.direction,
          volume: envData.context?.volume,
          readiness_status: envData.context?.readiness_status,
          error_code: envData.code,
          error_message: envData.message,
          timestamp: new Date().toISOString()
        });
      }
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
    `<div>${_severityLabel(env.severity)}</div>`,
    `<div style="font-weight:700;font-size:14px;margin-bottom:4px;margin-top:4px;">${style.icon} ${_esc(env.title)}</div>`,
    `<div>${_esc(env.message)}</div>`,
  ];

  if (env.action && env.action !== "No action required.") {
    parts.push(`<div style="margin-top:6px;font-style:italic;opacity:0.85;">💡 ${_esc(env.action)}</div>`);
  }

  if (env.tracking_id) {
    const tid = _esc(env.tracking_id);
    parts.push(
      `<div class="mono small">ID: <code>${tid}</code> ` +
      `<button class="copy-btn" data-copy="${tid}" title="Copy Tracking ID">📋</button></div>`
    );
  }

  // FR-019: Collapsible Details section showing context key-value pairs
  if (env.context && typeof env.context === "object" && Object.keys(env.context).length > 0) {
    parts.push(`<details class="mt-2"><summary class="small">Details</summary><pre class="small">${_esc(JSON.stringify(env.context, null, 2))}</pre></details>`);
  }

  // T013: Copy Support Package button for critical/high severity
  if (env.severity === "critical" || env.severity === "high") {
    parts.push(`<button class="btn btn-sm copy-support-btn mt-2">📋 Copy Support Package</button>`);
  }

  // T014: Failure messages (critical/high/medium) do not auto-close
  const autoClose = ["critical", "high", "medium"].includes(env.severity) ? 0 : 8000;

  const customClass = `severity-${env.severity || "medium"}`;
  renderToast(parts.join(""), { ...style, customClass }, autoClose, env);
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

/**
 * Render a MessageCenterEntry directly.
 * @param {object} entry
 */
export function showMessage(entry) {
  const env = {
    severity: entry.severity,
    title: entry.title,
    message: entry.message,
    action: entry.action,
    tracking_id: entry.tracking_id,
    context: entry.context,
    code: entry.code || null,
    ok: entry.severity === "success" || entry.severity === "low"
  };

  if (!("code" in env)) env.code = null;
  if (!("tracking_id" in env)) env.tracking_id = null;

  showEnvelope(env);
}
