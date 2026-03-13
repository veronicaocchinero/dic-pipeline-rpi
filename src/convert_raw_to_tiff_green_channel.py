import numpy as np
from pathlib import Path
import tifffile as tiff
import multiprocessing as mp
import argparse

WIDTH = 2028
HEIGHT = 1520

# stride reale (pixel per riga nel buffer)
STRIDE = 2048


def convert_file(raw_path: Path):

    # carica RAW
    data = np.fromfile(raw_path, dtype=np.uint16)

    # reshape con stride
    img = data.reshape((HEIGHT, STRIDE))

    # taglia padding
    bayer16 = img[:, :WIDTH]

    # converti a 8 bit (RAW8 in container 16)
    bayer8 = (bayer16 >> 8).astype(np.uint8)

    # estrai i due canali verdi dal Bayer BGGR
    green1 = bayer8[0::2, 1::2]
    green2 = bayer8[1::2, 0::2]

    # media dei due verdi
    green = ((green1.astype(np.uint16) + green2.astype(np.uint16)) // 2).astype(np.uint8)

    # salva TIFF
    tiff_path = raw_path.with_suffix(".tiff")
    tiff.imwrite(tiff_path, green)

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