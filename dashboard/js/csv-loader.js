/**
 * CSV Loader & Data Manager
 * Handles robust asynchronous loading across different server working directories,
 * Papa Parse parsing, in-memory caching, search, sorting, and pagination.
 */

const CSVManager = (function () {
  const CSV_FILES = {
    model_comparison: {
      name: "model_comparison.csv",
      title: "Model Comparison",
      filename: "model_comparison.csv"
    },
    clustering_quality_metrics: {
      name: "clustering_quality_metrics.csv",
      title: "Clustering Quality Metrics",
      filename: "clustering_quality_metrics.csv"
    },
    cluster_environmental_profiles: {
      name: "cluster_environmental_profiles.csv",
      title: "Cluster Environmental Profiles",
      filename: "cluster_environmental_profiles.csv"
    },
    cluster_yield_analysis: {
      name: "cluster_yield_analysis.csv",
      title: "Cluster Crop Yield Analysis",
      filename: "cluster_yield_analysis.csv"
    },
    cluster_assignments: {
      name: "cluster_assignments.csv",
      title: "Cluster Assignments (124,320 rows)",
      filename: "cluster_assignments.csv"
    }
  };

  const cache = {};

  /**
   * Resolves the working path for a CSV file regardless of whether the HTTP server
   * was started in the project root or inside the dashboard/ folder.
   */
  async function resolveCSVUrl(filename) {
    const candidatePaths = [
      `results/${filename}`,
      `../results/${filename}`,
      `/results/${filename}`,
      `/dashboard/results/${filename}`
    ];

    for (const p of candidatePaths) {
      try {
        const res = await fetch(p, { method: "HEAD" });
        if (res.ok) {
          return p;
        }
      } catch (err) {
        // Continue checking next candidate
      }
    }

    // Default fallback
    return `results/${filename}`;
  }

  /**
   * Fetch and parse CSV using Papa Parse
   */
  async function loadCSV(fileKey) {
    if (cache[fileKey]) {
      return cache[fileKey];
    }

    const config = CSV_FILES[fileKey];
    if (!config) {
      throw new Error(`Unknown CSV key: ${fileKey}`);
    }

    const targetUrl = await resolveCSVUrl(config.filename);

    return new Promise((resolve, reject) => {
      Papa.parse(targetUrl, {
        download: true,
        header: true,
        dynamicTyping: true,
        skipEmptyLines: true,
        complete: function (results) {
          if (results.errors && results.errors.length > 0 && (!results.data || results.data.length === 0)) {
            reject(new Error(results.errors[0].message || "Failed to parse CSV"));
            return;
          }

          const columns = results.meta.fields || [];
          const data = results.data;

          const parsedObj = {
            key: fileKey,
            filename: config.name,
            title: config.title,
            columns: columns,
            data: data,
            totalRows: data.length,
            totalColumns: columns.length,
            targetUrl: targetUrl
          };

          cache[fileKey] = parsedObj;
          resolve(parsedObj);
        },
        error: function (err) {
          console.error(`Error loading CSV from ${targetUrl}:`, err);
          reject(err);
        }
      });
    });
  }

  /**
   * Filter, sort, and paginate cached data
   */
  function queryData(fileKey, options = {}) {
    const dataset = cache[fileKey];
    if (!dataset) {
      throw new Error(`Dataset not loaded in cache: ${fileKey}`);
    }

    const {
      search = "",
      sortCol = null,
      sortDir = "asc",
      page = 1,
      pageSize = 25
    } = options;

    let filtered = dataset.data;

    // Search filter across all fields
    const term = search.trim().toLowerCase();
    if (term) {
      filtered = filtered.filter(row => {
        return Object.values(row).some(val => {
          if (val === null || val === undefined) return false;
          return String(val).toLowerCase().includes(term);
        });
      });
    }

    // Sorting
    if (sortCol && dataset.columns.includes(sortCol)) {
      filtered = [...filtered].sort((a, b) => {
        const valA = a[sortCol];
        const valB = b[sortCol];

        if (valA === null || valA === undefined) return 1;
        if (valB === null || valB === undefined) return -1;

        if (typeof valA === "number" && typeof valB === "number") {
          return sortDir === "asc" ? valA - valB : valB - valA;
        }

        const strA = String(valA).toLowerCase();
        const strB = String(valB).toLowerCase();
        if (strA < strB) return sortDir === "asc" ? -1 : 1;
        if (strA > strB) return sortDir === "asc" ? 1 : -1;
        return 0;
      });
    }

    const totalFilteredRows = filtered.length;
    const totalPages = Math.ceil(totalFilteredRows / pageSize) || 1;
    const validPage = Math.min(Math.max(1, page), totalPages);
    const startIdx = (validPage - 1) * pageSize;
    const endIdx = startIdx + pageSize;
    const pageRows = filtered.slice(startIdx, endIdx);

    return {
      key: fileKey,
      columns: dataset.columns,
      rows: pageRows,
      page: validPage,
      pageSize: pageSize,
      totalRows: dataset.totalRows,
      totalFilteredRows: totalFilteredRows,
      totalPages: totalPages,
      startIdx: totalFilteredRows === 0 ? 0 : startIdx + 1,
      endIdx: Math.min(endIdx, totalFilteredRows)
    };
  }

  /**
   * Trigger CSV download
   */
  function downloadCSV(fileKey) {
    const dataset = cache[fileKey];
    if (!dataset) return;

    if (dataset.targetUrl) {
      const a = document.createElement("a");
      a.href = dataset.targetUrl;
      a.download = dataset.filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      return;
    }

    const csvContent = Papa.unparse(dataset.data);
    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = dataset.filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }

  return {
    CSV_FILES,
    loadCSV,
    queryData,
    downloadCSV,
    getCached: (key) => cache[key]
  };
})();
