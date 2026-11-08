import csv
import os
import numpy as np

# 1. Load selected feature indices
selected_indices = []
with open("results/selected_features.csv", "r") as f:
    reader = csv.reader(f)
    next(reader)
    for row in reader:
        selected_indices.append(int(row[0]))

num_features = len(selected_indices)

# 2. Load dataset with memory mapping
data = np.load("data/extracted/data.npy", mmap_mode="r")
total_rows = data.shape[0]
chunk_size = 5000

# Pass 1: Compute min, max, and mean for selected features
feat_min = np.full(num_features, np.inf)
feat_max = np.full(num_features, -np.inf)
feat_sum = np.zeros(num_features, dtype=np.float64)
feat_count = np.zeros(num_features, dtype=np.int64)
missing_before = 0

for start in range(0, total_rows, chunk_size):
    end = min(start + chunk_size, total_rows)
    chunk = data[start:end, selected_indices]
    nan_mask = np.isnan(chunk)
    missing_before += int(nan_mask.sum())

    valid_mask = ~nan_mask
    feat_count += valid_mask.sum(axis=0)
    feat_min = np.minimum(feat_min, np.nanmin(chunk, axis=0))
    feat_max = np.maximum(feat_max, np.nanmax(chunk, axis=0))

    chunk_zeroed = np.where(nan_mask, 0.0, chunk)
    feat_sum += chunk_zeroed.sum(axis=0)

feat_mean = feat_sum / np.maximum(feat_count, 1)
feat_range = np.where(feat_max > feat_min, feat_max - feat_min, 1.0)

# Pass 2: Impute missing values with column mean, normalize to [0, 1], and save
os.makedirs("data/processed", exist_ok=True)
clustering_file = "data/processed/clustering_data.csv"
metadata_file = "data/processed/metadata.csv"

# Clear files if they exist
open(clustering_file, "wb").close()

with open(metadata_file, "w", newline="") as meta_f:
    meta_writer = csv.writer(meta_f)
    meta_writer.writerow([
        "fips", "year", "corn_yield", "cotton_upland_yield",
        "sorghum_yield", "soybeans_yield", "spring_wheat_yield", "winter_wheat_yield"
    ])

    missing_after = 0
    global_min = np.inf
    global_max = -np.inf

    for start in range(0, total_rows, chunk_size):
        end = min(start + chunk_size, total_rows)

        # Process metadata (columns 0-7)
        meta_chunk = data[start:end, :8]
        for row in meta_chunk:
            fips = int(row[0])
            year = int(row[1])
            yields = [f"{y:.2f}" if not np.isnan(y) else "" for y in row[2:8]]
            meta_writer.writerow([fips, year] + yields)

        # Process clustering features (1,322 columns)
        chunk = data[start:end, selected_indices].copy()

        # Handle missing values using column mean
        nan_mask = np.isnan(chunk)
        chunk = np.where(nan_mask, feat_mean, chunk)

        # Min-Max Normalization to [0, 1]
        chunk_norm = (chunk - feat_min) / feat_range
        chunk_norm = np.clip(chunk_norm, 0.0, 1.0)

        missing_after += int(np.isnan(chunk_norm).sum())
        global_min = min(global_min, float(chunk_norm.min()))
        global_max = max(global_max, float(chunk_norm.max()))

        # Append normalized chunk to clustering_data.csv
        with open(clustering_file, "ab") as clust_f:
            np.savetxt(clust_f, chunk_norm, fmt="%.4f", delimiter=",")

# Summary output
print("=" * 50)
print("PREPROCESSING SUMMARY")
print("=" * 50)
print(f"Rows processed:                 {total_rows:,}")
print(f"Clustering features:            {num_features:,}")
print(f"Missing values before handling: {missing_before:,}")
print(f"Missing values after handling:  {missing_after:,}")
print(f"Imputation method:              Column Mean")
print(f"Normalization method:           Min-Max Scaling [0, 1]")
print(f"Min value after normalization:  {global_min:.4f}")
print(f"Max value after normalization:  {global_max:.4f}")
print("=" * 50)
print(f"Outputs generated:")
print(f"  - {clustering_file}")
print(f"  - {metadata_file}")
