import os
import sys
import zipfile
import numpy as np


def inspect_dataset(file_path):

    if not os.path.exists(file_path):
        print("Dataset not found!")
        return

    print("\nDataset:", os.path.basename(file_path))
    print("Size: {:.2f} MB".format(
        os.path.getsize(file_path) / (1024 * 1024)
    ))

    with zipfile.ZipFile(file_path, "r") as archive:

        for item in archive.infolist():

            if not item.filename.endswith(".npy"):
                continue

            with archive.open(item.filename) as file:

                version = np.lib.format.read_magic(file)
                shape, order, dtype = np.lib.format._read_array_header(
                    file, version
                )

                print("\nArray:", item.filename)
                print("Shape:", shape)
                print("Data type:", dtype)
                print("Size: {:.2f} MB".format(
                    item.file_size / (1024 * 1024)
                ))


if __name__ == "__main__":

    if len(sys.argv) != 2:
        print("Usage: python3 inspect_dataset.py <dataset_path>")
        sys.exit(1)

    inspect_dataset(sys.argv[1])
