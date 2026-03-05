import { api } from "./app.js";
import { showEnvelope, showSuccess, showError } from "./message-renderer.js";
import { renderReadinessPanel, isReadinessBlocked, isReadinessDegraded, isWarningAcknowledged } from "./readiness.js";
import { showConfirmationModal } from "./confirmation-modal.js";

function isGuardedDuplicateError(err) {
  const message = String(err?.message || "");
  return message.includes("Single-flight mode active") || message.includes("Execution queue overload protection");
}

async function fetchVolumeConstraints(positionSymbol, positionVolume) {
  try {
    const [configured, broker] = await Promise.all([
      api("/symbols").catch(() => ({ symbols: [] })),
      api("/broker-symbols").catch(() => ({ symbols: [] })),
    ]);

    const configuredSymbols = configured?.symbols || [];
    const brokerSymbols = broker?.symbols || [];
    const configuredMatch = configuredSymbols.find(
      (s) => s.ticker === positionSymbol || s.mt5_symbol === positionSymbol,
    );
    const mt5Name = configuredMatch?.mt5_symbol || positionSymbol;
    const brokerMatch = brokerSymbols.find((s) => s.name === mt5Name);

    const step = Number(configuredMatch?.lot_size) || Number(brokerMatch?.volume_min) || 0.01;
    const min = Number(brokerMatch?.volume_min) || step;
    const max = Math.min(Number(brokerMatch?.volume_max) || Number(positionVolume), Number(positionVolume));
    return { step, min, max };
  } catch {
    return { step: 0.01, min: 0.01, max: Number(positionVolume) };
  }
}

function isStepAligned(value, min, step) {
  if (!Number.isFinite(step) || step <= 0) {
    return true;
  }
  const ratio = (value - min) / step;
  return Math.abs(ratio - Math.round(ratio)) < 1e-9;
}

function parsePartialCloseVolume(positionVolume, constraints) {
  const raw = prompt(
    `Enter volume to close (blank for full close).\nCurrent position volume: ${positionVolume}\nAllowed: ${constraints.min}-${constraints.max} (step ${constraints.step})`,
    "",
  );
  if (raw === null) {
    return { cancelled: true };
  }
  if (raw.trim() === "") {
    return { cancelled: false, volume: null };
  }
  const volume = Number(raw);
  if (!Number.isFinite(volume) || volume <= 0 || volume > Number(positionVolume)) {
    return { cancelled: false, error: "Invalid partial-close volume." };
  }
  if (volume < constraints.min || volume > constraints.max) {
    return {
      cancelled: false,
      error: `Volume must be between ${constraints.min} and ${constraints.max}.`,
    };
  }
  if (!isStepAligned(volume, constraints.min > 0 ? constraints.min : 0, constraints.step)) {
    return {
      cancelled: false,
      error: `Volume must follow step size ${constraints.step} from minimum ${constraints.min}.`,
    };
  }
  return { cancelled: false, volume };
}

export function renderPositions(contentEl, payload, accountPayload) {
  const accountPnl = Number(accountPayload?.profit || 0);
  const pnlClass = accountPnl >= 0 ? "text-green" : "text-red";
  const positions = payload?.positions || [];

  let html = `
    <h3>Open Positions</h3>
    <div class="summary-bar">
      <strong>Total Unrealized P&L:</strong>
      <span class="${pnlClass}">${accountPnl.toFixed(2)}</span>
    </div>
    <div class="card-actions mt-2">
      <button class="btn btn-danger btn-sm" id="closeAllBtn">Close All</button>
    </div>
    <div class="grid two mt-4">
  `;

  if (positions.length === 0) {
    html += `<p>No open positions found.</p>`;
  } else {
    positions.forEach((pos) => {
      const typeClass = pos.type === "buy" ? "text-green" : "text-red";
      const posPnlClass = Number(pos.profit) >= 0 ? "text-green" : "text-red";

      html += `
        <article class="card">
          <h4>${pos.symbol}</h4>
          <p><strong>Type:</strong> <span class="${typeClass}">${pos.type.toUpperCase()}</span></p>
          <p><strong>Volume:</strong> ${pos.volume}</p>
          <p><strong>Entry Price:</strong> ${pos.price_open}</p>
          <p><strong>Current Price:</strong> ${pos.price_current}</p>
          <p><strong>P&L:</strong> <span class="${posPnlClass}">${Number(pos.profit).toFixed(2)}</span></p>
          <p><strong>SL:</strong> ${pos.sl || "-"}</p>
          <p><strong>TP:</strong> ${pos.tp || "-"}</p>
          <p><strong>Swap:</strong> ${pos.swap}</p>
          <div class="card-actions mt-2">
            <button class="btn btn-sm btn-danger close-pos-btn" data-ticket="${pos.ticket}" data-symbol="${pos.symbol}" data-vol="${pos.volume}" data-type="${pos.type}">Close</button>
            <button class="btn btn-sm btn-secondary toggle-mod-pos-btn" data-ticket="${pos.ticket}">Modify SL/TP</button>
          </div>
          <div id="mod-pos-form-${pos.ticket}" class="hidden mod-pos-form mt-2 p-2 bg-gray-100 rounded">
            <div>
              <label>Stop Loss:</label>
              <input type="number" id="mod-pos-sl-${pos.ticket}" value="${pos.sl || 0}" step="0.00001">
            </div>
            <div class="mt-2">
              <label>Take Profit:</label>
              <input type="number" id="mod-pos-tp-${pos.ticket}" value="${pos.tp || 0}" step="0.00001">
            </div>
            <button class="btn btn-sm btn-primary submit-mod-pos-btn mt-2" data-ticket="${pos.ticket}">Submit Modify</button>
          </div>
        </article>
      `;
    });
  }

  html += `</div>`;
  contentEl.innerHTML = html;

  // T025: Render readiness panel before positions grid
  const readinessPanel = document.createElement("div");
  readinessPanel.id = "positions-readiness-panel";
  const gridEl = contentEl.querySelector(".grid");
  contentEl.insertBefore(readinessPanel, gridEl);
  renderReadinessPanel(readinessPanel, { operation: "close_position" });

  // T031: Listen for readiness acknowledgment changes
  contentEl.addEventListener("readiness-ack-change", () => {
    const isBlocked = isReadinessBlocked();
    contentEl.querySelectorAll(".close-pos-btn").forEach((btn) => {
      btn.disabled = isBlocked;
    });
    const closeAllBtn = document.getElementById("closeAllBtn");
    if (closeAllBtn) closeAllBtn.disabled = isBlocked;
  });

  const closePositionByTicket = async (ticket, volume) => {
    const body = { ticket: Number(ticket) };
    if (volume !== null && volume !== undefined) {
      body.volume = Number(volume);
    }
    return api("/close-position", {
      method: "POST",
      body: JSON.stringify(body),
    });
  };

  contentEl.querySelectorAll(".close-pos-btn").forEach((btn) => {
    btn.addEventListener("click", async (e) => {
      const target = e.currentTarget;
      const ticket = target.getAttribute("data-ticket");
      const symbol = target.getAttribute("data-symbol");
      const volume = target.getAttribute("data-vol");
      const type = target.getAttribute("data-type");

      target.disabled = true;
      const constraints = await fetchVolumeConstraints(symbol, volume);
      const parsed = parsePartialCloseVolume(volume, constraints);
      if (parsed.cancelled) {
        target.disabled = false;
        return;
      }
      if (parsed.error) {
        showError(parsed.error);
        target.disabled = false;
        return;
      }

      // T028: Check readiness before close
      if (isReadinessBlocked()) {
        showEnvelope({
          category: "system",
          severity: "critical",
          title: "Operation Blocked",
          message: "Readiness checks failed. Cannot proceed with closing position.",
        });
        target.disabled = false;
        return;
      }

      if (isReadinessDegraded() && !isWarningAcknowledged()) {
        showEnvelope({
          category: "system",
          severity: "warning",
          title: "Warnings Not Acknowledged",
          message: "You must acknowledge the warnings before proceeding.",
        });
        target.disabled = false;
        return;
      }

      const closeVolume = parsed.volume === null ? volume : parsed.volume;
      const approved = await showConfirmationModal({
        title: "Confirm Close Position",
        message: "You are about to close a position. This action is irreversible.",
        details: [
          { label: "Symbol", value: symbol },
          { label: "Ticket", value: ticket },
          { label: "Volume", value: closeVolume },
          { label: "Direction", value: type }
        ],
        riskSummary: "Closing this position will realize any unrealized P&L.",
        confirmLabel: "Close Position",
        variant: "danger",
        requireCheckbox: true
      });
      if (!approved) {
        target.disabled = false;
        return;
      }

      try {
        await closePositionByTicket(ticket, parsed.volume);
        showSuccess(`Close request accepted for position ${ticket}`);
      } catch (err) {
        if (!isGuardedDuplicateError(err)) {
          showEnvelope(err.envelope || err);
        }
      } finally {
        target.disabled = false;
      }
    });
  });

  document.getElementById("closeAllBtn")?.addEventListener("click", async () => {
    const closeAllBtn = document.getElementById("closeAllBtn");
    if (!positions.length) {
      return;
    }
    const confirmed = await showConfirmationModal({
      title: "Close All Positions",
      message: `You are about to close ${positions.length} open position(s).`,
      checkboxLabel: "I understand this action is irreversible.",
      confirmLabel: "Close All",
      variant: "danger",
      requireCheckbox: true
    });
    if (!confirmed) {
      return;
    }

    closeAllBtn.disabled = true;
    let successCount = 0;
    for (const pos of positions) {
      try {
        await closePositionByTicket(pos.ticket, null);
        successCount += 1;
      } catch (err) {
        if (!isGuardedDuplicateError(err)) {
          console.error(`Close failed for position ${pos.ticket}`, err);
        }
      }
    }
    closeAllBtn.disabled = false;
    showSuccess(`Close-all completed. Success: ${successCount}/${positions.length}`);
  });

  contentEl.querySelectorAll(".toggle-mod-pos-btn").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      const ticket = e.currentTarget.getAttribute("data-ticket");
      const form = document.getElementById(`mod-pos-form-${ticket}`);
      form.classList.toggle("hidden");
    });
  });

  contentEl.querySelectorAll(".submit-mod-pos-btn").forEach((btn) => {
    btn.addEventListener("click", async (e) => {
      const ticket = e.currentTarget.getAttribute("data-ticket");
      const slVal = Number(document.getElementById(`mod-pos-sl-${ticket}`).value);
      const tpVal = Number(document.getElementById(`mod-pos-tp-${ticket}`).value);

      try {
        await api(`/positions/${ticket}/sltp`, {
          method: "PUT",
          body: JSON.stringify({
            sl: Number.isFinite(slVal) && slVal > 0 ? slVal : null,
            tp: Number.isFinite(tpVal) && tpVal > 0 ? tpVal : null,
          }),
        });
        showSuccess(`Successfully modified position ${ticket}`);
      } catch (err) {
        showEnvelope(err.envelope || err);
      }
    });
  });
}
