/**
 * MT5 Bridge Dashboard — Execute Tab
 * Feature 008: Adaptive Broker Capabilities
 *
 * Changes:
 *  T032: Ticker dropdown populated from /broker-capabilities (optgroup categories)
 *  T033: Client-side symbol search filter
 *  T034: Trade mode badge displayed next to each symbol
 *  T035: Buy/Sell buttons disabled & annotated for restricted trade modes
 *  T036: mt5_symbol_direct sent in payload when broker-native symbol is selected
 */
import { api } from "./app.js";

let checkTimeout = null;
let _capabilitiesCache = null;

const TRADE_MODE_LABELS = {
  0: { label: "Disabled", color: "#dc3545", icon: "🚫" },
  1: { label: "Long Only", color: "#fd7e14", icon: "📈" },
  2: { label: "Short Only", color: "#6610f2", icon: "📉" },
  3: { label: "Close Only", color: "#6c757d", icon: "🔒" },
  4: { label: "Full", color: "#198754", icon: "✅" },
};

function roundToStep(value, step) {
  const precision = step.toString().includes(".") ? step.toString().split(".")[1].length : 0;
  const rounded = Math.round(value / step) * step;
  return Number(rounded.toFixed(precision));
}

/** T034: Build a colored trade mode badge HTML */
function tradeModeBadge(mode) {
  const info = TRADE_MODE_LABELS[mode] ?? TRADE_MODE_LABELS[4];
  return `<span style="
    display:inline-block;
    padding:1px 6px;
    border-radius:4px;
    font-size:11px;
    background:${info.color}22;
    color:${info.color};
    border:1px solid ${info.color};
    margin-left:6px;">${info.icon} ${info.label}</span>`;
}

export async function renderExecute(contentEl) {
  let latestTick = null;

  const brokerMeta = new Map(); // mt5 symbol name -> capabilities symbol object

  contentEl.innerHTML = `
    <h3>Execute Trade / Pending Order</h3>
    <div class="card" style="max-width: 600px">
      <form id="executeForm" onsubmit="return false;">
        <div class="mt-2">
          <label>Type:</label>
          <select id="execType" class="bg-gray-100 p-2 rounded w-full">
            <option value="buy">Market Buy</option>
            <option value="sell">Market Sell</option>
            <option value="buy_limit">Buy Limit</option>
            <option value="sell_limit">Sell Limit</option>
            <option value="buy_stop">Buy Stop</option>
            <option value="sell_stop">Sell Stop</option>
          </select>
        </div>

        <div class="mt-2">
          <label>Symbol:</label>
          <div style="position:relative;">
            <!-- T033: symbol search filter -->
            <input type="text" id="symbolSearch"
              placeholder="Search symbols…"
              class="bg-gray-100 p-2 rounded w-full"
              style="margin-bottom:4px;"
              autocomplete="off">
            <select id="execTicker" class="bg-gray-100 p-2 rounded w-full" size="1">
              <option value="">Select Symbol…</option>
            </select>
          </div>
          <!-- T034: trade mode badge + price display -->
          <div id="execTradeModeBadge" style="margin-top:4px;min-height:22px;"></div>
          <div id="execPriceDisplay" class="small mt-1 text-muted"></div>
          <!-- T035: restriction hint for disabled actions -->
          <div id="execTradeRestriction"
            style="color:#dc3545;font-size:12px;margin-top:4px;display:none;"></div>
        </div>

        <div class="mt-2">
          <label>Volume:</label>
          <input type="number" id="execVolume" value="0.01" step="0.01" min="0.01"
            class="bg-gray-100 p-2 rounded w-full">
          <div id="volumeHint" class="small mt-1"></div>
        </div>

        <div class="mt-2" id="execPriceGroup" style="display: none;">
          <label>Trigger Price (Pending Only):</label>
          <input type="number" id="execPrice" step="0.00001" class="bg-gray-100 p-2 rounded w-full">
        </div>

        <div class="mt-2">
          <label>Stop Loss (Optional):</label>
          <input type="number" id="execSL" step="0.00001" class="bg-gray-100 p-2 rounded w-full">
        </div>

        <div class="mt-2">
          <label>Take Profit (Optional):</label>
          <input type="number" id="execTP" step="0.00001" class="bg-gray-100 p-2 rounded w-full">
        </div>

        <div class="mt-2">
          <label>Comment:</label>
          <input type="text" id="execComment" class="bg-gray-100 p-2 rounded w-full">
        </div>

        <div id="validationPanel" class="mt-4 p-2 rounded bg-gray-100 hidden">
          <strong id="valStatusIcon"></strong> <span id="valStatusText"></span>
          <div class="small mt-1">
            <div>Margin Req: <span id="valMargin"></span></div>
            <div>Est. Profit: <span id="valProfit"></span></div>
            <div>Post-Trade Equity: <span id="valEquity"></span></div>
            <div class="text-muted" id="valComment"></div>
          </div>
        </div>

        <button id="execSubmitBtn" class="btn btn-primary mt-4 w-full">Submit</button>
      </form>
    </div>
  `;

  const execType = document.getElementById("execType");
  const execTicker = document.getElementById("execTicker");
  const symbolSearch = document.getElementById("symbolSearch");
  const execPriceGroup = document.getElementById("execPriceGroup");
  const execVolume = document.getElementById("execVolume");
  const execPrice = document.getElementById("execPrice");
  const execSL = document.getElementById("execSL");
  const execTP = document.getElementById("execTP");
  const execComment = document.getElementById("execComment");
  const execPriceDisplay = document.getElementById("execPriceDisplay");
  const execTradeModeBadge = document.getElementById("execTradeModeBadge");
  const execTradeRestriction = document.getElementById("execTradeRestriction");
  const volumeHint = document.getElementById("volumeHint");

  const valPanel = document.getElementById("validationPanel");
  const valStatusIcon = document.getElementById("valStatusIcon");
  const valStatusText = document.getElementById("valStatusText");
  const valMargin = document.getElementById("valMargin");
  const valProfit = document.getElementById("valProfit");
  const valEquity = document.getElementById("valEquity");
  const valComment = document.getElementById("valComment");
  const execSubmitBtn = document.getElementById("execSubmitBtn");

  // ----------------------------------------------------------------------
  // T035–T037: capabilities-driven dropdown + client-side search filter
  // ----------------------------------------------------------------------
  function populateTickerDropdown() {
    if (!_capabilitiesCache) {
      execTicker.innerHTML = `<option value="">Select Symbol…</option>`;
      return;
    }

    const categories = _capabilitiesCache.categories || {};
    const symbols = _capabilitiesCache.symbols || [];
    const symbolsByCategory = new Map();

    symbols
      .filter((symbol) => Number(symbol.trade_mode) !== 0)
      .forEach((symbol) => {
        const category = symbol.category || "Other";
        if (!symbolsByCategory.has(category)) {
          symbolsByCategory.set(category, []);
        }
        symbolsByCategory.get(category).push(symbol);
      });

    let html = `<option value="">Select Symbol…</option>`;
    Object.keys(categories).sort().forEach((category) => {
      const categorySymbols = symbolsByCategory.get(category) || [];
      if (categorySymbols.length === 0) {
        return;
      }
      html += `<optgroup label="${category}">`;
      categorySymbols.forEach((symbol) => {
        const modeLabel = TRADE_MODE_LABELS[symbol.trade_mode]?.label ?? "Full";
        html += `<option value="${symbol.name}" data-mode="${symbol.trade_mode}" data-broker="true">`;
        html += `${symbol.name} — ${symbol.description.slice(0, 40)} [${modeLabel}]`;
        html += `</option>`;
      });
      html += `</optgroup>`;
    });

    execTicker.innerHTML = html;
  }

  function filterSymbolDropdown(query) {
    const normalized = (query || "").toLowerCase().trim();
    Array.from(execTicker.options).forEach((option) => {
      if (!option.value) {
        option.hidden = false;
        return;
      }
      const symbol = brokerMeta.get(option.value);
      const haystack = `${option.textContent} ${(symbol?.description || "")}`.toLowerCase();
      option.hidden = normalized ? !haystack.includes(normalized) : false;
    });
  }

  try {
    _capabilitiesCache = await api("/broker-capabilities").catch(() => ({ symbols: [], categories: {} }));
    (_capabilitiesCache.symbols || []).forEach((symbol) => brokerMeta.set(symbol.name, symbol));
    populateTickerDropdown();
  } catch (err) {
    execPriceDisplay.textContent = `Failed to load symbols: ${err.message}`;
  }

  symbolSearch.addEventListener("input", () => {
    filterSymbolDropdown(symbolSearch.value);
  });

  // ----------------------------------------------------------------------
  // T038/T039: Trade mode enforcement helpers
  // ----------------------------------------------------------------------
  function getCurrentBrokerInfo() {
    const val = execTicker.value;
    if (!val) return null;
    return brokerMeta.get(val) ?? null;
  }

  function renderTradeModeWarning(symbol) {
    const mode = Number(symbol?.trade_mode ?? 4);
    const modeLabel = symbol?.trade_mode_label || (TRADE_MODE_LABELS[mode]?.label ?? "Full");
    if (mode === 0) {
      execTradeRestriction.style.display = "block";
      execTradeRestriction.textContent = `⚠️ ${symbol.name} is in ${modeLabel} mode. Trading is disabled by broker policy.`;
      return true;
    }
    if (mode === 3) {
      execTradeRestriction.style.display = "block";
      execTradeRestriction.textContent = `⚠️ ${symbol.name} is in ${modeLabel} mode. No new positions are allowed.`;
      return true;
    }
    execTradeRestriction.style.display = "none";
    execTradeRestriction.textContent = "";
    return false;
  }

  function onSymbolSelect(symbolName) {
    const symbol = brokerMeta.get(symbolName) || null;
    const mode = Number(symbol?.trade_mode ?? 4);
    const info = TRADE_MODE_LABELS[mode] ?? TRADE_MODE_LABELS[4];

    const buyRestricted = mode === 2 || mode === 3;
    const sellRestricted = mode === 1 || mode === 3;

    Array.from(execType.options).forEach((option) => {
      const value = option.value;
      const isBuyType = ["buy", "buy_limit", "buy_stop"].includes(value);
      const isSellType = ["sell", "sell_limit", "sell_stop"].includes(value);
      const disabled = (isBuyType && buyRestricted) || (isSellType && sellRestricted) || mode === 0;
      option.disabled = disabled;
      option.title = disabled ? `${info.label}: ${symbol?.name || symbolName} restricts this direction.` : "";
    });
  }

  function applyTradeModeUI() {
    const brokerInfo = getCurrentBrokerInfo();
    const mode = brokerInfo?.trade_mode ?? 4;
    const info = TRADE_MODE_LABELS[mode] ?? TRADE_MODE_LABELS[4];
    const action = execType.value;

    execTradeModeBadge.innerHTML = brokerInfo ? tradeModeBadge(mode) : "";
    if (brokerInfo) {
      onSymbolSelect(brokerInfo.name);
    }

    // Action-level restriction for currently selected order type
    let restricted = false;
    let hint = "";

    if (mode === 0) {
      restricted = true;
      hint = `${info.icon} Trading is disabled for this symbol by the broker.`;
    } else if (mode === 1 && ["sell", "sell_limit", "sell_stop"].includes(action)) {
      restricted = true;
      hint = `${info.icon} Only long (buy) trades are allowed for this symbol.`;
    } else if (mode === 2 && ["buy", "buy_limit", "buy_stop"].includes(action)) {
      restricted = true;
      hint = `${info.icon} Only short (sell) trades are allowed for this symbol.`;
    } else if (mode === 3) {
      restricted = true;
      hint = `${info.icon} Symbol is in close-only mode. No new positions allowed.`;
    }

    if (brokerInfo && renderTradeModeWarning(brokerInfo)) {
      restricted = true;
    } else {
      execTradeRestriction.style.display = restricted ? "block" : "none";
      execTradeRestriction.textContent = hint;
    }
    execSubmitBtn.disabled = restricted;
    execSubmitBtn.style.opacity = restricted ? "0.5" : "1";
  }

  const isPendingType = () => !["buy", "sell"].includes(execType.value);

  const applyVolumeConstraints = () => {
    const brokerInfo = getCurrentBrokerInfo();
    const lotStep = Number(brokerInfo?.volume_step) || 0.01;
    const min = Number(brokerInfo?.volume_min) || lotStep;
    const max = Number(brokerInfo?.volume_max) || 100;

    execVolume.min = String(min);
    execVolume.max = String(max);
    execVolume.step = String(lotStep);

    const current = Number(execVolume.value || min);
    if (current < min || current > max) {
      execVolume.value = String(min);
    } else {
      execVolume.value = String(roundToStep(current, lotStep));
    }
    volumeHint.textContent = `Allowed volume: ${min} – ${max} (step ${lotStep})`;
  };

  const handleTypeChange = () => {
    execPriceGroup.style.display = isPendingType() ? "block" : "none";
    applyTradeModeUI();
    triggerValidation();
  };

  const refreshTick = async () => {
    const val = execTicker.value;
    latestTick = null;
    if (!val) {
      execPriceDisplay.textContent = "";
      return;
    }
    try {
      const tick = await api(`/tick/${val}`);
      latestTick = tick;
      execPriceDisplay.textContent = `Bid: ${tick.bid} | Ask: ${tick.ask} | Spread: ${tick.spread}`;
    } catch (err) {
      execPriceDisplay.textContent = `Tick unavailable: ${err.message}`;
    }
  };

  const handleTickerChange = async () => {
    applyVolumeConstraints();
    applyTradeModeUI();
    await refreshTick();
    triggerValidation();
  };

  execType.addEventListener("change", handleTypeChange);
  execTicker.addEventListener("change", handleTickerChange);
  [execVolume, execPrice, execSL, execTP, execComment].forEach((input) => {
    input.addEventListener("input", triggerValidation);
  });

  // T036: Build payload – include mt5_symbol_direct for broker-native symbols
  function buildExecutePayload(marketPrice) {
    const val = execTicker.value;
    const payload = {
      ticker: val,
      action: execType.value,
      quantity: Number(execVolume.value),
      current_price: marketPrice,
      sl: execSL.value ? Number(execSL.value) : null,
      tp: execTP.value ? Number(execTP.value) : null,
      mt5_symbol_direct: val,
    };
    return payload;
  }

  function buildPendingPayload() {
    if (!execTicker.value || !execVolume.value || !execPrice.value) return null;
    const val = execTicker.value;
    const payload = {
      ticker: val,
      type: execType.value,
      volume: Number(execVolume.value),
      price: Number(execPrice.value),
      sl: execSL.value ? Number(execSL.value) : null,
      tp: execTP.value ? Number(execTP.value) : null,
      comment: execComment.value || "",
      mt5_symbol_direct: val,
    };
    return payload;
  }

  function triggerValidation() {
    clearTimeout(checkTimeout);
    checkTimeout = setTimeout(runValidation, 500);
  }

  async function runValidation() {
    if (!isPendingType()) {
      valPanel.classList.add("hidden");
      return;
    }
    const payload = buildPendingPayload();
    if (!payload) {
      valPanel.classList.add("hidden");
      return;
    }
    try {
      const res = await api("/order-check", { method: "POST", body: JSON.stringify(payload) });
      valPanel.classList.remove("hidden");
      if (res.valid) {
        valPanel.className = "mt-4 p-2 rounded bg-gray-100";
        valStatusIcon.innerText = "OK";
        valStatusText.innerText = "Valid Order";
        valMargin.innerText = Number(res.margin || 0).toFixed(2);
        valProfit.innerText = Number(res.profit || 0).toFixed(2);
        valEquity.innerText = Number(res.equity || 0).toFixed(2);
      } else {
        valPanel.className = "mt-4 p-2 rounded bg-gray-100 text-red";
        valStatusIcon.innerText = "✕";
        valStatusText.innerText = `Invalid (Retcode ${res.retcode})`;
        valMargin.innerText = "-";
        valProfit.innerText = "-";
        valEquity.innerText = "-";
      }
      valComment.innerText = res.comment || "";
    } catch (err) {
      valPanel.classList.remove("hidden");
      valPanel.className = "mt-4 p-2 rounded bg-gray-100 text-red";
      valStatusIcon.innerText = "✕";
      valStatusText.innerText = "Validation failed";
      valComment.innerText = err.message;
      valMargin.innerText = "-";
      valProfit.innerText = "-";
      valEquity.innerText = "-";
    }
  }

  execSubmitBtn.addEventListener("click", async () => {
    const val = execTicker.value;
    if (!val) {
      alert("Select a symbol before submitting.");
      return;
    }
    const volume = Number(execVolume.value);
    if (!Number.isFinite(volume) || volume <= 0) {
      alert("Volume must be greater than 0.");
      return;
    }

    const isPending = isPendingType();
    const actionLabel = execType.value.replace(/_/g, " ").toUpperCase();
    if (!confirm(`Submit ${actionLabel} ${volume} ${val}?`)) return;

    execSubmitBtn.disabled = true;
    execSubmitBtn.innerText = "Submitting…";

    try {
      let route = "/execute";
      let payload;

      if (isPending) {
        route = "/pending-order";
        payload = buildPendingPayload();
        if (!payload) {
          alert("Pending orders require symbol, volume, and trigger price.");
          return;
        }
      } else {
        if (!latestTick) await refreshTick();
        if (!latestTick) {
          alert("Unable to fetch live price for market order.");
          return;
        }
        const marketPrice = execType.value === "sell" ? Number(latestTick.bid) : Number(latestTick.ask);
        payload = buildExecutePayload(marketPrice);
      }

      const res = await api(route, { method: "POST", body: JSON.stringify(payload) });
      if (res.success) {
        alert(`✅ Success. Ticket ID: ${res.ticket_id}`);
        [execPrice, execSL, execTP, execComment].forEach((el) => (el.value = ""));
      } else {
        alert(`❌ Failed: ${res.error || "Unknown execution error"}`);
      }
    } catch (err) {
      alert(`Error: ${err.message}`);
    } finally {
      execSubmitBtn.disabled = false;
      execSubmitBtn.innerText = "Submit";
      applyTradeModeUI(); // re-apply trade mode state after submit
    }
  });

  handleTypeChange();
  applyVolumeConstraints();
}
