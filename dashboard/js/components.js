import { drawCandles } from "./chart.js";

function valueOrDash(value) {
  return value ?? "-";
}

export function renderStatus(contentEl, health, worker, metrics, account, terminal, config) {
  const executionEnabled = Boolean(config?.execution_enabled);
  const execClass = executionEnabled ? "ok" : "warn";
  const execLabel = executionEnabled ? "ENABLED" : "DISABLED";
  const toggleLabel = executionEnabled ? "Disable Execution" : "Enable Execution";

  let html = `
    <div class="grid two">
      <article class="card"><h3>Health</h3>
        <p><strong>Connected:</strong> ${health.connected}</p>
        <p><strong>Authorized:</strong> ${health.authorized}</p>
        <p><strong>Broker:</strong> ${valueOrDash(health.broker)}</p>
        <p><strong>Account:</strong> ${valueOrDash(health.account_id)}</p>
      </article>
      <article class="card"><h3>Worker</h3>
        <p><strong>State:</strong> ${worker.state}</p>
        <p><strong>Queue depth:</strong> ${worker.queue_depth}</p>
      </article>
      <article class="card"><h3>Metrics</h3>
        <p><strong>Total requests:</strong> ${metrics.total_requests}</p>
        <p><strong>Errors:</strong> ${metrics.errors_count}</p>
        <p><strong>Retention:</strong> ${metrics.retention_days} days</p>
      </article>
      <article class="card"><h3>Execution Policy</h3>
        <p><strong>Status:</strong> <span class="${execClass}">${execLabel}</span></p>
        <button id="executionToggleBtn" class="btn btn-sm ${executionEnabled ? "btn-danger" : "btn-primary"}">${toggleLabel}</button>
      </article>
  `;

  if (account) {
    html += `
      <article class="card"><h3>Account Summary</h3>
        <p><strong>Balance:</strong> ${account.balance} ${account.currency || ""}</p>
        <p><strong>Equity:</strong> ${account.equity} ${account.currency || ""}</p>
        <p><strong>Margin:</strong> ${account.margin} ${account.currency || ""}</p>
        <p><strong>Free Margin:</strong> ${account.free_margin} ${account.currency || ""}</p>
        <p><strong>Profit:</strong> ${account.profit} ${account.currency || ""}</p>
        <p><strong>Leverage:</strong> 1:${account.leverage}</p>
      </article>
    `;
  }

  if (terminal) {
    html += `
      <article class="card"><h3>Terminal Diagnostics</h3>
        <p><strong>Name:</strong> ${terminal.name}</p>
        <p><strong>Build:</strong> ${terminal.build}</p>
        <p><strong>Connected:</strong> ${terminal.connected}</p>
        <p><strong>Trade Allowed:</strong> ${terminal.trade_allowed}</p>
        <p><strong>Path:</strong> ${terminal.path}</p>
        <p><strong>Data Path:</strong> ${terminal.data_path}</p>
      </article>
    `;
  }

  html += `</div>`;
  contentEl.innerHTML = html;
}

export function renderSymbols(contentEl, symbols) {
  const rows = symbols
    .map(
      (symbol) =>
        `<tr><td>${symbol.ticker}</td><td>${symbol.mt5_symbol}</td><td>${symbol.lot_size}</td><td>${symbol.category}</td></tr>`,
    )
    .join("");

  contentEl.innerHTML = `
    <h3>Configured Symbols</h3>
    <div class="table-wrap">
      <table>
        <thead><tr><th>Ticker</th><th>MT5 Symbol</th><th>Lot Size</th><th>Category</th></tr></thead>
        <tbody>${rows || "<tr><td colspan='4'>No symbols configured.</td></tr>"}</tbody>
      </table>
    </div>
  `;
}

export function renderPrices(contentEl, payload) {
  const rows = payload.prices
    .map(
      (price) =>
        `<tr><td>${price.time}</td><td>${price.open}</td><td>${price.high}</td><td>${price.low}</td><td>${price.close}</td><td>${price.volume}</td></tr>`,
    )
    .join("");

  contentEl.innerHTML = `
    <h3>Prices — ${payload.ticker}</h3>
    <button id="exportPrices">Export CSV</button>
    <div class="table-wrap">
      <table>
        <thead><tr><th>Time</th><th>Open</th><th>High</th><th>Low</th><th>Close</th><th>Volume</th></tr></thead>
        <tbody>${rows || "<tr><td colspan='6'>No prices found for selected range.</td></tr>"}</tbody>
      </table>
    </div>
    <canvas id="candleChart" width="1000" height="320"></canvas>
  `;

  drawCandles(document.getElementById("candleChart"), payload.prices);

  const exportBtn = document.getElementById("exportPrices");
  exportBtn?.addEventListener("click", () => {
    const csv = ["time,open,high,low,close,volume"]
      .concat(payload.prices.map((p) => `${p.time},${p.open},${p.high},${p.low},${p.close},${p.volume}`))
      .join("\n");
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${payload.ticker}-prices.csv`;
    a.click();
    URL.revokeObjectURL(url);
  });
}



export function renderLogs(contentEl, logs) {
  const rows = logs.entries
    .map(
      (entry) =>
        `<tr><td>${entry.timestamp}</td><td>${JSON.stringify(entry.request)}</td><td>${JSON.stringify(entry.response)}</td></tr>`,
    )
    .join("");

  contentEl.innerHTML = `
    <h3>Trade Logs</h3>
    <p class="small">Showing ${logs.entries.length} / ${logs.total}</p>
    <div class="table-wrap">
      <table>
        <thead><tr><th>Timestamp</th><th>Request</th><th>Response</th></tr></thead>
        <tbody>${rows || "<tr><td colspan='3'>No log entries.</td></tr>"}</tbody>
      </table>
    </div>
  `;
}

export function renderConfig(contentEl, config) {
  const fields = Object.entries(config)
    .map(([key, value]) => `<tr><td>${key}</td><td>${JSON.stringify(value)}</td></tr>`)
    .join("");

  contentEl.innerHTML = `
    <h3>Runtime Config</h3>
    <div class="table-wrap">
      <table>
        <tbody>${fields}</tbody>
      </table>
    </div>
  `;
}

export function renderMetrics(contentEl, metrics) {
  const endpointRows = Object.entries(metrics.requests_by_endpoint)
    .map(([path, count]) => `<tr><td>${path}</td><td>${count}</td></tr>`)
    .join("");

  contentEl.innerHTML = `
    <h3>Metrics Summary</h3>
    <p><strong>Uptime:</strong> ${metrics.uptime_seconds.toFixed(2)}s</p>
    <p><strong>Total requests:</strong> ${metrics.total_requests}</p>
    <p><strong>Errors:</strong> ${metrics.errors_count}</p>
    <p><strong>Retention:</strong> ${metrics.retention_days} days</p>
    <table>
      <thead><tr><th>Endpoint</th><th>Requests</th></tr></thead>
      <tbody>${endpointRows || "<tr><td colspan='2'>No endpoint data yet.</td></tr>"}</tbody>
    </table>
  `;
}
