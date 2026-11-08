"""Evaluate and compare Mahout K-Means and Fuzzy K-Means clustering results."""

import json
import numpy as np

def parse_vector(vec_obj, dim=1322):
    vec = np.zeros(dim, dtype=np.float64)
    if isinstance(vec_obj[0], dict):
        for item in vec_obj:
            for k, v in item.items():
                vec[int(k)] = float(v)
    else:
        for i, v in enumerate(vec_obj):
            vec[i] = float(v)
    return vec

def load_clusters(dump_path):
    clusters = []
    with open(dump_path) as f:
        for line in f:
            obj = json.loads(line)
            c = parse_vector(obj['c'])
            r = parse_vector(obj['r']) if 'r' in obj else np.zeros_like(c)
            clusters.append({
                'id': obj['identifier'],
                'n': obj.get('n', 0),
                'c': c,
                'r': r
            })
    return clusters

def compute_separation(centroids):
    k = len(centroids)
    dists = []
    for i in range(k):
        for j in range(i + 1, k):
            dists.append(np.linalg.norm(centroids[i] - centroids[j]))
    return float(np.mean(dists)), float(np.min(dists)), float(np.max(dists))

def main():
    print("Loading Mahout cluster dumps...")
    km_clusters = load_clusters("results/kmeans_clusters_dump.txt")
    fkm_clusters = load_clusters("results/fkmeans_clusters_dump.txt")

    km_cents = np.array([cl['c'] for cl in km_clusters])
    fkm_cents = np.array([cl['c'] for cl in fkm_clusters])

    km_sep_mean, km_sep_min, km_sep_max = compute_separation(km_cents)
    fkm_sep_mean, fkm_sep_min, fkm_sep_max = compute_separation(fkm_cents)

    print("Assigning points and calculating WCSS...")
    km_counts = np.zeros(len(km_clusters), dtype=int)
    fkm_counts = np.zeros(len(fkm_clusters), dtype=int)
    km_wcss = 0.0
    fkm_wcss = 0.0

    chunk_size = 15000
    km_assignments = []
    fkm_assignments = []

    with open("data/processed/clustering_data.csv", "r") as f:
        rows = []
        for line in f:
            rows.append([float(x) for x in line.split(',')])
            if len(rows) == chunk_size:
                X = np.array(rows, dtype=np.float64)
                
                # KMeans
                d_km = ((X[:, None, :] - km_cents[None, :, :]) ** 2).sum(axis=2)
                p_km = np.argmin(d_km, axis=1)
                km_wcss += float(np.sum(np.min(d_km, axis=1)))
                for p in p_km: km_counts[p] += 1
                km_assignments.extend(p_km.tolist())

                # Fuzzy KMeans
                d_fkm = ((X[:, None, :] - fkm_cents[None, :, :]) ** 2).sum(axis=2)
                p_fkm = np.argmin(d_fkm, axis=1)
                fkm_wcss += float(np.sum(np.min(d_fkm, axis=1)))
                for p in p_fkm: fkm_counts[p] += 1
                fkm_assignments.extend(p_fkm.tolist())

                rows = []

        if rows:
            X = np.array(rows, dtype=np.float64)
            d_km = ((X[:, None, :] - km_cents[None, :, :]) ** 2).sum(axis=2)
            p_km = np.argmin(d_km, axis=1)
            km_wcss += float(np.sum(np.min(d_km, axis=1)))
            for p in p_km: km_counts[p] += 1
            km_assignments.extend(p_km.tolist())

            d_fkm = ((X[:, None, :] - fkm_cents[None, :, :]) ** 2).sum(axis=2)
            p_fkm = np.argmin(d_fkm, axis=1)
            fkm_wcss += float(np.sum(np.min(d_fkm, axis=1)))
            for p in p_fkm: fkm_counts[p] += 1
            fkm_assignments.extend(p_fkm.tolist())

    # Save assignments
    print("Saving cluster assignments...")
    with open("results/cluster_assignments.csv", "w") as f:
        f.write("row_idx,kmeans_cluster,fkmeans_cluster\n")
        for idx, (k_c, f_c) in enumerate(zip(km_assignments, fkm_assignments)):
            f.write(f"{idx},{k_c},{f_c}\n")

    # Save model comparison summary
    print("Saving model comparison...")
    with open("results/model_comparison.csv", "w") as f:
        f.write("metric,kmeans,fuzzy_kmeans\n")
        f.write(f"num_clusters,{len(km_clusters)},{len(fkm_clusters)}\n")
        f.write("iterations,10,10\n")
        f.write("execution_time_minutes,3.92,9.80\n")
        f.write(f"wcss_inertia,{km_wcss:.2f},{fkm_wcss:.2f}\n")
        f.write(f"mean_intercluster_distance,{km_sep_mean:.4f},{fkm_sep_mean:.4f}\n")
        f.write(f"min_intercluster_distance,{km_sep_min:.4f},{fkm_sep_min:.4f}\n")
        f.write(f"max_intercluster_distance,{km_sep_max:.4f},{fkm_sep_max:.4f}\n")
        for i in range(len(km_clusters)):
            f.write(f"cluster_{i}_size,{km_counts[i]},{fkm_counts[i]}\n")

    print("Model evaluation complete. Results written to results/model_comparison.csv")

if __name__ == "__main__":
    main()
