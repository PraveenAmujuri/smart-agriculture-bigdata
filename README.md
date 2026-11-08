# Smart Agriculture Big Data Analytics Using Hadoop and Apache Mahout

A Big Data analytics project using **Apache Hadoop (HDFS, YARN)** and **Apache Mahout** to analyze and cluster US agricultural weather, land-surface, and soil patterns (124,320 county-year observations across 1,322 features) from 1981 to 2020.

---

## 🌾 Project Overview

- **Dataset:** Cornell USCrop Big Data Dataset (124,320 observations $\times$ 6,322 features).
- **Selected Clustering Features:** 1,322 features (PRISM weather, NLDAS land surface, gSSURGO soil quality).
- **Target Analysis:** 6 crop yields (Corn, Cotton, Sorghum, Soybeans, Spring Wheat, Winter Wheat) preserved separately to validate cluster interpretations.
- **Distributed Processing:** Apache Hadoop 3.3.6 (HDFS, YARN MapReduce) and Apache Mahout 0.13.0.
- **Algorithms:** Distributed K-Means ($k=5$) vs. Fuzzy K-Means ($k=5, m=2.0$).

---

## 🏗️ Repository Architecture

```
Smart-Agriculture-BigData/
├── data/
│   ├── raw/                 # Cornell USCrop dataset (.npz)
│   ├── extracted/           # Extracted matrix data (.npy)
│   └── processed/           # Normalized clustering data and metadata
├── docs/
│   └── methodology.md       # Detailed technical architecture and math
├── reports/
│   └── final_report.md      # Comprehensive academic project report
├── results/
│   ├── model_comparison.csv # K-Means vs Fuzzy K-Means benchmarks
│   ├── crop_yield_by_cluster.csv # Yield distributions across clusters
│   ├── cluster_agroclimatic_profiles.csv # Identified agricultural zones
│   ├── cluster_assignments.csv # County-year cluster mappings
│   ├── kmeans_clusters_dump.txt  # Mahout K-Means cluster centers
│   └── fkmeans_clusters_dump.txt # Mahout Fuzzy K-Means cluster centers
├── src/
│   ├── analysis/
│   │   ├── analyze_missing_values.py # Missingness analysis
│   │   ├── select_features.py        # Feature partition script
│   │   ├── preprocess.py             # Normalization and imputation
│   │   ├── evaluate_models.py        # Model evaluation & WCSS
│   │   └── analyze_crop_yields.py    # Crop yield linkage analysis
│   └── mahout/
│       ├── run_kmeans.sh             # Mahout K-Means MapReduce job
│       └── run_fuzzy_kmeans.sh       # Mahout Fuzzy K-Means MapReduce job
└── README.md
```

---

## 🚀 Execution Workflow

### 1. Feature Selection and Preprocessing
```bash
# Impute missing values and normalize 1,322 features to [0, 1]
python3 src/analysis/preprocess.py
```

### 2. Ingest Vectors into HDFS
```bash
# Upload converted vectors to HDFS
hdfs dfs -mkdir -p /user/praveen/smart_agriculture/input
hdfs dfs -put data/processed/clustering_data.txt /user/praveen/smart_agriculture/input/

# Convert text vectors to Mahout SequenceFiles via MapReduce
MAHOUT_LOCAL="" mahout seqdirectory \
  -i /user/praveen/smart_agriculture/input \
  -o /user/praveen/smart_agriculture/vectors \
  -xm mapreduce
```

### 3. Run Mahout Distributed Clustering
```bash
# Run K-Means on Hadoop YARN
bash src/mahout/run_kmeans.sh

# Run Fuzzy K-Means on Hadoop YARN
bash src/mahout/run_fuzzy_kmeans.sh
```

### 4. Evaluate Models and Analyze Crop Yields
```bash
# Compute WCSS, separation, and model comparison
python3 src/analysis/evaluate_models.py

# Link clusters with USDA crop yields and export profiles
python3 src/analysis/analyze_crop_yields.py
```

---

## 📊 Summary of Results

### Clustering Performance on Hadoop MapReduce

| Metric | Apache Mahout K-Means | Apache Mahout Fuzzy K-Means | Winner |
| :--- | :---: | :---: | :---: |
| **MapReduce Runtime** | **3.92 min** | 9.80 min | **K-Means (2.5x faster)** |
| **Within-Cluster Sum of Squares (WCSS)** | **1,568,053.21** | 2,152,892.04 | **K-Means (27.2% tighter)** |
| **Mean Inter-Cluster Separation** | **5.3406** | 2.2515 | **K-Means (more distinct)** |

### Agro-Climatic Zone Discovery

Without seeing crop yields during training, environmental clustering accurately discovered America's major agricultural belts:

- **Cluster 1 (Midwest Corn-Soy Belt):** Highest corn (126.1 bu/ac) and soybean (40.7 bu/ac) yields.
- **Cluster 2 (Southern Cotton Belt):** Dominates US cotton production (698.3 lbs/ac).
- **Cluster 0 (Northern Plains Wheat Zone):** Produces 64% of all US spring wheat (42.6 bu/ac).
- **Cluster 3 (Central Transition Zone):** High grain sorghum (69.7 bu/ac) and diversified grain.
- **Cluster 4 (Western Semi-Arid Zone):** Lower overall crop yields due to water stress.
