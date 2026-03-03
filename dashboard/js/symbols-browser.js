export function renderBrokerSymbols(container, brokerData) {
  const section = document.createElement("div");
  section.innerHTML = `
    <hr style="margin: 30px 0; border: 1px solid var(--border-color);" />
    <h3>Broker Symbols Catalog</h3>
    <div class="panel">
      <div class="grid two" style="margin-bottom: 20px;">
        <input type="text" id="symSearch" placeholder="Search by name or description..." />
        <select id="symGroup">
          <option value="all">All Groups</option>
          <option value="forex">Forex</option>
          <option value="crypto">Crypto</option>
          <option value="indices">Indices</option>
          <option value="metals">Metals</option>
          <option value="energy">Energy</option>
        </select>
      </div>
      <div id="symCatalogSummary" class="small" style="margin-bottom: 10px;"></div>
      <div id="symCatalogTableContainer" style="overflow-x: auto;"></div>
      <div id="symPager" class="card-actions mt-2"></div>
    </div>
  `;
  container.appendChild(section);

  const data = brokerData.symbols || [];
  const searchEl = section.querySelector("#symSearch");
  const groupEl = section.querySelector("#symGroup");
  const summaryEl = section.querySelector("#symCatalogSummary");
  const tableContainer = section.querySelector("#symCatalogTableContainer");
  const pagerEl = section.querySelector("#symPager");
  const pageSize = 100;
  let page = 1;
  let debounceTimer = null;

  const getFiltered = () => {
    const q = searchEl.value.toLowerCase().trim();
    const g = groupEl.value.toLowerCase();

    return data.filter((s) => {
      const mText = !q || s.name.toLowerCase().includes(q) || s.description.toLowerCase().includes(q);

      let mGroup = true;
      if (g !== "all") {
        const path = s.path.toLowerCase();
        if (g === "forex" && !(path.includes("forex") || path.includes("fx"))) mGroup = false;
        if (g === "crypto" && !(path.includes("crypto") || path.includes("coin"))) mGroup = false;
        if (g === "indices" && !(path.includes("index") || path.includes("indices"))) mGroup = false;
        if (g === "metals" && !(path.includes("metal") || path.includes("gold") || path.includes("silver"))) mGroup = false;
        if (g === "energy" && !(path.includes("energy") || path.includes("oil") || path.includes("gas"))) mGroup = false;
      }
      return mText && mGroup;
    });
  };

  const renderTable = () => {
    const filtered = getFiltered();
    const totalPages = Math.max(1, Math.ceil(filtered.length / pageSize));
    page = Math.min(Math.max(page, 1), totalPages);

    if (filtered.length === 0) {
      summaryEl.textContent = "No symbols match the current filter.";
      tableContainer.innerHTML = "<p>No broker symbols match the filter.</p>";
      pagerEl.innerHTML = "";
      return;
    }

    const start = (page - 1) * pageSize;
    const end = start + pageSize;
    const toRender = filtered.slice(start, end);
    summaryEl.textContent = `Showing ${start + 1}-${Math.min(end, filtered.length)} of ${filtered.length} matching symbols`;

    let html = `<table class="table" style="font-size: 0.9em; margin-top: 10px;">
      <thead>
        <tr>
          <th>Name</th>
          <th>Description</th>
          <th>Spread</th>
          <th>Digits</th>
          <th>Volume (Min - Max)</th>
          <th>Trade Mode</th>
          <th>Configured</th>
        </tr>
      </thead>
      <tbody>`;
    toRender.forEach((s) => {
      const confBadge = s.is_configured
          ? `<span class="badge" style="background: var(--success-color);">Yes</span>`
          : `<span class="badge" style="background: #555;">No</span>`;

      html += `<tr>
        <td style="font-weight: bold; color: var(--primary-color);">${s.name}</td>
        <td>${s.description}</td>
        <td>${s.spread}</td>
        <td>${s.digits}</td>
        <td>${s.volume_min} - ${s.volume_max}</td>
        <td>${s.trade_mode}</td>
        <td>${confBadge}</td>
      </tr>`;
    });
    html += `</tbody></table>`;
    tableContainer.innerHTML = html;

    pagerEl.innerHTML = `
      <button class="btn btn-sm btn-secondary" id="symPrev" ${page <= 1 ? "disabled" : ""}>Previous</button>
      <span class="small">Page ${page} / ${totalPages}</span>
      <button class="btn btn-sm btn-secondary" id="symNext" ${page >= totalPages ? "disabled" : ""}>Next</button>
    `;
    pagerEl.querySelector("#symPrev")?.addEventListener("click", () => {
      page -= 1;
      renderTable();
    });
    pagerEl.querySelector("#symNext")?.addEventListener("click", () => {
      page += 1;
      renderTable();
    });
  };

  const debouncedRender = () => {
    if (debounceTimer) {
      clearTimeout(debounceTimer);
    }
    debounceTimer = setTimeout(() => {
      page = 1;
      renderTable();
    }, 150);
  };

  searchEl.addEventListener("input", debouncedRender);
  groupEl.addEventListener("change", () => {
    page = 1;
    renderTable();
  });

  if (data.length > 0) renderTable();
  else tableContainer.innerHTML = "<p>Failed to load any symbols from the broker.</p>";
}
