"""
undistort_sequence_parallel.py
------------------------------
Correzione distorsione per interi dataset TIFF16 in parallelo.
"""

from pathlib import Path
import multiprocessing as mp
from undistort_tiff16 import undistort_tiff16

def worker(file_pair):
    inp, out = file_pair
    undistort_tiff16(inp, out)

def undistort_folder_parallel(folder: Path, suffix="_undist"):

    tiff_files = sorted(folder.glob("*.tiff"))
    if not tiff_files:
        print("[undist] Nessun TIFF16 trovato.")
        return

    out_folder = folder / "undistorted"
    out_folder.mkdir(exist_ok=True)

    file_pairs = []
    for f in tiff_files:
        out_file = out_folder / f"{f.stem}{suffix}.tiff"
        file_pairs.append((f, out_file))

    print(f"[undist] Correggo {len(file_pairs)} file in parallelo...")

    with mp.Pool(mp.cpu_count() - 1) as pool:
        for _ in pool.imap_unordered(worker, file_pairs):
            pass

    print("[undist] Completato.")


if __name__ == "__main__":
    folder = Path("output/seq_0001")
    undistort_folder_parallel(folder)
