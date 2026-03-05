/** MT5 Bridge — Shared Confirmation Modal (Phase 6). */

export function showConfirmationModal(config) {
  return new Promise((resolve) => {
    const previousFocus = document.activeElement;

    const {
      title,
      message,
      details,
      riskSummary,
      confirmLabel,
      cancelLabel = "Cancel",
      variant = "primary",
      requireCheckbox,
      checkboxLabel = "I understand this action is irreversible"
    } = config;

    const overlay = document.createElement("div");
    overlay.className = "confirmation-modal-overlay";

    const modal = document.createElement("div");
    modal.className = "confirmation-modal";
    modal.setAttribute("role", "dialog");
    modal.setAttribute("aria-modal", "true");
    modal.setAttribute("aria-labelledby", "modal-title");
    modal.setAttribute("aria-describedby", "modal-desc");

    const titleEl = document.createElement("h4");
    titleEl.id = "modal-title";
    titleEl.textContent = title;
    modal.appendChild(titleEl);

    const descEl = document.createElement("p");
    descEl.id = "modal-desc";
    descEl.textContent = message;
    modal.appendChild(descEl);

    if (details && details.length > 0) {
      const detailsEl = document.createElement("div");
      detailsEl.className = "confirmation-modal-details";
      details.forEach(d => {
        const labelEl = document.createElement("span");
        labelEl.className = "detail-label";
        labelEl.textContent = `${d.label}:`;
        const valueEl = document.createElement("span");
        valueEl.className = "detail-value";
        valueEl.textContent = d.value;
        detailsEl.appendChild(labelEl);
        detailsEl.appendChild(document.createTextNode(" "));
        detailsEl.appendChild(valueEl);
        detailsEl.appendChild(document.createElement("br"));
      });
      modal.appendChild(detailsEl);
    }

    if (riskSummary) {
      const riskEl = document.createElement("div");
      riskEl.className = "confirmation-modal-risk";
      riskEl.textContent = `⚠️ ${riskSummary}`;
      modal.appendChild(riskEl);
    }

    let checkbox = null;
    if (requireCheckbox) {
      const labelEl = document.createElement("label");
      labelEl.className = "confirm-checkbox";
      checkbox = document.createElement("input");
      checkbox.type = "checkbox";
      checkbox.id = "modalConfirmCheckbox";
      labelEl.appendChild(checkbox);
      labelEl.appendChild(document.createTextNode(` ${checkboxLabel || "I understand this action is irreversible"}`));
      modal.appendChild(labelEl);
    }

    const actionsEl = document.createElement("div");
    actionsEl.className = "confirmation-modal-actions";

    const cancelBtn = document.createElement("button");
    cancelBtn.className = "btn btn-secondary";
    cancelBtn.id = "modalCancelBtn";
    cancelBtn.textContent = cancelLabel;

    const confirmBtn = document.createElement("button");
    // fallback variant is primary if not provided or default
    const validVariant = (variant && variant !== 'default') ? variant : 'primary';
    confirmBtn.className = `btn btn-${validVariant}`;
    confirmBtn.id = "modalConfirmBtn";
    confirmBtn.textContent = confirmLabel;

    if (requireCheckbox) {
      confirmBtn.disabled = true;
      checkbox.addEventListener("change", () => {
        confirmBtn.disabled = !checkbox.checked;
      });
    }

    actionsEl.appendChild(cancelBtn);
    actionsEl.appendChild(confirmBtn);
    modal.appendChild(actionsEl);

    overlay.appendChild(modal);

    const modalRoot = document.getElementById("modalRoot") || document.body;
    modalRoot.appendChild(overlay);

    const cleanup = () => {
      document.removeEventListener("keydown", handleKeydown);
      overlay.remove();
      if (previousFocus && typeof previousFocus.focus === 'function') {
        previousFocus.focus();
      }
    };

    const handleConfirm = () => {
      if (confirmBtn.disabled) return;
      cleanup();
      resolve(true);
    };

    const handleCancel = () => {
      cleanup();
      resolve(false);
    };

    cancelBtn.addEventListener("click", handleCancel);
    confirmBtn.addEventListener("click", handleConfirm);

    const handleKeydown = (e) => {
      if (e.key === "Escape") {
        e.preventDefault();
        handleCancel();
      } else if (e.key === "Enter") {
        if (document.activeElement === confirmBtn) {
          e.preventDefault();
          handleConfirm();
        }
      } else if (e.key === "Tab") {
        const focusableElements = modal.querySelectorAll(
          'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );
        if (focusableElements.length === 0) return;
        
        const firstElement = focusableElements[0];
        const lastElement = focusableElements[focusableElements.length - 1];

        if (e.shiftKey) {
          if (document.activeElement === firstElement) {
            e.preventDefault();
            lastElement.focus();
          }
        } else {
          if (document.activeElement === lastElement) {
            e.preventDefault();
            firstElement.focus();
          }
        }
      }
    };

    document.addEventListener("keydown", handleKeydown);

    // Initial focus
    cancelBtn.focus();
  });
}
