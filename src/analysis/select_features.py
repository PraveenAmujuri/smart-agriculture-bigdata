import csv
import os
import re

# 1. Parse column_names.csv and build feature map
col_names = {}
with open("data/column_names.csv", "r") as f:
    reader = csv.reader(f)
    next(reader)
    for row in reader:
        if len(row) >= 4:
            m = re.findall(r"\d+", row[1])
            if m:
                start, end = int(m[0]), int(m[1])
                var_name = row[2]
                if start == end:
                    col_names[start] = var_name
                else:
                    for i in range(start, end + 1):
                        col_names[i] = f"{var_name}_{i - start + 1}"

# 2. Define column ranges
IDENTIFIERS = list(range(0, 2))       # FIPS, Year (2 cols)
TARGET_YIELDS = list(range(2, 8))     # Crop Yields (6 cols)
WEATHER_COLS = list(range(8, 372))    # PRISM Weather (364 cols)
LAND_COLS = list(range(372, 1204))    # NLDAS Land Surface (832 cols)
EXCLUDED_COLS = list(range(1204, 6196)) # USDA Crop Progress (4992 cols)
SOIL_COLS = list(range(6196, 6322))   # gSSURGO Soil (126 cols)

CLUSTERING_COLS = WEATHER_COLS + LAND_COLS + SOIL_COLS  # 1322 cols

# 3. Print breakdown
print("FEATURE SELECTION SUMMARY")
print("-" * 50)
print(f"Identifiers (Preserved):      {len(IDENTIFIERS):>5} cols (indices 0-1)")
print(f"Crop Yields (Preserved):      {len(TARGET_YIELDS):>5} cols (indices 2-7)")
print(f"PRISM Weather (Clustering):   {len(WEATHER_COLS):>5} cols (indices 8-371)")
print(f"NLDAS Land (Clustering):      {len(LAND_COLS):>5} cols (indices 372-1203)")
print(f"gSSURGO Soil (Clustering):    {len(SOIL_COLS):>5} cols (indices 6196-6321)")
print(f"USDA Progress (Excluded):     {len(EXCLUDED_COLS):>5} cols (indices 1204-6195)")
print("-" * 50)
print(f"Total Selected for Clustering:{len(CLUSTERING_COLS):>5} cols")
print(f"Total Preserved Context:      {len(IDENTIFIERS) + len(TARGET_YIELDS):>5} cols")
print(f"Total Columns Verified:       {len(IDENTIFIERS) + len(TARGET_YIELDS) + len(CLUSTERING_COLS) + len(EXCLUDED_COLS):>5} cols (of 6322)")

# 4. Save results to CSV
os.makedirs("results", exist_ok=True)

with open("results/feature_selection_summary.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["category", "role", "start_col", "end_col", "num_columns"])
    writer.writerow(["Identifiers (FIPS, Year)", "Preserve / Context", 0, 1, len(IDENTIFIERS)])
    writer.writerow(["USDA Crop Yields", "Preserve / Evaluation", 2, 7, len(TARGET_YIELDS)])
    writer.writerow(["PRISM Weather", "Clustering Input", 8, 371, len(WEATHER_COLS)])
    writer.writerow(["NLDAS Land Surface", "Clustering Input", 372, 1203, len(LAND_COLS)])
    writer.writerow(["gSSURGO Soil Quality", "Clustering Input", 6196, 6321, len(SOIL_COLS)])
    writer.writerow(["USDA Crop Progress", "Excluded (High Sparsity)", 1204, 6195, len(EXCLUDED_COLS)])

with open("results/selected_features.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["column_index", "column_name", "category"])
    for idx in CLUSTERING_COLS:
        cat = "Weather" if idx < 372 else ("Land_Surface" if idx < 1204 else "Soil")
        writer.writerow([idx, col_names.get(idx, f"col_{idx}"), cat])

print(f"\nSaved feature lists to:")
print("  - results/feature_selection_summary.csv")
print("  - results/selected_features.csv")
