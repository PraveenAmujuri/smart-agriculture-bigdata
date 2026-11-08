# Final Project Report: Smart Agriculture Big Data Analytics

**Technologies Used:** Apache Hadoop 3.3.6, Apache Mahout 0.13.0, HDFS, YARN MapReduce, Python 3 / NumPy  
**Dataset:** Cornell USCrop Agricultural Big Data (124,320 observations x 6,322 features)  
**Task:** Unsupervised Agro-Climatic Clustering and Crop Yield Analysis  

---

## 1. Executive Summary

This project deployed an end-to-end Big Data analytics pipeline using Apache Hadoop and Apache Mahout to cluster 124,320 United States county-year agricultural observations (1981–2020). By selecting 1,322 environmental features spanning PRISM weather, NLDAS land-surface hydrology, and gSSURGO soil quality, we trained **K-Means** and **Fuzzy K-Means** distributed clustering models on Hadoop YARN.

Evaluating the resulting clusters against separately preserved USDA crop yield records revealed that the unsupervised environmental clusters directly correspond to the five primary agricultural production belts in the United States. K-Means outperformed Fuzzy K-Means across all Big Data benchmarks, achieving a 27.2% lower Within-Cluster Sum of Squares (1.57M vs 2.15M) and executing in 3.92 minutes compared to 9.80 minutes on Hadoop YARN.

---

## 2. Big Data Architecture and Workflow

```
[ Raw Cornell USCrop Dataset: 124,320 x 6,322 ]
                     |
                     v
[ Feature Selection: 1,322 Weather/Land/Soil Features Selected ]
[ 8 Metadata Columns (FIPS, Year, 6 Crop Yields) Preserved Separately ]
                     |
                     v
[ Min-Max Scaling [0,1] & Mean Imputation (preprocess.py) ]
                     |
                     v
[ Ingestion into HDFS: /user/praveen/smart_agriculture/input/ ]
                     |
                     v
[ Mahout InputDriver MapReduce Conversion -> SequenceFiles (vectors) ]
                     |
      +--------------+--------------+
      |                             |
      v                             v
[ Mahout K-Means (k=5) ]     [ Mahout Fuzzy K-Means (k=5) ]
(10 MR Iterations on YARN)   (10 MR Iterations on YARN)
      |                             |
      +--------------+--------------+
                     |
                     v
[ Model Evaluation & Comparison (evaluate_models.py) ]
                     |
                     v
[ Crop Yield Analysis Across Clusters (analyze_crop_yields.py) ]
```

---

## 3. Distributed Model Comparison Results

Both clustering algorithms processed the entire 124,320-record dataset on Hadoop YARN MapReduce using Squared Euclidean Distance with $k=5$:

| Metric | Apache Mahout K-Means | Apache Mahout Fuzzy K-Means | Analysis / Interpretation |
| :--- | :---: | :---: | :--- |
| **Cluster Count ($k$)** | **5** | **5** | Equal partition baseline |
| **Fuzziness Parameter ($m$)** | N/A (Hard) | 2.0 (Soft) | Standard fuzzy exponent |
| **MapReduce Iterations** | 10 | 10 | Convergence tolerance $\delta=0.01$ |
| **Hadoop YARN Runtime** | **3.92 minutes** | **9.80 minutes** | **K-Means is 2.5x faster in distributed execution** |
| **Within-Cluster Sum of Squares (WCSS)** | **1,568,053.21** | **2,152,892.04** | **K-Means produces 27.2% tighter clusters** |
| **Mean Inter-Cluster Distance** | **5.3406** | **2.2515** | K-Means centroids are significantly better separated |
| **Min Inter-Cluster Distance** | 2.8332 | 0.2971 | Fuzzy centroids contract toward data mass center |
| **Max Inter-Cluster Distance** | 8.4852 | 3.9586 | K-Means spans broader feature geometry |
| **Cluster Sizes (Points)** | [19.9k, 35.8k, 17.2k, 25.7k, 25.7k] | [17.0k, 40.9k, 30.3k, 22.1k, 14.1k] | Balanced spatial distribution |

### Performance Analysis
- **Compactness:** K-Means strictly minimizes Euclidean point-to-center distances, producing denser and more cohesive clusters.
- **Separation:** K-Means maintains a mean inter-cluster distance of 5.34 compared to 2.25 for Fuzzy K-Means, preventing cluster collapse.
- **Computational Efficiency:** Fuzzy K-Means computes continuous $5 \times 1,322$ membership weights for all points across every iteration, resulting in 2.5x higher MapReduce CPU and I/O overhead.

---

## 4. Agricultural Interpretation & Crop Yield Analysis

By linking cluster assignments to the preserved USDA county crop yield metadata, we discovered clear agro-ecological profiles:

### Cluster Profile Table

| Cluster | Identified Agro-Ecological Zone | Dominant Crops & Yield Statistics | Distinct Agricultural Role |
| :---: | :--- | :--- | :--- |
| **Cluster 1** | **Prime Midwest Corn-Soy Belt** | **Corn:** Mean = 126.12 bu/ac ($N=26,810$)<br>**Soybeans:** Mean = 40.72 bu/ac ($N=22,707$)<br>**Winter Wheat:** Mean = 51.18 bu/ac ($N=18,589$)<br>**Cotton:** 0.00 | Dominates national grain output. High-productivity mollisol soils, abundant growing-season moisture. (Iowa, Illinois, Indiana, Ohio, Minnesota). |
| **Cluster 2** | **Southern Cotton Belt** | **Upland Cotton:** Mean = 698.33 lbs/ac ($N=7,289$)<br>**Corn:** Mean = 91.62 bu/ac ($N=7,934$)<br>**Soybeans:** Mean = 25.58 bu/ac ($N=5,284$) | Concentrates 55% of all southern cotton county observations. Long frost-free growing seasons, high summer humidity. (MS, AL, GA, AR). |
| **Cluster 0** | **Northern Plains Spring Wheat Zone** | **Spring Wheat:** Mean = 42.57 bu/ac ($N=8,139$)<br>**Winter Wheat:** Mean = 45.03 bu/ac ($N=11,354$)<br>**Corn:** Mean = 113.11 bu/ac ($N=10,579$) | Accounts for 64% of all US spring wheat county-years. Colder continental winters, short growing window. (North Dakota, South Dakota, Montana). |
| **Cluster 3** | **Central Transition & Grain Sorghum Zone** | **Grain Sorghum:** Mean = 69.67 bu/ac ($N=7,748$)<br>**Corn:** Mean = 113.32 bu/ac ($N=19,098$)<br>**Soybeans:** Mean = 34.67 bu/ac ($N=18,245$) | Transitional temperate zone. High sorghum yields and diversified grain production. (Kansas, Missouri, Kentucky, Tennessee). |
| **Cluster 4** | **Western Semi-Arid & Marginal Zone** | **Grain Sorghum:** Mean = 53.15 bu/ac ($N=7,485$)<br>**Cotton:** Mean = 584.81 lbs/ac ($N=5,322$)<br>**Corn:** Mean = 101.11 bu/ac ($N=13,557$) | Semi-arid High Plains and western fringe. Lower soil moisture and higher heat stress suppress average crop yields. (West Texas, OK, CO). |

---

## 5. College-Level Project Conclusions & Takeaways

1. **Unsupervised Validation Works:** The clustering models were trained strictly on weather, land, and soil data without crop yields. Despite this blind training, the clusters naturally separated the major US crop belts, validating the predictive power of environmental factors on agricultural productivity.
2. **Hadoop & Mahout Distributed Scalability:** The entire pipeline scaled seamlessly over 124,320 observations $\times$ 1,322 dimensions using actual Hadoop HDFS storage and YARN MapReduce processing without memory bottlenecks.
3. **Hard vs. Soft Clustering:** While Fuzzy K-Means offers theoretical flexibility for boundary counties, hard K-Means is computationally superior and provides cleaner, more actionable agro-climatic boundaries for large-scale agricultural planning.
