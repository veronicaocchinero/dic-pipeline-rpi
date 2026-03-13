import numpy as np
from pathlib import Path
import tifffile as tiff
import cv2
import multiprocessing as mp
import argparse

WIDTH = 2028
HEIGHT = 1520

# stride reale (pixel per riga nel buffer)
STRIDE = 2048


def convert_file(raw_path: Path):

    data = np.fromfile(raw_path, dtype=np.uint16)

    img = data.reshape((HEIGHT, STRIDE))

    # taglia padding
    bayer16 = img[:, :WIDTH]

    # shift per ottenere 8 bit
    bayer8 = (bayer16 >> 8).astype(np.uint8)

    # debayer per preview
    #rgb = cv2.cvtColor(bayer8, cv2.COLOR_BAYER_BG2RGB)
    #gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)


    tiff_path = raw_path.with_suffix(".tiff")
 
    tiff.imwrite(tiff_path, bayer8)
    #tiff.imwrite(tiff_path, gray)

    return raw_path.name


def convert_folder(folder: Path, workers: int):

    raw_files = sorted(folder.glob("*.raw"))

    print(f"\n{len(raw_files)} RAW trovati")

    with mp.Pool(workers) as pool:

        for name in pool.imap_unordered(convert_file, raw_files):

            print("converted:", name)


if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument("folder", type=str)

    parser.add_argument("--workers", type=int, default=mp.cpu_count())

    args = parser.parse_args()

    convert_folder(Path(args.folder), args.workers)