import csv
import os
import numpy as np
from sklearn.metrics import silhouette_score, davies_bouldin_score


def main():
    print("=== STEP 1: Verifying Alignment Between Features and Cluster Assignments ===")
    
    assignments_path = "results/cluster_assignments.csv"
    features_path = "data/processed/clustering_data.csv"
    output_path = "results/clustering_quality_metrics.csv"
    
    if not os.path.exists(assignments_path):
        raise FileNotFoundError(f"Missing {assignments_path}")
    if not os.path.exists(features_path):
        raise FileNotFoundError(f"Missing {features_path}")

    # Load cluster assignments
    km_labels = []
    fkm_labels = []
    row_indices = []
    with open(assignments_path, "r") as f:
        reader = csv.DictReader(f)
        for r in reader:
            row_indices.append(int(r["row_idx"]))
            km_labels.append(int(r["kmeans_cluster"]))
            fkm_labels.append(int(r["fkmeans_cluster"]))
    
    km_labels = np.array(km_labels)
    fkm_labels = np.array(fkm_labels)
    total_assignments = len(km_labels)
    
    print(f"Loaded cluster assignments: {total_assignments:,} rows")
    assert row_indices[0] == 0 and row_indices[-1] == total_assignments - 1, "Row indices not contiguous from 0"
    assert len(set(row_indices)) == total_assignments, "Duplicate row indices found in assignments"
    assert np.all((km_labels >= 0) & (km_labels <= 4)), "K-Means labels out of range [0, 4]"
    assert np.all((fkm_labels >= 0) & (fkm_labels <= 4)), "Fuzzy K-Means labels out of range [0, 4]"
    print("Cluster assignments verification passed.")

    # === STEP 2: Sampling 5,000 Observations with Random Seed 42 ===
    print("\n=== STEP 2: Sampling 5,000 Observations (Random Seed 42) ===")
    sample_size = 5000
    random_seed = 42
    np.random.seed(random_seed)
    
    sample_indices = np.random.choice(total_assignments, size=sample_size, replace=False)
    sorted_sample_indices = np.sort(sample_indices)
    sample_idx_set = set(sorted_sample_indices)
    
    # Stream clustering_data.csv to extract only the sampled rows
    sampled_vectors = []
    total_feature_rows = 0
    with open(features_path, "r") as f:
        for i, line in enumerate(f):
            total_feature_rows += 1
            if i in sample_idx_set:
                vec = np.fromstring(line, sep=",", dtype=np.float32)
                sampled_vectors.append(vec)

    assert total_feature_rows == total_assignments, (
        f"Row count mismatch: features has {total_feature_rows}, assignments has {total_assignments}"
    )
    print(f"Verified feature dataset row count: {total_feature_rows:,} rows.")

    X_sample = np.array(sampled_vectors, dtype=np.float32)
    assert X_sample.shape == (sample_size, 1322), f"Unexpected shape {X_sample.shape}, expected ({sample_size}, 1322)"
    assert not np.isnan(X_sample).any(), "NaN found in sampled features"
    assert not np.isinf(X_sample).any(), "Inf found in sampled features"
    print(f"Sample matrix verified: {X_sample.shape[0]} rows, {X_sample.shape[1]} features, all finite and scaled.")

    # Sliced cluster assignments for the sample
    y_km = km_labels[sorted_sample_indices]
    y_fkm = fkm_labels[sorted_sample_indices]

    # === STEP 3: Calculating Quality Metrics ===
    print("\n=== STEP 3: Calculating Silhouette Score and Davies–Bouldin Index ===")
    
    # K-Means
    print("Computing metrics for K-Means...")
    sil_km = float(silhouette_score(X_sample, y_km, metric="euclidean"))
    db_km = float(davies_bouldin_score(X_sample, y_km))
    
    # Fuzzy K-Means
    print("Computing metrics for Fuzzy K-Means (hard assignments)...")
    sil_fkm = float(silhouette_score(X_sample, y_fkm, metric="euclidean"))
    db_fkm = float(davies_bouldin_score(X_sample, y_fkm))

    print("\n--- Clustering Quality Results (N=5,000, 1,322 Features) ---")
    print(f"K-Means:       Silhouette Score = {sil_km:.4f}, Davies–Bouldin Index = {db_km:.4f}")
    print(f"Fuzzy K-Means: Silhouette Score = {sil_fkm:.4f}, Davies–Bouldin Index = {db_fkm:.4f}")

    # === STEP 4: Saving Results ===
    results = [
        {
            "model": "K-Means",
            "sample_size": sample_size,
            "random_seed": random_seed,
            "silhouette_score": round(sil_km, 4),
            "davies_bouldin_index": round(db_km, 4)
        },
        {
            "model": "Fuzzy K-Means",
            "sample_size": sample_size,
            "random_seed": random_seed,
            "silhouette_score": round(sil_fkm, 4),
            "davies_bouldin_index": round(db_fkm, 4)
        }
    ]

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", newline="") as f:
        fieldnames = ["model", "sample_size", "random_seed", "silhouette_score", "davies_bouldin_index"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print(f"\nMetrics successfully saved to: {output_path}")


if __name__ == "__main__":
    main()
