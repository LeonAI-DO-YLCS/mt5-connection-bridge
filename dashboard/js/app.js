import {
  renderConfig,
  renderLogs,
  renderMetrics,
  renderStatus,
  renderSymbols,
} from "./components.js";
import { renderExecute } from "./execute-v2.js";
import { renderPositions } from "./positions.js";
import { renderOrders } from "./orders.js";
import { renderHistory } from "./history.js";
import { renderBrokerSymbols } from "./symbols-browser.js";
import { showEnvelope, showError } from "./message-renderer.js";

const API_KEY_STORAGE = "mt5_bridge_api_key";

const authScreen = document.getElementById("authScreen");
const dashboardScreen = document.getElementById("dashboardScreen");
const authButton = document.getElementById("authButton");
const apiKeyInput = document.getElementById("apiKeyInput");
const authError = document.getElementById("authError");
const tabContent = document.getElementById("tabContent");
const envBadge = document.getElementById("envBadge");

let ObjectInterval = null;
let singleFlightPromise = null;
const tabCache = new Map();

const connectionBanner = document.createElement("div");
connectionBanner.className = "connection-banner hidden";
connectionBanner.id = "connectionBanner";
connectionBanner.textContent = "Terminal disconnected. Showing stale data when available.";
dashboardScreen.prepend(connectionBanner);

function clearAutoRefresh() {
  if (ObjectInterval) {
    clearInterval(ObjectInterval);
    ObjectInterval = null;
  }
}

function getApiKey() {
  return sessionStorage.getItem(API_KEY_STORAGE);
}

function setApiKey(key) {
  sessionStorage.setItem(API_KEY_STORAGE, key);
}

function clearApiKey() {
  sessionStorage.removeItem(API_KEY_STORAGE);
}

function isTerminalDisconnectedError(err) {
  const text = String(err?.message || "");
  return (
    text.includes("MT5 terminal not connected") ||
    text.includes("Not connected to MT5") ||
    text.includes("Failed to retrieve terminal info")
  );
}

function setConnectionBanner(disconnected) {
  connectionBanner.classList.toggle("hidden", !disconnected);
}

function cacheTabData(tab, data) {
  tabCache.set(tab, { data, at: new Date() });
}

function getCachedTabData(tab) {
  return tabCache.get(tab) || null;
}

function renderFreshness(tab, stale = false) {
  const cached = getCachedTabData(tab);
  if (!cached?.at) {
    return;
  }
  const stamp = document.createElement("div");
  stamp.className = `freshness-badge${stale ? " stale" : ""}`;
  stamp.textContent = `${stale ? "Showing stale data. " : ""}Last updated: ${cached.at.toLocaleString()}`;
  tabContent.prepend(stamp);
}

export async function api(path, options = {}) {
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
    // Attach full envelope body to the error for downstream rendering
    const err = new Error(JSON.stringify(body.detail || body));
    err.envelope = (body && body.tracking_id) ? body : null;
    throw err;
  }
  return body;
}
window.api = api;

function selectTab(tabName) {
  clearAutoRefresh();
  document.querySelectorAll(".tab[data-tab]").forEach((tabButton) => {
    tabButton.classList.toggle("active", tabButton.dataset.tab === tabName);
  });
  loadTab(tabName).catch((err) => {
    tabContent.innerHTML = `<p class="error">${err.message}</p>`;
  });
}

async function loadTab(tabName) {
  if (tabName === "status") {
    const wireExecutionToggle = (doLoad, executionEnabled) => {
      const btn = document.getElementById("executionToggleBtn");
      if (!btn) {
        return;
      }
      btn.addEventListener("click", async () => {
        const targetEnabled = !executionEnabled;
        const confirmed = confirm(
          `${targetEnabled ? "Enable" : "Disable"} order execution policy?`,
        );
        if (!confirmed) {
          return;
        }
        btn.disabled = true;
        try {
          const updatedConfig = await api("/config/execution", {
            method: "PUT",
            body: JSON.stringify({ execution_enabled: targetEnabled }),
          });
          envBadge.textContent = updatedConfig.execution_enabled ? "LIVE ENABLED" : "EXECUTION BLOCKED";
          await doLoad();
        } catch (err) {
          showEnvelope(err.envelope || err);
        } finally {
          btn.disabled = false;
        }
      });
    };

    const doLoad = async () => {
      try {
        const [health, worker, metrics, account, terminal, config, capabilities] = await Promise.all([
          api("/health"),
          api("/worker/state"),
          api("/metrics"),
          api("/account").catch(() => null),
          api("/terminal").catch(() => null),
          api("/config"),
          api("/broker-capabilities").catch(() => null),
        ]);
        cacheTabData("status", { health, worker, metrics, account, terminal, config, capabilities });
        setConnectionBanner(false);
        renderStatus(tabContent, health, worker, metrics, account, terminal, config, capabilities);
        envBadge.textContent = config.execution_enabled ? "LIVE ENABLED" : "EXECUTION BLOCKED";
        wireExecutionToggle(doLoad, Boolean(config.execution_enabled));
        renderFreshness("status", false);
      } catch (err) {
        const cached = getCachedTabData("status");
        if (!cached || !isTerminalDisconnectedError(err)) {
          throw err;
        }
        setConnectionBanner(true);
        renderStatus(
          tabContent,
          cached.data.health,
          cached.data.worker,
          cached.data.metrics,
          cached.data.account,
          cached.data.terminal,
          cached.data.config,
          cached.data.capabilities,
        );
        envBadge.textContent = cached.data.config?.execution_enabled ? "LIVE ENABLED" : "EXECUTION BLOCKED";
        wireExecutionToggle(doLoad, Boolean(cached.data.config?.execution_enabled));
        renderFreshness("status", true);
      }
    };
    await doLoad();
    ObjectInterval = setInterval(doLoad, 5000); // 5 sec refresh for status too
    return;
  }

  if (tabName === "positions") {
    const doLoad = async () => {
      try {
        const [positionsData, accountData] = await Promise.all([
          api("/positions"),
          api("/account").catch(() => null),
        ]);
        cacheTabData("positions", { positionsData, accountData });
        setConnectionBanner(false);
        renderPositions(tabContent, positionsData, accountData);
        renderFreshness("positions", false);
      } catch (err) {
        const cached = getCachedTabData("positions");
        if (!cached || !isTerminalDisconnectedError(err)) {
          throw err;
        }
        setConnectionBanner(true);
        renderPositions(tabContent, cached.data.positionsData, cached.data.accountData);
        renderFreshness("positions", true);
      }
    };
    await doLoad();
    ObjectInterval = setInterval(doLoad, 5000);
    return;
  }

  if (tabName === "orders") {
    const doLoad = async () => {
      try {
        const data = await api("/orders");
        cacheTabData("orders", { data });
        setConnectionBanner(false);
        renderOrders(tabContent, data);
        renderFreshness("orders", false);
      } catch (err) {
        const cached = getCachedTabData("orders");
        if (!cached || !isTerminalDisconnectedError(err)) {
          throw err;
        }
        setConnectionBanner(true);
        renderOrders(tabContent, cached.data.data);
        renderFreshness("orders", true);
      }
    };
    await doLoad();
    ObjectInterval = setInterval(doLoad, 10000);
    return;
  }

  if (tabName === "symbols") {
    try {
      const data = await api("/symbols");
      cacheTabData("symbols", { data });
      setConnectionBanner(false);
      renderSymbols(tabContent, data.symbols || []);
      await renderBrokerSymbols(tabContent).catch(() => {});
      renderFreshness("symbols", false);
    } catch (err) {
      const cached = getCachedTabData("symbols");
      if (!cached || !isTerminalDisconnectedError(err)) {
        throw err;
      }
      setConnectionBanner(true);
      renderSymbols(tabContent, cached.data.data.symbols || []);
      await renderBrokerSymbols(tabContent).catch(() => {});
      renderFreshness("symbols", true);
    }
    return;
  }

  if (tabName === "prices") {
    const capResp = await api("/broker-capabilities").catch(() => ({ symbols: [], categories: {} }));
    const capCategories = capResp.categories || {};

    let optionsHtml = "";
    for (const [cat, subs] of Object.entries(capCategories).sort()) {
      const catSyms = (capResp.symbols || []).filter((s) => s.category === cat);
      if (catSyms.length === 0) continue;
      optionsHtml += `<optgroup label="${cat}">`;
      for (const sym of catSyms) {
        optionsHtml += `<option value="${sym.name}">${sym.name} — ${sym.description.slice(0, 40)}</option>`;
      }
      optionsHtml += `</optgroup>`;
    }

    tabContent.innerHTML = `
      <h3>Live Prices</h3>
      <div class="card" style="max-width: 560px;">
        <label for="priceSearch"><strong>Search:</strong></label>
        <input type="text" id="priceSearch" placeholder="Filter symbols…" class="mt-1" style="width:100%;" />
        <label for="priceTicker" style="margin-top:8px;display:block;"><strong>Symbol</strong></label>
        <select id="priceTicker" class="mt-2" size="1">${optionsHtml}</select>
        <div id="priceSnapshot" class="mt-4 small">Select a symbol to load current price.</div>
      </div>
    `;

    const tickerEl = document.getElementById("priceTicker");
    const priceSearchEl = document.getElementById("priceSearch");
    const snapshotEl = document.getElementById("priceSnapshot");

    priceSearchEl?.addEventListener("input", () => {
      const q = priceSearchEl.value.toLowerCase();
      tickerEl.innerHTML = "";
      for (const [cat, subs] of Object.entries(capCategories).sort()) {
        const catSyms = (capResp.symbols || []).filter(
          (s) => s.category === cat && (s.name.toLowerCase().includes(q) || s.description.toLowerCase().includes(q))
        );
        if (catSyms.length > 0) {
          const og = document.createElement("optgroup");
          og.label = cat;
          catSyms.forEach((sym) => {
            const opt = document.createElement("option");
            opt.value = sym.name;
            opt.textContent = `${sym.name} — ${sym.description.slice(0, 40)}`;
            og.appendChild(opt);
          });
          tickerEl.appendChild(og);
        }
      }
    });

    const refreshTick = async () => {
      const ticker = tickerEl?.value;
      if (!ticker) {
        snapshotEl.textContent = "No symbol selected.";
        return;
      }
      try {
        const tick = await api(`/tick/${ticker}`);
        cacheTabData("prices", { tick, ticker });
        setConnectionBanner(false);
        snapshotEl.innerHTML = `
          <p><strong>Symbol:</strong> ${tick.ticker}</p>
          <p><strong>Bid:</strong> ${tick.bid}</p>
          <p><strong>Ask:</strong> ${tick.ask}</p>
          <p><strong>Spread:</strong> ${tick.spread}</p>
          <p><strong>Time:</strong> ${tick.time}</p>
        `;
        renderFreshness("prices", false);
      } catch (err) {
        const cached = getCachedTabData("prices");
        if (cached && isTerminalDisconnectedError(err) && cached.data.ticker === ticker) {
          setConnectionBanner(true);
          const tick = cached.data.tick;
          snapshotEl.innerHTML = `
            <p><strong>Symbol:</strong> ${tick.ticker}</p>
            <p><strong>Bid:</strong> ${tick.bid}</p>
            <p><strong>Ask:</strong> ${tick.ask}</p>
            <p><strong>Spread:</strong> ${tick.spread}</p>
            <p><strong>Time:</strong> ${tick.time}</p>
            <p class="warn small">Terminal disconnected. Showing stale tick.</p>
          `;
          renderFreshness("prices", true);
          return;
        }
        snapshotEl.innerHTML = `<p class="error">${err.message}</p>`;
      }
    };

    tickerEl?.addEventListener("change", refreshTick);
    await refreshTick();
    return;
  }

  if (tabName === "execute") {
    const config = await api("/config");
    envBadge.textContent = config.execution_enabled ? "LIVE ENABLED" : "EXECUTION BLOCKED";
    await renderExecute(tabContent);
    return;
  }
  
  if (tabName === "history") {
    await renderHistory(tabContent);
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
