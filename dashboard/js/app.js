/**
 * Main Application Controller
 * Handles UI interactions, CSV tab switching, table rendering,
 * search debouncing, column sorting, pagination, and scroll-spy.
 */

document.addEventListener("DOMContentLoaded", function () {
  const state = {
    activeTab: "model_comparison",
    search: "",
    sortCol: null,
    sortDir: "asc",
    page: 1,
    pageSize: 25,
    searchTimeout: null
  };

  const elements = {
    csvTabs: document.querySelectorAll(".csv-tab-btn"),
    tableContainer: document.getElementById("tableContainer"),
    tableHead: document.getElementById("tableHead"),
    tableBody: document.getElementById("tableBody"),
    tableSearch: document.getElementById("tableSearch"),
    pageSizeSelect: document.getElementById("pageSizeSelect"),
    paginationInfo: document.getElementById("paginationInfo"),
    paginationControls: document.getElementById("paginationControls"),
    rowBadge: document.getElementById("rowBadge"),
    tableLoading: document.getElementById("tableLoading"),
    tableEmpty: document.getElementById("tableEmpty"),
    downloadBtn: document.getElementById("downloadActiveBtn"),
    sidebarLinks: document.querySelectorAll(".nav-menu .nav-item a")
  };

  async function init() {
    if (typeof ChartsManager !== "undefined") {
      ChartsManager.init();
    }
    setupEventListeners();
    setupScrollSpy();
    await loadActiveTab();
  }

  /**
   * Scroll-Spy: updates sidebar active focus dynamically on scroll
   */
  function setupScrollSpy() {
    const sectionIds = ["overview", "model-comparison", "cluster-distribution", "csv-explorer"];
    const navItems = document.querySelectorAll(".nav-menu .nav-item");

    function setActiveNav(id) {
      if (!id) return;
      navItems.forEach(item => {
        const link = item.querySelector("a");
        if (!link) return;
        const href = (link.getAttribute("href") || "").replace(/^#/, "");
        if (href === id) {
          item.classList.add("active");
        } else {
          item.classList.remove("active");
        }
      });
    }

    function onScroll() {
      const scrollY = window.pageYOffset || document.documentElement.scrollTop || document.body.scrollTop || 0;
      const viewportHeight = window.innerHeight;
      const scrollHeight = document.documentElement.scrollHeight || document.body.scrollHeight;

      // If user has scrolled near bottom of page, activate the last section
      if (scrollY > 100 && (viewportHeight + scrollY >= scrollHeight - 100)) {
        setActiveNav("csv-explorer");
        return;
      }

      // Check sections: whichever section's top is at or above the trigger line
      const triggerY = 220;
      let currentSectionId = "overview";

      for (const id of sectionIds) {
        const sec = document.getElementById(id);
        if (!sec) continue;
        const rect = sec.getBoundingClientRect();
        if (rect.top <= triggerY) {
          currentSectionId = id;
        }
      }

      setActiveNav(currentSectionId);
    }

    window.addEventListener("scroll", onScroll, { passive: true });
    document.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", onScroll, { passive: true });

    // Initial check
    setTimeout(onScroll, 100);
  }

  function setupEventListeners() {
    // CSV Tab Switching
    elements.csvTabs.forEach(tab => {
      tab.addEventListener("click", async () => {
        const tabKey = tab.getAttribute("data-tab");
        if (tabKey === state.activeTab) return;

        elements.csvTabs.forEach(t => t.classList.remove("active"));
        tab.classList.add("active");

        state.activeTab = tabKey;
        state.search = "";
        state.sortCol = null;
        state.sortDir = "asc";
        state.page = 1;
        if (elements.tableSearch) elements.tableSearch.value = "";

        await loadActiveTab();
      });
    });

    // Search filter with debounce
    if (elements.tableSearch) {
      elements.tableSearch.addEventListener("input", (e) => {
        clearTimeout(state.searchTimeout);
        state.searchTimeout = setTimeout(() => {
          state.search = e.target.value;
          state.page = 1;
          renderTable();
        }, 180);
      });
    }

    // Page size dropdown
    if (elements.pageSizeSelect) {
      elements.pageSizeSelect.addEventListener("change", (e) => {
        state.pageSize = parseInt(e.target.value, 10);
        state.page = 1;
        renderTable();
      });
    }

    // CSV Download
    if (elements.downloadBtn) {
      elements.downloadBtn.addEventListener("click", () => {
        CSVManager.downloadCSV(state.activeTab);
      });
    }

    // Sidebar smooth scroll on click
    elements.sidebarLinks.forEach(link => {
      link.addEventListener("click", (e) => {
        const href = link.getAttribute("href");
        if (href && href.startsWith("#")) {
          e.preventDefault();
          const target = document.querySelector(href);
          if (target) {
            target.scrollIntoView({ behavior: "smooth" });
            const navItem = link.closest(".nav-item");
            if (navItem) {
              document.querySelectorAll(".nav-menu .nav-item").forEach(i => i.classList.remove("active"));
              navItem.classList.add("active");
            }
          }
        }
      });
    });
  }

  async function loadActiveTab() {
    showLoading(true);
    try {
      await CSVManager.loadCSV(state.activeTab);
      showLoading(false);
      renderTable();
    } catch (err) {
      showLoading(false);
      console.error("Error loading CSV:", err);
      showErrorState(err.message);
    }
  }

  function renderTable() {
    const result = CSVManager.queryData(state.activeTab, {
      search: state.search,
      sortCol: state.sortCol,
      sortDir: state.sortDir,
      page: state.page,
      pageSize: state.pageSize
    });

    if (elements.rowBadge) {
      elements.rowBadge.textContent = `${result.totalFilteredRows.toLocaleString()} rows (${result.columns.length} columns)`;
    }

    if (result.totalFilteredRows === 0) {
      elements.tableHead.innerHTML = "";
      elements.tableBody.innerHTML = "";
      if (elements.tableEmpty) elements.tableEmpty.style.display = "block";
      if (elements.paginationInfo) elements.paginationInfo.textContent = "No matching rows found";
      if (elements.paginationControls) elements.paginationControls.innerHTML = "";
      return;
    } else {
      if (elements.tableEmpty) elements.tableEmpty.style.display = "none";
    }

    // Render Headers
    let theadHTML = "<tr>";
    result.columns.forEach(col => {
      let icon = "↕";
      if (state.sortCol === col) {
        icon = state.sortDir === "asc" ? "▲" : "▼";
      }
      theadHTML += `<th data-col="${col}">${formatColumnName(col)} <span style="font-size:10px; color:#94a3b8;">${icon}</span></th>`;
    });
    theadHTML += "</tr>";
    elements.tableHead.innerHTML = theadHTML;

    // Attach sort listeners
    elements.tableHead.querySelectorAll("th").forEach(th => {
      th.addEventListener("click", () => {
        const col = th.getAttribute("data-col");
        if (state.sortCol === col) {
          state.sortDir = state.sortDir === "asc" ? "desc" : "asc";
        } else {
          state.sortCol = col;
          state.sortDir = "asc";
        }
        renderTable();
      });
    });

    // Render Body Rows
    let tbodyHTML = "";
    result.rows.forEach(row => {
      tbodyHTML += "<tr>";
      result.columns.forEach(col => {
        const val = row[col];
        tbodyHTML += `<td>${formatCellValue(col, val)}</td>`;
      });
      tbodyHTML += "</tr>";
    });
    elements.tableBody.innerHTML = tbodyHTML;

    // Render Pagination
    renderPagination(result);
  }

  function formatColumnName(col) {
    return col
      .replace(/_/g, " ")
      .replace(/\b\w/g, c => c.toUpperCase());
  }

  function formatCellValue(col, val) {
    if (val === null || val === undefined || val === "") {
      return `<span style="color:#94a3b8;">—</span>`;
    }
    if (typeof val === "number") {
      if (Number.isInteger(val)) {
        return val.toLocaleString();
      }
      return val.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 4 });
    }
    return String(val);
  }

  function renderPagination(result) {
    if (elements.paginationInfo) {
      elements.paginationInfo.textContent = `Showing ${result.startIdx.toLocaleString()}–${result.endIdx.toLocaleString()} of ${result.totalFilteredRows.toLocaleString()} rows`;
    }

    if (!elements.paginationControls) return;

    const { page, totalPages } = result;
    let html = "";

    html += `<button class="page-btn" ${page <= 1 ? "disabled" : ""} data-page="${page - 1}">Prev</button>`;

    const maxButtons = 5;
    let startPage = Math.max(1, page - 2);
    let endPage = Math.min(totalPages, startPage + maxButtons - 1);
    if (endPage - startPage < maxButtons - 1) {
      startPage = Math.max(1, endPage - maxButtons + 1);
    }

    if (startPage > 1) {
      html += `<button class="page-btn" data-page="1">1</button>`;
      if (startPage > 2) html += `<span style="padding:0 4px; color:#94a3b8;">…</span>`;
    }

    for (let p = startPage; p <= endPage; p++) {
      html += `<button class="page-btn ${p === page ? "active" : ""}" data-page="${p}">${p}</button>`;
    }

    if (endPage < totalPages) {
      if (endPage < totalPages - 1) html += `<span style="padding:0 4px; color:#94a3b8;">…</span>`;
      html += `<button class="page-btn" data-page="${totalPages}">${totalPages}</button>`;
    }

    html += `<button class="page-btn" ${page >= totalPages ? "disabled" : ""} data-page="${page + 1}">Next</button>`;
    elements.paginationControls.innerHTML = html;

    elements.paginationControls.querySelectorAll(".page-btn").forEach(btn => {
      btn.addEventListener("click", () => {
        const target = parseInt(btn.getAttribute("data-page"), 10);
        if (!isNaN(target) && target !== state.page && target >= 1 && target <= totalPages) {
          state.page = target;
          renderTable();
          elements.tableContainer.scrollTop = 0;
        }
      });
    });
  }

  function showLoading(isLoading) {
    if (elements.tableLoading) {
      elements.tableLoading.style.display = isLoading ? "block" : "none";
    }
    if (elements.tableContainer) {
      elements.tableContainer.style.opacity = isLoading ? "0.3" : "1";
    }
  }

  function showErrorState(msg) {
    if (elements.tableBody) {
      elements.tableBody.innerHTML = `<tr><td colspan="6" style="padding:30px; text-align:center; color:#dc2626;">
        Failed to load CSV: ${msg}
      </td></tr>`;
    }
  }

  init();
});
