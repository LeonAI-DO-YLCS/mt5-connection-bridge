/** MT5 Bridge — Support Package Clipboard Helper (Phase 6). */

export async function copySupportPackage(data) {
  const {
    tracking_id,
    operation,
    symbol,
    direction,
    volume,
    readiness_status,
    error_code,
    error_message,
    timestamp
  } = data;

  const text = `--- MT5 Bridge Support Package ---
Tracking ID   : ${tracking_id}
Operation     : ${operation}
Symbol        : ${symbol || "N/A"}
Direction     : ${direction || "N/A"}
Volume        : ${volume || "N/A"}
Readiness     : ${readiness_status || "N/A"}
Error Code    : ${error_code || "N/A"}
Error Message : ${error_message || "N/A"}
Timestamp     : ${timestamp}
----------------------------------`;

  try {
    await navigator.clipboard.writeText(text);
    return { success: true };
  } catch (err) {
    const overlay = document.createElement("div");
    overlay.className = "confirmation-modal-overlay";
    overlay.style.zIndex = "10000";

    const modal = document.createElement("div");
    modal.className = "confirmation-modal";

    const titleEl = document.createElement("h4");
    titleEl.textContent = "Support Package";
    modal.appendChild(titleEl);

    const descEl = document.createElement("p");
    descEl.textContent = "Could not copy automatically. Please copy the text below:";
    modal.appendChild(descEl);

    const textarea = document.createElement("textarea");
    textarea.readOnly = true;
    textarea.value = text;
    textarea.style.width = "100%";
    textarea.style.height = "200px";
    textarea.style.fontFamily = "monospace";
    modal.appendChild(textarea);

    const actionsEl = document.createElement("div");
    actionsEl.className = "confirmation-modal-actions";

    const closeBtn = document.createElement("button");
    closeBtn.className = "btn btn-secondary";
    closeBtn.textContent = "Close";
    closeBtn.addEventListener("click", () => {
      overlay.remove();
    });

    actionsEl.appendChild(closeBtn);
    modal.appendChild(actionsEl);
    overlay.appendChild(modal);
    document.body.appendChild(overlay);

    textarea.select();

    return { success: false, fallback: true };
  }
}
