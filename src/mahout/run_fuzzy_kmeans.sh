#!/bin/bash
set -e

INPUT_DIR="/user/praveen/smart_agriculture/vectors"
CLUSTERS_DIR="/user/praveen/smart_agriculture/clusters/initial_fuzzy"
OUTPUT_DIR="/user/praveen/smart_agriculture/results/fuzzy_kmeans"

export MAHOUT_LOCAL=""

echo "=== Running Mahout Fuzzy K-Means on Hadoop ==="
echo "Input: $INPUT_DIR"
echo "Output: $OUTPUT_DIR"

mahout fkmeans \
  -i "$INPUT_DIR" \
  -c "$CLUSTERS_DIR" \
  -o "$OUTPUT_DIR" \
  -k 5 \
  -m 2.0 \
  -x 10 \
  -cd 0.01 \
  -rs 42 \
  -dm org.apache.mahout.common.distance.SquaredEuclideanDistanceMeasure \
  -xm mapreduce \
  -ow \
  -cl

echo "=== Fuzzy K-Means Completed Successfully ==="
