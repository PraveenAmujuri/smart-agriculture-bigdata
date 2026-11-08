"""Analyze crop yield distributions across Mahout K-Means clusters."""

import csv
import numpy as np

CROPS = [
    "corn_yield",
    "cotton_upland_yield",
    "sorghum_yield",
    "soybeans_yield",
    "spring_wheat_yield",
    "winter_wheat_yield"
]

def main():
    print("Loading cluster assignments and metadata...")
    clusters = []
    with open("results/cluster_assignments.csv", "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            clusters.append(int(row["kmeans_cluster"]))

    yield_data = {c: [[] for _ in range(5)] for c in CROPS}
    fips_by_cluster = [set() for _ in range(5)]

    with open("data/processed/metadata.csv", "r") as f:
        reader = csv.DictReader(f)
        for idx, row in enumerate(reader):
            c_idx = clusters[idx]
            fips_by_cluster[c_idx].add(row["fips"])
            for crop in CROPS:
                val_str = row[crop].strip()
                if val_str:
                    yield_data[crop][c_idx].append(float(val_str))

    print("Computing cluster crop yield statistics...")
    summary_rows = []
    for c_idx in range(5):
        num_counties = len(fips_by_cluster[c_idx])
        num_obs = sum(1 for c in clusters if c == c_idx)
        print(f"\n--- Cluster {c_idx} (Total Obs: {num_obs}, Unique Counties: {num_counties}) ---")
        for crop in CROPS:
            vals = np.array(yield_data[crop][c_idx], dtype=np.float64)
            if len(vals) > 0:
                mean_y = float(np.mean(vals))
                std_y = float(np.std(vals))
                med_y = float(np.median(vals))
                count_y = len(vals)
            else:
                mean_y = std_y = med_y = 0.0
                count_y = 0

            summary_rows.append({
                "cluster": c_idx,
                "crop": crop,
                "count": count_y,
                "mean_yield": round(mean_y, 2),
                "std_yield": round(std_y, 2),
                "median_yield": round(med_y, 2)
            })
            if count_y > 0:
                print(f"  {crop:20s}: Mean={mean_y:7.2f}, Median={med_y:7.2f}, N={count_y:5d}")

    out_csv = "results/crop_yield_by_cluster.csv"
    with open(out_csv, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["cluster", "crop", "count", "mean_yield", "std_yield", "median_yield"])
        writer.writeheader()
        writer.writerows(summary_rows)
    print(f"\nCrop yield analysis written to {out_csv}")

if __name__ == "__main__":
    main()
