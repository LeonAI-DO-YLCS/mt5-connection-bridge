import { api } from "./app.js";

let _capabilitiesData = null;

const TRADE_MODE_BADGES = {
  0: { label: "Disabled", className: "badge-disabled" },
  1: { label: "Long Only", className: "badge-longonly" },
  2: { label: "Short Only", className: "badge-shortonly" },
  3: { label: "Close Only", className: "badge-closeonly" },
  4: { label: "Full", className: "badge-full" },
};

function ensureBadgeStyles() {
  if (document.getElementById("symbol-browser-badge-styles")) {
    return;
  }
  const style = document.createElement("style");
  style.id = "symbol-browser-badge-styles";
  style.textContent = `
    .mode-badge { display:inline-block; padding:2px 8px; border-radius:4px; font-size:11px; font-weight:600; }
    .badge-full { background:#19875422; color:#198754; border:1px solid #198754; }
    .badge-longonly { background:#0d6efd22; color:#0d6efd; border:1px solid #0d6efd; }
    .badge-shortonly { background:#fd7e1422; color:#fd7e14; border:1px solid #fd7e14; }
    .badge-closeonly { background:#ffc10722; color:#856404; border:1px solid #ffc107; }
    .badge-disabled { background:#dc354522; color:#dc3545; border:1px solid #dc3545; }
  `;
  document.head.appendChild(style);
}

function tradeModeBadge(mode, tradeModeLabel) {
  const info = TRADE_MODE_BADGES[mode] || TRADE_MODE_BADGES[4];
  const label = tradeModeLabel || info.label;
  return `<span class="mode-badge ${info.className}">${label}</span>`;
}

export async function renderBrokerSymbols(container) {
  ensureBadgeStyles();

  const section = document.createElement("div");
  section.innerHTML = `
    <hr style="margin: 30px 0; border: 1px solid var(--border-color);" />
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px;">
      <h3 style="margin:0;">Broker Symbols Catalog</h3>
      <button id="symRefreshBtn" class="btn btn-sm btn-secondary">⟳ Refresh</button>
    </div>
    <div class="panel">
      <div class="grid two" style="margin-bottom: 12px; grid-template-columns: 1fr 180px 180px;">
        <input type="text" id="symSearch" placeholder="Search by name or description…" />
        <select id="symCategory">
          <option value="all">All Categories</option>
        </select>
        <select id="symSubcategory">
          <option value="all">All Subcategories</option>
        </select>
      </div>
      <div style="margin-bottom:10px;">
        <label style="font-size:13px;">
          <input type="checkbox" id="showDisabledSymbols" />
          Show disabled symbols
        </label>
      </div>
      <div id="symCatalogSummary" class="small" style="margin-bottom: 10px;"></div>
      <div id="symCatalogTableContainer" style="overflow-x: auto;"></div>
      <div id="symPager" class="card-actions mt-2"></div>
    </div>
  `;
  container.appendChild(section);

  const searchEl = section.querySelector("#symSearch");
  const categoryEl = section.querySelector("#symCategory");
  const subcategoryEl = section.querySelector("#symSubcategory");
  const showDisabledEl = section.querySelector("#showDisabledSymbols");
  const summaryEl = section.querySelector("#symCatalogSummary");
  const tableContainer = section.querySelector("#symCatalogTableContainer");
  const pagerEl = section.querySelector("#symPager");
  const refreshBtn = section.querySelector("#symRefreshBtn");

  const pageSize = 100;
  let page = 1;
  let debounceTimer = null;

  async function loadCapabilities(forceRefresh = false) {
    if (forceRefresh) {
      await api("/broker-capabilities/refresh", { method: "POST" });
      _capabilitiesData = null;
    }
    if (_capabilitiesData === null) {
      _capabilitiesData = await api("/broker-capabilities");
    }
    return _capabilitiesData;
  }

  function populateCategoryDropdown(categories) {
    categoryEl.innerHTML = `<option value="all">All Categories</option>`;
    Object.keys(categories).sort().forEach((category) => {
      const option = document.createElement("option");
      option.value = category;
      option.textContent = category;
      categoryEl.appendChild(option);
    });
  }

  function populateSubcategoryDropdown(categories) {
    const category = categoryEl.value;
    subcategoryEl.innerHTML = `<option value="all">All Subcategories</option>`;
    if (category === "all") {
      subcategoryEl.disabled = true;
      return;
    }
    (categories[category] || []).forEach((subcategory) => {
      const option = document.createElement("option");
      option.value = subcategory;
      option.textContent = subcategory;
      subcategoryEl.appendChild(option);
    });
    subcategoryEl.disabled = false;
  }

  function getFilteredSymbols(symbols) {
    const query = searchEl.value.toLowerCase().trim();
    const selectedCategory = categoryEl.value;
    const selectedSubcategory = subcategoryEl.value;
    const showDisabled = Boolean(showDisabledEl.checked);

    return symbols.filter((symbol) => {
      if (!showDisabled && Number(symbol.trade_mode) === 0) {
        return false;
      }
      if (query) {
        const haystack = `${symbol.name} ${symbol.description}`.toLowerCase();
        if (!haystack.includes(query)) {
          return false;
        }
      }
      if (selectedCategory !== "all" && symbol.category !== selectedCategory) {
        return false;
      }
      if (selectedSubcategory !== "all" && symbol.subcategory !== selectedSubcategory) {
        return false;
      }
      return true;
    });
  }

  function renderTable(symbols) {
    const filtered = getFilteredSymbols(symbols);
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
    const rows = filtered.slice(start, end);
    summaryEl.textContent = `Showing ${start + 1}–${Math.min(end, filtered.length)} of ${filtered.length} matching symbols`;

    let html = `<table class="table" style="font-size: 0.85em; margin-top: 10px;">
      <thead>
        <tr>
          <th>Name</th>
          <th>Description</th>
          <th>Category</th>
          <th>Subcategory</th>
          <th>Spread</th>
          <th>Volume (Min – Max)</th>
          <th>Trade Mode</th>
          <th>Filling Modes</th>
          <th>Configured</th>
        </tr>
      </thead>
      <tbody>`;

    rows.forEach((symbol) => {
      const configuredBadge = symbol.is_configured
        ? `<span class="badge" style="background: var(--success-color);">Yes</span>`
        : `<span class="badge" style="background: #555;">No</span>`;

      const fillingModes = Array.isArray(symbol.supported_filling_modes)
        ? symbol.supported_filling_modes.join(", ")
        : "RETURN";

      html += `<tr>
        <td style="font-weight:bold;color:var(--primary-color);">${symbol.name}</td>
        <td>${symbol.description}</td>
        <td>${symbol.category || "Other"}</td>
        <td>${symbol.subcategory || ""}</td>
        <td>${symbol.spread}</td>
        <td>${symbol.volume_min} – ${symbol.volume_max}</td>
        <td>${tradeModeBadge(Number(symbol.trade_mode), symbol.trade_mode_label)}</td>
        <td>${fillingModes}</td>
        <td>${configuredBadge}</td>
      </tr>`;
    });

    html += `</tbody></table>`;
    tableContainer.innerHTML = html;

    pagerEl.innerHTML = `
      <button class="btn btn-sm btn-secondary" id="symPrev" ${page <= 1 ? "disabled" : ""}>◀ Prev</button>
      <span class="small" style="margin:0 8px;">Page ${page} / ${totalPages}</span>
      <button class="btn btn-sm btn-secondary" id="symNext" ${page >= totalPages ? "disabled" : ""}>Next ▶</button>
    `;
    pagerEl.querySelector("#symPrev")?.addEventListener("click", () => { page -= 1; renderTable(symbols); });
    pagerEl.querySelector("#symNext")?.addEventListener("click", () => { page += 1; renderTable(symbols); });
  }

  try {
    const capabilities = await loadCapabilities(false);
    const symbols = capabilities.symbols || [];
    const categories = capabilities.categories || {};

    populateCategoryDropdown(categories);
    populateSubcategoryDropdown(categories);
    renderTable(symbols);

    const debouncedRender = () => {
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(() => {
        page = 1;
        renderTable(symbols);
      }, 150);
    };

    searchEl.addEventListener("input", debouncedRender);
    showDisabledEl.addEventListener("change", () => {
      page = 1;
      renderTable(symbols);
    });
    categoryEl.addEventListener("change", () => {
      populateSubcategoryDropdown(categories);
      page = 1;
      renderTable(symbols);
    });
    subcategoryEl.addEventListener("change", () => {
      page = 1;
      renderTable(symbols);
    });

    refreshBtn.addEventListener("click", async () => {
      refreshBtn.disabled = true;
      refreshBtn.textContent = "Refreshing…";
      try {
        const refreshed = await loadCapabilities(true);
        const refreshedSymbols = refreshed.symbols || [];
        const refreshedCategories = refreshed.categories || {};
        populateCategoryDropdown(refreshedCategories);
        populateSubcategoryDropdown(refreshedCategories);
        page = 1;
        renderTable(refreshedSymbols);
        summaryEl.textContent = `✅ Refreshed: ${refreshed.symbol_count} symbols at ${refreshed.fetched_at}`;
      } catch (error) {
        summaryEl.textContent = `❌ Refresh failed: ${error.message}`;
      } finally {
        refreshBtn.disabled = false;
        refreshBtn.textContent = "⟳ Refresh";
      }
    });
  } catch (error) {
    tableContainer.innerHTML = `<p>Failed to load broker symbols: ${error.message}</p>`;
  }
}

