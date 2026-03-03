import { api } from "./app.js";

let checkTimeout = null;

function roundToStep(value, step) {
  const precision = step.toString().includes(".") ? step.toString().split(".")[1].length : 0;
  const rounded = Math.round(value / step) * step;
  return Number(rounded.toFixed(precision));
}

export async function renderExecute(contentEl) {
  let latestTick = null;
  const tickerMeta = new Map();
  const brokerMeta = new Map();

  contentEl.innerHTML = `
    <h3>Execute Trade / Pending Order</h3>
    <div class="card" style="max-width: 560px">
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
          <label>Ticker:</label>
          <select id="execTicker" class="bg-gray-100 p-2 rounded w-full">
            <option value="">Select Ticker...</option>
          </select>
          <div id="execPriceDisplay" class="small mt-1 text-muted"></div>
        </div>

        <div class="mt-2">
          <label>Volume:</label>
          <input type="number" id="execVolume" value="0.01" step="0.01" min="0.01" class="bg-gray-100 p-2 rounded w-full">
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
  const execPriceGroup = document.getElementById("execPriceGroup");
  const execVolume = document.getElementById("execVolume");
  const execPrice = document.getElementById("execPrice");
  const execSL = document.getElementById("execSL");
  const execTP = document.getElementById("execTP");
  const execComment = document.getElementById("execComment");
  const execPriceDisplay = document.getElementById("execPriceDisplay");
  const volumeHint = document.getElementById("volumeHint");

  const valPanel = document.getElementById("validationPanel");
  const valStatusIcon = document.getElementById("valStatusIcon");
  const valStatusText = document.getElementById("valStatusText");
  const valMargin = document.getElementById("valMargin");
  const valProfit = document.getElementById("valProfit");
  const valEquity = document.getElementById("valEquity");
  const valComment = document.getElementById("valComment");
  const execSubmitBtn = document.getElementById("execSubmitBtn");

  try {
    const [symbolsResp, brokerResp] = await Promise.all([
      api("/symbols"),
      api("/broker-symbols").catch(() => ({ symbols: [] })),
    ]);

    const symbols = symbolsResp.symbols || [];
    const brokerSymbols = brokerResp.symbols || [];

    symbols.forEach((s) => {
      tickerMeta.set(s.ticker, { mt5Symbol: s.mt5_symbol, lotSize: Number(s.lot_size) || 0.01 });
    });
    brokerSymbols.forEach((b) => {
      brokerMeta.set(b.name, b);
    });

    execTicker.innerHTML =
      `<option value="">Select Ticker...</option>` +
      symbols
        .map((s) => s.ticker)
        .sort()
        .map((t) => `<option value="${t}">${t}</option>`)
        .join("");
  } catch (err) {
    execPriceDisplay.textContent = `Failed to load symbols: ${err.message}`;
  }

  const isPendingType = () => !["buy", "sell"].includes(execType.value);

  const applyVolumeConstraints = () => {
    const ticker = execTicker.value;
    const meta = tickerMeta.get(ticker);
    const lotStep = meta?.lotSize || 0.01;
    const brokerInfo = meta ? brokerMeta.get(meta.mt5Symbol) : null;
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

    volumeHint.textContent = `Allowed volume: ${min} - ${max} (step ${lotStep})`;
  };

  const handleTypeChange = () => {
    execPriceGroup.style.display = isPendingType() ? "block" : "none";
    triggerValidation();
  };

  const refreshTick = async () => {
    const ticker = execTicker.value;
    latestTick = null;
    if (!ticker) {
      execPriceDisplay.textContent = "";
      return;
    }
    try {
      const tick = await api(`/tick/${ticker}`);
      latestTick = tick;
      execPriceDisplay.textContent = `Bid: ${tick.bid} | Ask: ${tick.ask} | Spread: ${tick.spread}`;
    } catch (err) {
      execPriceDisplay.textContent = `Tick unavailable: ${err.message}`;
    }
  };

  const handleTickerChange = async () => {
    applyVolumeConstraints();
    await refreshTick();
    triggerValidation();
  };

  execType.addEventListener("change", handleTypeChange);
  execTicker.addEventListener("change", handleTickerChange);
  [execVolume, execPrice, execSL, execTP, execComment].forEach((input) => {
    input.addEventListener("input", triggerValidation);
  });

  function buildPendingPayload() {
    if (!execTicker.value || !execVolume.value || !execPrice.value) {
      return null;
    }
    return {
      ticker: execTicker.value,
      type: execType.value,
      volume: Number(execVolume.value),
      price: Number(execPrice.value),
      sl: execSL.value ? Number(execSL.value) : null,
      tp: execTP.value ? Number(execTP.value) : null,
      comment: execComment.value || "",
    };
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
      const res = await api("/order-check", {
        method: "POST",
        body: JSON.stringify(payload),
      });

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
        valStatusIcon.innerText = "X";
        valStatusText.innerText = `Invalid (Retcode ${res.retcode})`;
        valMargin.innerText = "-";
        valProfit.innerText = "-";
        valEquity.innerText = "-";
      }
      valComment.innerText = res.comment || "";
    } catch (err) {
      valPanel.classList.remove("hidden");
      valPanel.className = "mt-4 p-2 rounded bg-gray-100 text-red";
      valStatusIcon.innerText = "X";
      valStatusText.innerText = "Validation failed";
      valComment.innerText = err.message;
      valMargin.innerText = "-";
      valProfit.innerText = "-";
      valEquity.innerText = "-";
    }
  }

  execSubmitBtn.addEventListener("click", async () => {
    const ticker = execTicker.value;
    if (!ticker) {
      alert("Select a ticker before submitting.");
      return;
    }

    const volume = Number(execVolume.value);
    if (!Number.isFinite(volume) || volume <= 0) {
      alert("Volume must be greater than 0.");
      return;
    }

    const isPending = isPendingType();
    const actionName = `${execType.value.replace("_", " ").toUpperCase()} ${volume} ${ticker}`;
    if (!confirm(`Submit ${actionName}?`)) {
      return;
    }

    execSubmitBtn.disabled = true;
    execSubmitBtn.innerText = "Submitting...";

    try {
      let route = "/execute";
      let payload;

      if (isPending) {
        route = "/pending-order";
        payload = buildPendingPayload();
        if (!payload) {
          alert("Pending orders require ticker, volume, and trigger price.");
          return;
        }
      } else {
        if (!latestTick) {
          await refreshTick();
        }
        if (!latestTick) {
          alert("Unable to fetch live price for market order.");
          return;
        }
        const marketPrice = execType.value === "sell" ? Number(latestTick.bid) : Number(latestTick.ask);
        payload = {
          ticker,
          action: execType.value,
          quantity: volume,
          current_price: marketPrice,
          sl: execSL.value ? Number(execSL.value) : null,
          tp: execTP.value ? Number(execTP.value) : null,
        };
      }

      const res = await api(route, {
        method: "POST",
        body: JSON.stringify(payload),
      });

      if (res.success) {
        alert(`Success. Ticket ID: ${res.ticket_id}`);
        execPrice.value = "";
        execSL.value = "";
        execTP.value = "";
        execComment.value = "";
      } else {
        alert(`Failed: ${res.error || "Unknown execution error"}`);
      }
    } catch (err) {
      alert(`Error: ${err.message}`);
    } finally {
      execSubmitBtn.disabled = false;
      execSubmitBtn.innerText = "Submit";
    }
  });

  handleTypeChange();
  applyVolumeConstraints();
}
