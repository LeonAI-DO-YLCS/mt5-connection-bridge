export async function renderHistory(container) {
  container.innerHTML = `
    <h3>Trade History</h3>
    <div class="panel">
      <div class="grid two">
        <label>From: <input type="date" id="histFrom"></label>
        <label>To: <input type="date" id="histTo"></label>
        <button id="histRefresh" class="btn">Refresh</button>
        <button id="histExport" class="btn">Export to CSV</button>
      </div>
      <div class="tabs mt-4" style="margin-top: 20px;">
        <button id="tabDeals" class="tab active">Deals</button>
        <button id="tabOrders" class="tab">Orders</button>
      </div>
    </div>
    <div id="histSummary" class="panel hidden" style="margin-top: 15px; background: var(--bg-color); border: 1px solid var(--border-color); padding: 10px; border-radius: 6px;"></div>
    <div id="histTableContainer" style="margin-top: 15px; overflow-x: auto;"></div>
  `;

  // Set default dates: To = today, From = 7 days ago
  const dateTo = new Date();
  const dateFrom = new Date();
  dateFrom.setDate(dateTo.getDate() - 7);
  
  const fromEl = document.getElementById("histFrom");
  const toEl = document.getElementById("histTo");
  
  fromEl.value = dateFrom.toISOString().split("T")[0];
  toEl.value = dateTo.toISOString().split("T")[0];

  let currentSubTab = "deals";
  let currentData = null;

  const tabDeals = document.getElementById("tabDeals");
  const tabOrders = document.getElementById("tabOrders");
  const refreshBtn = document.getElementById("histRefresh");
  const exportBtn = document.getElementById("histExport");

  const loadData = async () => {
    // We add T00:00:00Z and T23:59:59Z to the dates
    const dFrom = fromEl.value ? `${fromEl.value}T00:00:00Z` : "";
    const dTo = toEl.value ? `${toEl.value}T23:59:59Z` : "";

    if (!dFrom || !dTo) return;

    try {
      const endpoint = currentSubTab === "deals" ? "/history/deals" : "/history/orders";
      if (typeof window.api !== "function") {
        throw new Error("API helper is not initialized");
      }
      const data = await window.api(`${endpoint}?date_from=${dFrom}&date_to=${dTo}`);
      currentData = data;
      renderTable(data);
    } catch (err) {
      document.getElementById("histTableContainer").innerHTML = `<p class="error">Failed to load history: ${err.message}</p>`;
    }
  };

  const renderTable = (data) => {
    const summaryEl = document.getElementById("histSummary");
    const container = document.getElementById("histTableContainer");

    if (currentSubTab === "deals") {
      summaryEl.classList.remove("hidden");
      summaryEl.innerHTML = `
        <strong>Summary:</strong>
        <span style="margin-right: 15px;">Net Profit: <span style="color: ${data.net_profit >= 0 ? 'var(--success-color)' : 'var(--danger-color)'}">$${data.net_profit.toFixed(2)}</span></span>
        <span style="margin-right: 15px;">Swap: $${data.total_swap.toFixed(2)}</span>
        <span style="margin-right: 15px;">Commission: $${data.total_commission.toFixed(2)}</span>
        <span>Count: ${data.count}</span>
      `;

      if (!data.deals || data.deals.length === 0) {
        container.innerHTML = "<p>No trades found for this period.</p>";
        return;
      }

      let html = `<table class="table">
        <thead>
          <tr>
            <th>Time</th>
            <th>Type</th>
            <th>Entry</th>
            <th>Symbol</th>
            <th>Volume</th>
            <th>Price</th>
            <th>Profit</th>
            <th>Commission</th>
          </tr>
        </thead>
        <tbody>`;
      data.deals.forEach(d => {
        const pColor = d.profit >= 0 ? 'var(--success-color)' : 'var(--danger-color)';
        html += `<tr>
          <td>${new Date(d.time).toLocaleString()}</td>
          <td>${d.type.toUpperCase()}</td>
          <td>${d.entry.toUpperCase()}</td>
          <td>${d.symbol}</td>
          <td>${d.volume}</td>
          <td>${d.price}</td>
          <td style="color: ${pColor}">${d.profit.toFixed(2)}</td>
          <td>${d.commission.toFixed(2)}</td>
        </tr>`;
      });
      html += `</tbody></table>`;
      container.innerHTML = html;
    } else {
      summaryEl.classList.add("hidden");
      summaryEl.innerHTML = "";

      if (!data.orders || data.orders.length === 0) {
        container.innerHTML = "<p>No trades found for this period.</p>";
        return;
      }

      let html = `<table class="table">
        <thead>
          <tr>
            <th>Setup Time</th>
            <th>Done Time</th>
            <th>Ticket</th>
            <th>Type</th>
            <th>State</th>
            <th>Symbol</th>
            <th>Volume</th>
            <th>Price</th>
          </tr>
        </thead>
        <tbody>`;
      data.orders.forEach(o => {
        let stateColor = "";
        if (o.state === "filled") stateColor = "var(--success-color)";
        else if (o.state === "cancelled" || o.state === "rejected") stateColor = "var(--danger-color)";
        else stateColor = "var(--text-color)";

        html += `<tr>
          <td>${new Date(o.time_setup).toLocaleString()}</td>
          <td>${new Date(o.time_done).toLocaleString()}</td>
          <td>${o.ticket}</td>
          <td>${o.type.toUpperCase()}</td>
          <td style="color: ${stateColor}; font-weight: bold;">${o.state.toUpperCase()}</td>
          <td>${o.symbol}</td>
          <td>${o.volume}</td>
          <td>${o.price}</td>
        </tr>`;
      });
      html += `</tbody></table>`;
      container.innerHTML = html;
    }
  };

  const exportCsv = () => {
    if (!currentData) return;

    let csvContent = "";
    if (currentSubTab === "deals") {
      const arr = currentData.deals || [];
      if (arr.length === 0) return;
      csvContent += "Time,Type,Entry,Symbol,Volume,Price,Profit,Swap,Commission\n";
      arr.forEach(d => {
        csvContent += `${d.time},${d.type},${d.entry},${d.symbol},${d.volume},${d.price},${d.profit},${d.swap},${d.commission}\n`;
      });
    } else {
      const arr = currentData.orders || [];
      if (arr.length === 0) return;
      csvContent += "SetupTime,DoneTime,Ticket,Type,State,Symbol,Volume,Price,SL,TP\n";
      arr.forEach(o => {
        csvContent += `${o.time_setup},${o.time_done},${o.ticket},${o.type},${o.state},${o.symbol},${o.volume},${o.price},${o.sl || 0},${o.tp || 0}\n`;
      });
    }

    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `history-${currentSubTab}-${fromEl.value}-to-${toEl.value}.csv`;
    link.style.visibility = "hidden";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  tabDeals.addEventListener("click", () => {
    tabDeals.classList.add("active");
    tabOrders.classList.remove("active");
    currentSubTab = "deals";
    loadData();
  });

  tabOrders.addEventListener("click", () => {
    tabOrders.classList.add("active");
    tabDeals.classList.remove("active");
    currentSubTab = "orders";
    loadData();
  });

  refreshBtn.addEventListener("click", loadData);
  exportBtn.addEventListener("click", exportCsv);

  // Initial load
  await loadData();
}
