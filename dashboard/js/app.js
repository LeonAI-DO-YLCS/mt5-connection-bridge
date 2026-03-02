import {
  renderConfig,
  renderExecute,
  renderLogs,
  renderMetrics,
  renderPrices,
  renderStatus,
  renderSymbols,
} from "./components.js";

const API_KEY_STORAGE = "mt5_bridge_api_key";

const authScreen = document.getElementById("authScreen");
const dashboardScreen = document.getElementById("dashboardScreen");
const authButton = document.getElementById("authButton");
const apiKeyInput = document.getElementById("apiKeyInput");
const authError = document.getElementById("authError");
const tabContent = document.getElementById("tabContent");
const envBadge = document.getElementById("envBadge");

let singleFlightPromise = null;

function getApiKey() {
  return sessionStorage.getItem(API_KEY_STORAGE);
}

function setApiKey(key) {
  sessionStorage.setItem(API_KEY_STORAGE, key);
}

function clearApiKey() {
  sessionStorage.removeItem(API_KEY_STORAGE);
}

async function api(path, options = {}) {
  const apiKey = getApiKey();
  const response = await fetch(path, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      "X-API-KEY": apiKey,
      ...(options.headers || {}),
    },
  });

  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(JSON.stringify(body.detail || body));
  }
  return body;
}

function selectTab(tabName) {
  document.querySelectorAll(".tab[data-tab]").forEach((tabButton) => {
    tabButton.classList.toggle("active", tabButton.dataset.tab === tabName);
  });
  loadTab(tabName).catch((err) => {
    tabContent.innerHTML = `<p class="error">${err.message}</p>`;
  });
}

async function loadTab(tabName) {
  if (tabName === "status") {
    const [health, worker, metrics] = await Promise.all([api("/health"), api("/worker/state"), api("/metrics")]);
    renderStatus(tabContent, health, worker, metrics);
    return;
  }

  if (tabName === "symbols") {
    const data = await api("/symbols");
    renderSymbols(tabContent, data.symbols || []);
    return;
  }

  if (tabName === "prices") {
    const data = await api("/prices?ticker=V75&start_date=2026-01-01&end_date=2026-01-31&timeframe=D1");
    renderPrices(tabContent, data);
    return;
  }

  if (tabName === "execute") {
    const config = await api("/config");
    envBadge.textContent = config.execution_enabled ? "LIVE ENABLED" : "EXECUTION BLOCKED";
    renderExecute(tabContent, config);
    wireExecuteTab();
    return;
  }

  if (tabName === "logs") {
    const logs = await api("/logs?limit=50&offset=0");
    renderLogs(tabContent, logs);
    return;
  }

  if (tabName === "config") {
    const config = await api("/config");
    renderConfig(tabContent, config);
    return;
  }

  if (tabName === "metrics") {
    const metrics = await api("/metrics");
    renderMetrics(tabContent, metrics);
  }
}

function wireExecuteTab() {
  const submitButton = document.getElementById("submitTrade");
  const multiTradeMode = document.getElementById("multiTradeMode");
  const warning = document.getElementById("multiTradeWarning");
  const confirmLive = document.getElementById("confirmLive");
  const resultEl = document.getElementById("executeResult");

  multiTradeMode?.addEventListener("change", () => {
    warning.classList.toggle("hidden", !multiTradeMode.checked);
  });

  submitButton?.addEventListener("click", async () => {
    if (!confirmLive.checked) {
      alert("Confirm live-trade risk before submitting.");
      return;
    }

    if (!multiTradeMode.checked && singleFlightPromise) {
      resultEl.textContent = "Single-flight mode blocks parallel submissions.";
      return;
    }

    const payload = {
      ticker: document.getElementById("execTicker").value,
      action: document.getElementById("execAction").value,
      quantity: Number(document.getElementById("execQty").value),
      current_price: Number(document.getElementById("execPrice").value),
      multi_trade_mode: Boolean(multiTradeMode.checked),
    };

    const runRequest = api("/execute", {
      method: "POST",
      body: JSON.stringify(payload),
    });

    if (!multiTradeMode.checked) {
      singleFlightPromise = runRequest;
    }

    try {
      const result = await runRequest;
      resultEl.textContent = JSON.stringify(result, null, 2);
    } catch (error) {
      resultEl.textContent = `Execution error: ${error.message}`;
    } finally {
      if (!multiTradeMode.checked) {
        singleFlightPromise = null;
      }
    }
  });
}

async function authenticateAndBoot() {
  try {
    await api("/health");
    authError.textContent = "";
    authScreen.classList.add("hidden");
    dashboardScreen.classList.remove("hidden");
    selectTab("status");
  } catch (err) {
    authError.textContent = "Authentication failed.";
    clearApiKey();
  }
}

authButton?.addEventListener("click", async () => {
  const value = apiKeyInput.value.trim();
  if (!value) {
    authError.textContent = "API key is required.";
    return;
  }
  setApiKey(value);
  await authenticateAndBoot();
});

document.getElementById("tabs")?.addEventListener("click", (event) => {
  const target = event.target;
  if (!(target instanceof HTMLElement)) {
    return;
  }

  if (target.id === "logoutButton") {
    clearApiKey();
    dashboardScreen.classList.add("hidden");
    authScreen.classList.remove("hidden");
    return;
  }

  if (target.dataset.tab) {
    selectTab(target.dataset.tab);
  }
});

window.addEventListener("beforeunload", () => {
  clearApiKey();
});

if (getApiKey()) {
  authenticateAndBoot().catch(() => {
    authScreen.classList.remove("hidden");
  });
}
