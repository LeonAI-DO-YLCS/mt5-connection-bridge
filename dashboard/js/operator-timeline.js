/** MT5 Bridge — Operator Timeline (Phase 6). */

let _entries = [];

try {
  const stored = sessionStorage.getItem("mt5_timeline");
  if (stored) {
    _entries = JSON.parse(stored);
    if (!Array.isArray(_entries)) {
      _entries = [];
    }
  }
} catch (e) {
  _entries = [];
}

export function pushTimelineEntry(entry) {
  _entries.unshift(entry);
  if (_entries.length > 50) {
    _entries.pop();
  }
  try {
    sessionStorage.setItem("mt5_timeline", JSON.stringify(_entries));
  } catch (e) {
    // Ignore storage errors
  }
}

export function getTimelineEntries() {
  return [..._entries];
}

export function renderTimeline(containerEl) {
  if (!containerEl) return;
  containerEl.innerHTML = "";

  if (_entries.length === 0) {
    const emptyMsg = document.createElement("p");
    emptyMsg.className = "text-muted";
    emptyMsg.textContent = "No operations yet in this session.";
    containerEl.appendChild(emptyMsg);
    
    // Still render the clear button (or we could choose not to, but the prompt says to render it "at the bottom")
    const clearBtn = document.createElement("button");
    clearBtn.className = "btn btn-secondary";
    clearBtn.style.marginTop = "10px";
    clearBtn.textContent = "Clear Timeline";
    clearBtn.addEventListener("click", () => {
      _entries = [];
      try {
        sessionStorage.removeItem("mt5_timeline");
      } catch (e) {}
      renderTimeline(containerEl);
    });
    containerEl.appendChild(clearBtn);
    return;
  }

  _entries.forEach(entry => {
    const div = document.createElement("div");
    div.className = "timeline-entry";
    
    const icon = entry.outcome === "success" ? "✅" : "❌";
    
    div.innerHTML = `
      ${icon}
      <span class="outcome-${entry.outcome}">${entry.action}</span>
      <span class="mono text-muted">${entry.code || "—"}</span>
      <span class="mono small">${entry.tracking_id ? entry.tracking_id.slice(0, 12) + "…" : "—"}</span>
      <span class="text-muted small">${new Date(entry.timestamp).toLocaleTimeString()}</span>
    `;
    containerEl.appendChild(div);
  });

  const clearBtn = document.createElement("button");
  clearBtn.className = "btn btn-secondary";
  clearBtn.style.marginTop = "10px";
  clearBtn.textContent = "Clear Timeline";
  clearBtn.addEventListener("click", () => {
    _entries = [];
    try {
      sessionStorage.removeItem("mt5_timeline");
    } catch (e) {}
    renderTimeline(containerEl);
  });
  
  containerEl.appendChild(clearBtn);
}
