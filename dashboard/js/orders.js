import { api } from "./app.js";
import { showEnvelope, showSuccess } from "./message-renderer.js";
import { renderReadinessPanel, isReadinessBlocked } from "./readiness.js";
import { showConfirmationModal } from "./confirmation-modal.js";

function isGuardedDuplicateError(err) {
  const message = String(err?.message || "");
  return message.includes("Single-flight mode active") || message.includes("Execution queue overload protection");
}

export function renderOrders(contentEl, payload) {
  const orders = payload?.orders || [];
  let html = `
    <h3>Pending Orders</h3>
    <div class="card-actions mt-2">
      <button class="btn btn-danger btn-sm" id="cancelAllBtn">Cancel All</button>
    </div>
    <div class="grid two mt-4">
  `;

  if (orders.length === 0) {
    html += `<p>No pending orders found.</p>`;
  } else {
    orders.forEach((order) => {
      let typeClass = "";
      if (order.type.includes("buy")) {
        typeClass = "text-green";
      }
      if (order.type.includes("sell")) {
        typeClass = "text-red";
      }

      html += `
        <article class="card">
          <h4>${order.symbol}</h4>
          <p><strong>Type:</strong> <span class="${typeClass}">${order.type.replace("_", " ").toUpperCase()}</span></p>
          <p><strong>Volume:</strong> ${order.volume}</p>
          <p><strong>Trigger Price:</strong> ${order.price}</p>
          <p><strong>SL:</strong> ${order.sl || "-"}</p>
          <p><strong>TP:</strong> ${order.tp || "-"}</p>
          <p><strong>Setup Time:</strong> ${order.time_setup}</p>
          <div class="card-actions mt-2">
            <button class="btn btn-sm btn-danger cancel-ord-btn" data-ticket="${order.ticket}" data-symbol="${order.symbol}" data-vol="${order.volume}" data-type="${order.type}" data-price="${order.price}">Cancel</button>
            <button class="btn btn-sm btn-secondary toggle-mod-ord-btn" data-ticket="${order.ticket}">Modify</button>
          </div>
          <div id="mod-ord-form-${order.ticket}" class="hidden mod-ord-form mt-2 p-2 bg-gray-100 rounded">
            <div>
              <label>Price:</label>
              <input type="number" id="mod-ord-price-${order.ticket}" value="${order.price}" step="0.00001">
            </div>
            <div class="mt-2">
              <label>Stop Loss:</label>
              <input type="number" id="mod-ord-sl-${order.ticket}" value="${order.sl || 0}" step="0.00001">
            </div>
            <div class="mt-2">
              <label>Take Profit:</label>
              <input type="number" id="mod-ord-tp-${order.ticket}" value="${order.tp || 0}" step="0.00001">
            </div>
            <button class="btn btn-sm btn-primary submit-mod-ord-btn mt-2" data-ticket="${order.ticket}">Submit Modify</button>
          </div>
        </article>
      `;
    });
  }

  html += `</div>`;
  contentEl.innerHTML = html;

  // T026: Render readiness panel before orders grid
  const readinessPanel = document.createElement("div");
  readinessPanel.id = "orders-readiness-panel";
  const gridEl = contentEl.querySelector(".grid");
  contentEl.insertBefore(readinessPanel, gridEl);
  renderReadinessPanel(readinessPanel, { operation: "cancel_order" });

  // T031: Listen for readiness acknowledgment changes
  contentEl.addEventListener("readiness-ack-change", () => {
    const isBlocked = isReadinessBlocked();
    contentEl.querySelectorAll(".cancel-ord-btn").forEach((btn) => {
      btn.disabled = isBlocked;
    });
    const cancelAllBtn = document.getElementById("cancelAllBtn");
    if (cancelAllBtn) cancelAllBtn.disabled = isBlocked;
  });

  const cancelOrderByTicket = async (ticket) => {
    return api(`/orders/${ticket}`, { method: "DELETE" });
  };

  contentEl.querySelectorAll(".cancel-ord-btn").forEach((btn) => {
    btn.addEventListener("click", async (e) => {
      const target = e.currentTarget;
      const ticket = target.getAttribute("data-ticket");
      const symbol = target.getAttribute("data-symbol");
      const volume = target.getAttribute("data-vol");
      const type = target.getAttribute("data-type");
      const price = target.getAttribute("data-price");

      const approved = await showConfirmationModal({
        title: "Confirm Cancel Order",
        message: "You are about to cancel a pending order. This action is irreversible.",
        details: [
          { label: "Symbol", value: symbol },
          { label: "Ticket", value: ticket },
          { label: "Type", value: type.replace("_", " ").toUpperCase() },
          { label: "Volume", value: volume },
          { label: "Price", value: price }
        ],
        confirmLabel: "Cancel Order",
        variant: "danger"
      });
      if (!approved) {
        return;
      }

      // T030: Check readiness before cancel
      if (isReadinessBlocked()) {
        showEnvelope({
          category: "system",
          severity: "critical",
          title: "Operation Blocked",
          message: "Readiness checks failed. Cannot proceed with cancelling order.",
        });
        return;
      }

      target.disabled = true;
      try {
        await cancelOrderByTicket(ticket);
        showSuccess(`Successfully cancelled order ${ticket}`);
      } catch (err) {
        if (!isGuardedDuplicateError(err)) {
          showEnvelope(err.envelope || err);
        }
      } finally {
        target.disabled = false;
      }
    });
  });

  document.getElementById("cancelAllBtn")?.addEventListener("click", async () => {
    const cancelAllBtn = document.getElementById("cancelAllBtn");
    if (!orders.length) {
      return;
    }
    const confirmed = await showConfirmationModal({
      title: "Cancel All Pending Orders",
      message: `You are about to cancel ${orders.length} pending order(s).`,
      requireCheckbox: true,
      checkboxLabel: "I understand this action is irreversible.",
      confirmLabel: "Cancel All",
      variant: "danger"
    });
    if (!confirmed) {
      return;
    }

    cancelAllBtn.disabled = true;
    let successCount = 0;
    for (const order of orders) {
      try {
        await cancelOrderByTicket(order.ticket);
        successCount += 1;
      } catch (err) {
        if (!isGuardedDuplicateError(err)) {
          console.error(`Cancel failed for order ${order.ticket}`, err);
        }
      }
    }
    cancelAllBtn.disabled = false;
    showSuccess(`Cancel-all completed. Success: ${successCount}/${orders.length}`);
  });

  contentEl.querySelectorAll(".toggle-mod-ord-btn").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      const ticket = e.currentTarget.getAttribute("data-ticket");
      const form = document.getElementById(`mod-ord-form-${ticket}`);
      form.classList.toggle("hidden");
    });
  });

  contentEl.querySelectorAll(".submit-mod-ord-btn").forEach((btn) => {
    btn.addEventListener("click", async (e) => {
      const ticket = e.currentTarget.getAttribute("data-ticket");
      const priceVal = Number(document.getElementById(`mod-ord-price-${ticket}`).value);
      const slVal = Number(document.getElementById(`mod-ord-sl-${ticket}`).value);
      const tpVal = Number(document.getElementById(`mod-ord-tp-${ticket}`).value);

      try {
        await api(`/orders/${ticket}`, {
          method: "PUT",
          body: JSON.stringify({
            price: Number.isFinite(priceVal) && priceVal > 0 ? priceVal : null,
            sl: Number.isFinite(slVal) && slVal > 0 ? slVal : null,
            tp: Number.isFinite(tpVal) && tpVal > 0 ? tpVal : null,
          }),
        });
        showSuccess(`Successfully modified order ${ticket}`);
      } catch (err) {
        showEnvelope(err.envelope || err);
      }
    });
  });
}
