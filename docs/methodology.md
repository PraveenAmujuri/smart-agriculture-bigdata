# Big Data Methodology: Smart Agriculture Analytics

## 1. Pipeline Architecture
This project implements a scalable, distributed Big Data analytics workflow to discover agro-ecological zones across US agricultural counties from 1981 to 2020 using Apache Hadoop and Apache Mahout.

```
+-------------------------------------------------------------+
|               Cornell USCrop Big Data Dataset               |
|            (124,320 County-Years x 6,322 Features)          |
+-------------------------------------------------------------+
                              |
                              v
+-------------------------------------------------------------+
|            Feature Selection & Separation Stage             |
|  - Identifiers & Yields Preserved: cols 0-7                 |
|  - Selected Features (1,322): PRISM, NLDAS, gSSURGO         |
|  - Highly Sparse Survey Features Excluded: cols 1204-6195   |
+-------------------------------------------------------------+
                              |
                              v
+-------------------------------------------------------------+
|              Preprocessing & Scaling (Python/NumPy)         |
|  - NLDAS Mean Imputation (0.02% missing)                    |
|  - Feature-wise Min-Max Normalization to [0.0, 1.0]         |
|  - Outputs: clustering_data.csv & metadata.csv              |
+-------------------------------------------------------------+
                              |
                              v
+-------------------------------------------------------------+
|                 HDFS Vector Ingestion                       |
|  - Streamed to /user/praveen/smart_agriculture/input/       |
|  - Converted via Mahout InputDriver to SequenceFiles        |
|  - Stored in /user/praveen/smart_agriculture/vectors/       |
+-------------------------------------------------------------+
                              |
                              v
+-------------------------------------------------------------+
|             Distributed MapReduce Clustering on YARN        |
|  - Apache Mahout K-Means (k=5, 10 iterations)               |
|  - Apache Mahout Fuzzy K-Means (k=5, m=2.0, 10 iterations)  |
+-------------------------------------------------------------+
                              |
                              v
+-------------------------------------------------------------+
|             Model Evaluation & Interpretation               |
|  - WCSS / Inertia Calculation & Inter-Cluster Distance      |
|  - Cluster Assignment to Metadata Join                      |
|  - Agro-Climatic Zone & Crop Yield Analysis                 |
+-------------------------------------------------------------+
```

## 2. Feature Selection Strategy
The raw dataset spans 6,322 features for 124,320 county-year observations:
- **Columns 0–1 (Identifiers):** `fips` (county code) and `year` (1981–2020). Preserved separately.
- **Columns 2–7 (Crop Yields):** Corn, Upland Cotton, Grain Sorghum, Soybeans, Spring Wheat, and Winter Wheat. Excluded from clustering so that environmental patterns form unsupervised clusters without bias, and preserved for outcome validation.
- **Columns 8–371 (PRISM Climate):** 364 features capturing weekly precipitation, vapor pressure, and temperature extremes. 0.00% missing values.
- **Columns 372–1203 (NLDAS Land Surface):** 832 features detailing solar radiation, convective precipitation, and wind speeds. 0.02% missing values (imputed using global feature mean).
- **Columns 1204–6195 (USDA Survey Crop Progress):** 4,992 features. Excluded due to extreme sparsity (93.38% missing), which would degrade distance metrics.
- **Columns 6196–6321 (gSSURGO Soil Quality):** 126 features capturing soil organic carbon, bulk density, available water capacity, and pH. 0.00% missing values.
- **Total Selected Clustering Features:** 1,322 normalized numerical dimensions.

## 3. Data Preprocessing & Normalization
- **Memory-Mapped Streaming:** Used NumPy memory-mapping (`mmap_mode="r"`) to process chunks without loading the 6 GB dataset into RAM.
- **Min-Max Scaling:** Scaled each selected feature independently into $[0.0, 1.0]$:
  $$x_{\text{norm}} = \frac{x - x_{\min}}{x_{\max} - x_{\min}}$$
- **Order Preservation:** Exact row order from row 0 to 124,319 was maintained across both `clustering_data.csv` and `metadata.csv`.

## 4. Distributed Processing on Hadoop & Apache Mahout
- **HDFS Staging:** The normalized 1,322-dimensional text vectors were transferred to HDFS at `/user/praveen/smart_agriculture/input/clustering_data.txt`.
- **Vector Transformation:** Executed `org.apache.mahout.clustering.conversion.InputDriver` via Hadoop MapReduce to generate binary `(Text, VectorWritable)` SequenceFiles in `/user/praveen/smart_agriculture/vectors/`.
- **MapReduce Execution:** Both clustering algorithms ran in true distributed mode by explicitly unsetting `MAHOUT_LOCAL=""` and submitting jobs to YARN's ResourceManager on port 8032.
- **K-Means Configuration:** $k=5$, max iterations = 10, convergence delta = 0.01, measure = Squared Euclidean Distance, classification enabled (`-cl`).
- **Fuzzy K-Means Configuration:** $k=5$, fuzziness exponent $m=2.0$, max iterations = 10, convergence delta = 0.01, measure = Squared Euclidean Distance, classification enabled (`-cl`).

## 5. Model Evaluation Criteria
Rather than improper classification metrics, unsupervised evaluation used:
1. **Within-Cluster Sum of Squares (WCSS / Inertia):** Measures compactness:
   $$\text{WCSS} = \sum_{k=1}^K \sum_{x \in S_k} \| x - \mu_k \|^2$$
2. **Inter-Cluster Centroid Separation:** Pairwise Euclidean distances between cluster centroids to measure distinctness.
3. **Execution Runtime & Convergence Efficiency:** Total Wall-clock time on Hadoop MapReduce.
4. **Agro-Ecological Interpretability:** Crop yield distributions (mean, median, standard deviation) across clusters when joined with preserved USDA yield figures.
