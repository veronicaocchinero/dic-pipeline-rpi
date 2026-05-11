import numpy as np
from pathlib import Path
import tifffile as tiff
import cv2
import multiprocessing as mp
import argparse

# ============================================================
# CONFIGURAZIONE
# ============================================================

# 🔵 CASO 1 — ORIZZONTALE (funzionava prima)
CAMERA_RESOLUTION = (2028, 1520)
RAW_H = 1520
RAW_W = 2048
HEIGHT = 1520
WIDTH = 2028

# 🔴 CASO 2 — VERTICALE (nuovo setup)
# CAMERA_RESOLUTION = (1520, 2028)
#RAW_H = 2160      # righe reali buffer (con padding)
#RAW_W = 4064      # stride reale buffer

#HEIGHT = 2160     # altezza immagine utile
#WIDTH = 4056    # larghezza immagine utile

# ============================================================
# CONVERSIONE
# ============================================================

def convert_file(raw_path: Path):

    data = np.fromfile(raw_path, dtype=np.uint16)

    # reshape con dimensioni REALI del buffer
    img = data.reshape((RAW_H, RAW_W))

    # crop verticale (rimuove padding righe)
    img = img[:HEIGHT, :]

    # crop orizzontale (rimuove padding colonne)
    bayer16 = img[:, :WIDTH]

    # conversione 8 bit (fondamentale)
    bayer8 = (bayer16 >> 8).astype(np.uint8)

    # preview opzionale
    # rgb = cv2.cvtColor(bayer8, cv2.COLOR_BAYER_BG2RGB)
    # gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)

    tiff_path = raw_path.with_suffix(".tiff")
    tiff.imwrite(tiff_path, bayer8)

    return raw_path.name

# ============================================================
# MULTIPROCESS
# ============================================================

def convert_folder(folder: Path, workers: int):

    raw_files = sorted(folder.glob("*.raw"))

    print(f"\n{len(raw_files)} RAW trovati")

    with mp.Pool(workers) as pool:

        for name in pool.imap_unordered(convert_file, raw_files):

            print("converted:", name)

# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument("folder", type=str)
    parser.add_argument("--workers", type=int, default=mp.cpu_count())

    args = parser.parse_args()

    convert_folder(Path(args.folder), args.workers)