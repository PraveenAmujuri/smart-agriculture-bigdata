# Project Report: Smart Agriculture Big Data Analytics Using Hadoop and Apache Mahout

Course: Big Data Analytics Mini-Project  
Technologies: Apache Hadoop 3.3.6, Apache Mahout 0.13.0, HDFS, YARN MapReduce, Python 3, NumPy  
Dataset: Cornell USCrop Dataset (1981–2020)  

---

# Introduction

In agriculture, crop growth and yield depend on environmental factors like rainfall, temperature, and soil quality. Farmers and researchers track these conditions across different counties over many years to see how regional conditions affect different crops. Because this data covers thousands of counties over four decades with measurements recorded every week, the resulting datasets are large and difficult to work with on a regular computer.

In this mini-project, we used the Cornell USCrop dataset to study agricultural patterns across US counties from 1981 to 2020. We used Apache Hadoop for distributed data storage and processing, and Apache Mahout to run two clustering algorithms: K-Means and Fuzzy K-Means. By clustering counties based on physical weather and soil features, we examined whether these groups show noticeable differences in crop yields without using crop data during the clustering process.

---

# Problem Statement

Working with multi-decade agricultural data presents practical challenges:
- The raw dataset is 5.9 GB uncompressed, which can cause out-of-memory errors if loaded into RAM all at once.
- The dataset contains 6,322 columns per row, many of which are weekly survey questions with large amounts of missing data.
- Processing and clustering this volume of data on a single machine can be slow or fail completely without distributed tools.

We need a simple workflow to filter out sparse columns, normalize the remaining features, store the data in Hadoop HDFS, run clustering algorithms through Apache Mahout, and check if the resulting clusters match real-world agricultural differences.

---

# Objectives

The main objectives of this project are:
- Inspect the dataset and analyze missing values across different feature groups.
- Select continuous weather and soil features for clustering, while keeping crop yields and county identifiers separate.
- Handle missing values and scale the clustering features to the range 0 to 1.
- Upload the processed data to HDFS and convert it to SequenceFiles required by Apache Mahout.
- Run K-Means and Fuzzy K-Means clustering using 5 clusters on Hadoop YARN.
- Compare the execution time, iterations, and cluster assignments of both models.
- Analyze crop-yield averages across the clusters to see if environmental groupings reflect different agricultural characteristics.

---

# Dataset Description

We used the Cornell USCrop dataset, which contains county-year records from 1981 to 2020 for agricultural counties across the United States.

- Dataset source: https://ecommons.cornell.edu/entities/publication/867a510e-9a59-4466-9f56-1a3a432b200e
- Extracted file: `data/extracted/data.npy` (5.9 GB)
- Total rows: 124,320 observations (one row per county per year)
- Total columns: 6,322 features

The columns in the dataset fall into several main groups:
- Identifiers (columns 0–1): County FIPS code and year (0% missing).
- Crop yields (columns 2–7): USDA reported yields for corn, upland cotton, sorghum, soybeans, spring wheat, and winter wheat.
- Weather data (columns 8–371): 52-week PRISM measurements of rainfall, temperature, dew point, and vapor pressure (0% missing).
- Land surface data (columns 372–1203): 52-week NLDAS measurements of soil moisture across multiple depths, soil temperature, and runoff (0.02% missing).
- Crop progress surveys (columns 1204–6195): Weekly survey questions about planting, blooming, and harvesting progress (93.38% missing).
- Soil quality (columns 6196–6321): gSSURGO measurements including sand, silt, clay, and organic matter percentages (0% missing).

During our missing-value analysis, we found that more than 99.9% of all missing values in the dataset came from the crop-progress survey columns. These surveys are only conducted in counties and weeks where specific crops are actively grown, leaving 2,583 columns completely empty. Because of this high sparsity, we excluded all 4,992 crop-progress columns from the clustering process.

---

# Software and Hardware Requirements

Hardware used:
- Device: Lenovo LOQ 15IAX9
- Processor: 12th Gen Intel Core i5-12450HX
- RAM: 24 GB DDR5

Software configuration:
- Operating System: Ubuntu Linux 24.04 LTS (64-bit)
- Hadoop: Apache Hadoop 3.3.6 (configured in single-node pseudo-distributed mode)
- Mahout: Apache Mahout 0.13.0
- Java: OpenJDK 11
- Python: Python 3.14 with NumPy

---

# Methodology

Our project followed six practical steps:
1. Data Analysis: Checked file headers and measured missing values across each column group without loading the full 5.9 GB file into memory.
2. Feature Selection: Picked 1,322 continuous weather, land-surface, and soil columns for clustering. Preserved FIPS, year, and 6 crop yields separately.
3. Preprocessing: Handled missing values using column mean imputation and normalized features to the range 0 to 1.
4. HDFS Storage and Conversion: Uploaded the normalized data into HDFS and converted text vectors into binary SequenceFiles using Mahout's MapReduce converter.
5. Clustering on Hadoop: Executed K-Means and Fuzzy K-Means clustering jobs with $k=5$ using Hadoop MapReduce on YARN.
6. Evaluation and Yield Analysis: Evaluated cluster distributions, compared model agreement using the Adjusted Rand Index, and calculated average crop yields and weather conditions for each cluster.

---

# Implementation

### Data Preprocessing
To avoid running out of memory, we wrote `src/analysis/preprocess.py` to read the dataset in chunks of 5,000 rows using NumPy memory mapping (`mmap_mode="r"`).

There were only 24,960 missing values among the 1,322 selected features, all within the NLDAS land-surface columns. We replaced these missing values with the average of that specific column. This allowed us to keep all 124,320 rows without dropping any records.

Next, we applied Min-Max scaling to bring all values into the range 0 to 1 so that variables with large ranges (such as annual rainfall) would not dominate variables with small ranges (such as soil fractions). The script created two output files:
- `data/processed/clustering_data.csv`: 124,320 rows and 1,322 normalized columns (1.1 GB).
- `data/processed/metadata.csv`: 124,320 rows containing FIPS, year, and 6 crop yields in the exact same row order (3.5 MB).

### Storing Data in HDFS
We verified that Hadoop daemons (NameNode, DataNode, ResourceManager, NodeManager) were running. We then piped the comma-separated data through `tr` to change commas to spaces and streamed the text directly into HDFS:
```bash
hdfs dfs -mkdir -p /user/praveen/smart_agriculture/input
tr ',' ' ' < data/processed/clustering_data.csv | \
  hdfs dfs -put - /user/praveen/smart_agriculture/input/clustering_data.txt
```
This saved disk space by avoiding an extra copy on the local drive.

### Converting to Mahout SequenceFiles
Mahout cannot read plain text files directly; it requires SequenceFiles containing vector objects. We ran Mahout's `InputDriver` MapReduce job:
```bash
MAHOUT_LOCAL="" mahout org.apache.mahout.clustering.conversion.InputDriver \
  -i /user/praveen/smart_agriculture/input/ \
  -o /user/praveen/smart_agriculture/vectors/ \
  -v org.apache.mahout.math.DenseVector
```
Unsetting `MAHOUT_LOCAL=""` is important because if it contains any text, Mahout runs locally in memory instead of submitting jobs to Hadoop. This job created 9 SequenceFile parts under `/user/praveen/smart_agriculture/vectors/`, holding all 124,320 vectors.

### Running K-Means and Fuzzy K-Means
We chose 5 clusters ($k=5$) to represent broad agricultural regions in the US. Both jobs used random seed 42, Squared Euclidean Distance, and a convergence threshold of 0.01:
- K-Means was run using `bash src/mahout/run_kmeans.sh`. It ran for its configured maximum of 10 iterations on YARN and finished in approximately 9.80 minutes. Output was stored in `/user/praveen/smart_agriculture/results/kmeans/`.
- Fuzzy K-Means was run using `bash src/mahout/run_fuzzy_kmeans.sh` with fuzziness factor $m=2.0$. It converged after 6 iterations on YARN and finished in approximately 3.92 minutes. Point assignments were generated using the `-cl` flag to assign each observation to its most likely cluster. Output was stored in `/user/praveen/smart_agriculture/results/fuzzy_kmeans/`.

---

# Results and Discussion

### Model Comparison
Table 1 shows the comparison between the two clustering models:

| Metric | K-Means | Fuzzy K-Means |
| :--- | :---: | :---: |
| Number of Clusters ($k$) | 5 | 5 |
| Iterations | 10 (reached max) | 6 (converged) |
| Execution Time | ~9.80 minutes | ~3.92 minutes |
| Observations Assigned | 124,320 (100%) | 124,320 (100%) |
| Cluster 0 Size | 19,934 (16.0%) | 16,966 (13.7%) |
| Cluster 1 Size | 35,765 (28.8%) | 40,889 (32.9%) |
| Cluster 2 Size | 17,191 (13.8%) | 30,306 (24.4%) |
| Cluster 3 Size | 25,734 (20.7%) | 22,101 (17.8%) |
| Cluster 4 Size | 25,696 (20.7%) | 14,058 (11.3%) |
| Adjusted Rand Index (ARI) | — | 0.4426 |
| Silhouette Score ($N=5,000$) | 0.1363 | 0.0833 |
| Davies–Bouldin Index ($N=5,000$) | 1.9229 | 2.4350 |

In our execution, Fuzzy K-Means stopped after 6 iterations taking about 3.92 minutes, while K-Means completed all 10 iterations taking about 9.80 minutes. Both models assigned all 124,320 observations and produced balanced clusters without empty groups.

The Adjusted Rand Index between the two solutions is 0.4426. ARI measures the agreement between two clusterings while adjusting for chance (where 0 means random and 1 means identical). An ARI of 0.4426 indicates moderate agreement between the hard assignments. This happens because counties near cluster borders get divided differently when soft probability weighting is used. ARI is an agreement measure between the two outputs, not a measure of classification accuracy.

### Clustering Quality Evaluation
To assess cluster compactness and geometric separation without computing full $124,320 \times 124,320$ distance matrices in memory, we calculated the Silhouette Score and the Davies–Bouldin Index on a random sample of 5,000 observations (random seed 42) using the 1,322 normalized environmental features. For Fuzzy K-Means, we used the hard cluster assignments (each point assigned to its highest-membership cluster).

- **Silhouette Score**: Measures how close each point is to points within its assigned cluster relative to points in neighboring clusters, on a scale from -1.0 to +1.0. A score of 0 indicates overlapping cluster boundaries, while values closer to +1.0 indicate distinct separation. K-Means recorded a score of 0.1363, while Fuzzy K-Means recorded 0.0833. Both scores are relatively low, suggesting that the clusters are not strongly separated and that some observations may have similar characteristics across cluster boundaries.
- **Davies–Bouldin Index**: Evaluates the ratio of within-cluster dispersion to between-cluster separation, where lower values signify tighter and more separated clusters. K-Means scored 1.9229, while Fuzzy K-Means scored 2.4350. K-Means obtained a lower Davies–Bouldin Index, indicating relatively more compact and better-separated clusters than the hard-assignment Fuzzy K-Means solution in this evaluation.

**Overall comparison:** K-Means achieved a higher Silhouette Score (0.1363 vs. 0.0833) and a lower Davies–Bouldin Index (1.9229 vs. 2.4350), indicating better clustering quality according to these internal evaluation metrics. However, Fuzzy K-Means completed execution faster (3.92 minutes compared with 9.80 minutes for K-Means). Therefore, K-Means performed better in terms of measured clustering quality, while Fuzzy K-Means had an execution-time advantage.

These metrics provide useful mathematical characterization of cluster geometry, but they reflect structural algorithmic differences in partitioning continuous data rather than proving one model is inherently superior or more accurate.

### Environmental Characteristics of Clusters
We calculated average weather and soil properties for each K-Means cluster (Table 2):

| Cluster | Count | Annual Rain (cm / mm) | Mean Temp (°C) | Soil Summary | Profile Interpretation |
| :---: | :---: | :---: | :---: | :--- | :--- |
| 0 | 19,934 | 73.6 cm (736 mm) | 7.9°C | 47.4% Sand, 4.78% Organic Matter | Cool, semi-arid northern plains |
| 1 | 35,765 | 142.0 cm (1,420 mm) | 8.9°C | 49.7% Silt, 7.57% Organic Matter | Silt-loam soil with high organic content |
| 2 | 17,191 | 147.8 cm (1,478 mm) | 19.0°C | 68.7% Sand, 1.94% Organic Matter | Warm, sandy southern region |
| 3 | 25,734 | 181.5 cm (1,815 mm) | 14.7°C | 57.2% Silt, 3.33% Organic Matter | High-rainfall, high-silt river basin |
| 4 | 25,696 | 152.5 cm (1,525 mm) | 15.3°C | 46.5% Sand, 2.76% Organic Matter | Warm, sandy-loam plains |

Note: In the PRISM dataset, weekly rainfall is recorded in centimeters. Summing over 52 weeks gives annual rainfall totals between 73.6 cm and 181.5 cm (736 mm to 1,815 mm). The regional descriptions above are interpretations based on these physical averages, not official administrative zones.

### Crop-Yield Observations
We matched the cluster assignments to the preserved USDA crop yields. Missing yield values were excluded on a per-crop basis and not treated as zero. Missing yield records indicate unavailable survey data for that county-year, not confirmed crop absence.

The key observations from the K-Means clusters include:
- Cluster 1 had the highest average corn yield (126.12 bu/acre across 26,810 observations) and highest soybean yield (40.72 bu/acre across 22,707 observations). Cotton yield records were essentially absent (only 1 record).
- Cluster 2 had the highest concentration of cotton yield records (7,289 observations, averaging 698.33 lbs/acre). Spring wheat had zero valid yield records in this cluster.
- Cluster 0 had the highest number of spring wheat yield reports (8,139 observations, averaging 42.57 bu/acre), representing over 65% of all spring wheat records in the dataset. Cotton was almost absent (0.17% coverage).
- Cluster 3 had high corn yields (113.32 bu/acre) and frequent soybean reports, matching its high annual rainfall (181.5 cm).
- Cluster 4 showed mixed crop reporting, with winter wheat (40.46 bu/acre), grain sorghum (53.15 bu/acre), and cotton (584.81 lbs/acre).

These results suggest that environmental clustering can identify groups with different agricultural characteristics, even though crop yields were never used during the clustering process.

---

# Limitations

1. Single-node setup: Hadoop and Mahout ran in pseudo-distributed mode on a single machine. While this ran real MapReduce jobs, it did not test network communication across multiple physical computers.
2. Defuzzification: For comparison purposes, Fuzzy K-Means soft memberships were simplified to the single most likely cluster.
3. Fixed number of clusters: We only tested $k=5$. Testing other values of $k$ could be explored in future work.
4. Technological changes over time: The dataset covers 40 years (1981–2020). Over this time, better seeds, fertilizers, and equipment improved crop yields independent of weather conditions.

---

# Conclusion

In this project, we built a working Big Data pipeline for agricultural data using Hadoop and Apache Mahout:
- Memory-mapped chunk processing allowed us to clean and normalize a 5.9 GB dataset on a standard laptop without memory issues.
- Mahout executed distributed K-Means and Fuzzy K-Means clustering jobs through Hadoop YARN.
- Fuzzy K-Means finished in 6 iterations (~3.92 min), while K-Means ran for 10 iterations (~9.80 min), with moderate agreement between their hard assignments (ARI = 0.4426).
- The resulting clusters showed distinct differences in rainfall, temperature, soil composition, and crop yields. This shows that clustering on weather and soil data alone can group county-years into meaningful agricultural profiles.
- Based on the Silhouette Score and Davies–Bouldin Index, K-Means showed better clustering quality, whereas Fuzzy K-Means completed execution faster.
