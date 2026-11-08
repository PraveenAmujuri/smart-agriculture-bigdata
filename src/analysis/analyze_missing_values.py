import csv
import os
import re
import numpy as np

# 1. Load column index to variable name mapping
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

# 2. Load dataset using memory mapping
data = np.load("data/extracted/data.npy", mmap_mode="r")
total_rows, total_cols = data.shape
chunk_size = 1000

col_missing = np.zeros(total_cols, dtype=np.int64)
rows_with_missing = 0
total_missing = 0

# 3. Process in chunks of 1,000 rows
for start in range(0, total_rows, chunk_size):
    end = min(start + chunk_size, total_rows)
    chunk = data[start:end]
    nan_mask = np.isnan(chunk)

    total_missing += int(nan_mask.sum())
    col_missing += nan_mask.sum(axis=0)
    rows_with_missing += int(np.any(nan_mask, axis=1).sum())

total_elements = total_rows * total_cols
overall_missing_pct = (total_missing / total_elements) * 100
rows_missing_pct = (rows_with_missing / total_rows) * 100

print(f"Total Rows: {total_rows}")
print(f"Total Columns: {total_cols}")
print(f"Total Missing: {total_missing} ({overall_missing_pct:.2f}%)")
print(f"Rows with Missing: {rows_with_missing} ({rows_missing_pct:.2f}%)")

# 4. Save summary report
os.makedirs("results", exist_ok=True)
with open("results/missing_values_summary.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["metric", "value"])
    writer.writerow(["total_rows", total_rows])
    writer.writerow(["total_columns", total_cols])
    writer.writerow(["total_elements", total_elements])
    writer.writerow(["total_missing_values", total_missing])
    writer.writerow(["overall_missing_percentage", f"{overall_missing_pct:.2f}%"])
    writer.writerow(["rows_with_at_least_one_missing", rows_with_missing])
    writer.writerow(["rows_with_missing_percentage", f"{rows_missing_pct:.2f}%"])

# 5. Find and save top 20 missing columns
top_20_idx = np.argsort(-col_missing)[:20]
with open("results/top_20_missing_columns.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["rank", "column_index", "column_name", "missing_count", "missing_percentage"])
    for rank, idx in enumerate(top_20_idx, 1):
        name = col_names.get(idx, f"col_{idx}")
        count = int(col_missing[idx])
        pct = round((count / total_rows) * 100, 2)
        writer.writerow([rank, idx, name, count, pct])
        print(f"{rank}. {name} (col {idx}): {count} ({pct}%)")
