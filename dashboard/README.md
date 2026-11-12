# Smart Agriculture Big Data - Results Explorer

A lightweight, static web explorer built with HTML5, CSS3, and Vanilla JavaScript for inspecting the clustering results, model comparison, and CSV files from the **Smart Agriculture Big Data Analytics** project.

---

## Dashboard Sections

The dashboard contains only four focused sections:

1. **Project Overview**:
   - Total Observations: `124,320` county-year records (1981–2020)
   - Original Columns: `6,322` columns
   - Selected Features: `1,322` continuous weather and soil variables
   - Number of Clusters: `5` clusters

2. **Model Comparison**:
   - Direct benchmark comparison table:
     - **Silhouette Score**: K-Means `0.1363` vs Fuzzy K-Means `0.0833`
     - **Davies–Bouldin Index**: K-Means `1.9229` vs Fuzzy K-Means `2.4350`
     - **Execution Time**: K-Means `9.80 min` vs Fuzzy K-Means `3.92 min`
     - **Iterations**: K-Means `10` vs Fuzzy K-Means `6`
   - Short summary of results.

3. **Cluster Distribution**:
   - Grouped bar chart comparing observation counts allocated across clusters 0 through 4 for K-Means and Fuzzy K-Means.

4. **CSV Results Explorer**:
   - Tabbed access to the project's actual CSV result files:
     - `model_comparison.csv`
     - `clustering_quality_metrics.csv`
     - `cluster_environmental_profiles.csv`
     - `cluster_yield_analysis.csv`
     - `cluster_assignments.csv` (124,320 rows)
   - Search filter across all columns.
   - Column sorting (click table headers to sort asc/desc).
   - Pagination controls (10, 25, 50, 100 rows per page).
   - Direct CSV download button.

---

## How to Run Locally

You can launch the web server from either the project root or the `dashboard/` directory:

### Option A: From the Project Root (Recommended)

```bash
# Run from ~/Smart-Agriculture-BigData
python3 -m http.server 8000
```
Then open: **`http://localhost:8000/`** (automatically opens the dashboard).

### Option B: From Inside `dashboard/`

```bash
# Run inside ~/Smart-Agriculture-BigData/dashboard
python3 -m http.server 8000
```
Then open: **`http://localhost:8000/`** (loads the dashboard and CSV files directly).

---

## Directory Structure

```text
dashboard/
├── index.html        # Compact HTML5 markup
├── css/
│   └── style.css     # Clean stylesheet
├── js/
│   ├── app.js        # Controller for search, sort, pagination, and tabs
│   ├── charts.js     # Chart.js grouped bar chart
│   └── csv-loader.js # Papa Parse CSV loader with multi-path resolution
├── results/ -> ../results  # Symlink for CSV access when served from dashboard/
└── README.md
```
