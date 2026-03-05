"""
raw_to_tiff.py
--------------
Conversione IMX477 RAW12 (DNG) → TIFF16 monocromatico per DIC.

Correzioni applicate:
- Lettura RAW corretta da rawpy
- Rimozione black level
- Estrazione canale verde (G1) del pattern Bayer
- Normalizzazione 12 → 16 bit
- Salvataggio TIFF16 senza perdita
"""

from pathlib import Path
import rawpy
import numpy as np
import imageio.v3 as iio


# ================================================================
# Conversione singolo file DNG → TIFF16 mono
# ================================================================

def convert_dng_to_tiff(dng_path: Path, tiff_path: Path):

    with rawpy.imread(str(dng_path)) as raw:

        # 1. RAW Bayer grezzo (16-bit)
        bayer = raw.raw_image.copy()

        # 2. Applica correzione black level
        black = raw.black_level_per_channel[0]
        bayer = bayer.astype(np.int32) - black
        bayer[bayer < 0] = 0

        # 3. Estrai canale verde (G1) dal pattern Bayer
        # IMX477 usa RGGB → G1 = pixel riga pari, colonna dispari
        h, w = bayer.shape
        green = bayer[0:h:2, 1:w:2]

        # 4. Escludi saturazione oltre i 12 bit reali (4095)
        green = np.clip(green, 0, 4095)

        # 5. Converti 12-bit → 16-bit
        tiff16 = (green.astype(np.uint16) << 4)

        # 6. Salva TIFF16 (mono)
        iio.imwrite(str(tiff_path), tiff16)
        print(f"[convert] {dng_path.name} → {tiff_path.name}")


# ================================================================
# Conversione di un'intera cartella seq_XXXX
# ================================================================

def convert_sequence_folder(seq_folder: Path):

    dng_files = sorted(seq_folder.glob("*.dng"))
    if not dng_files:
        print("[convert] Nessun file DNG trovato.")
        return

    print(f"[convert] Converting {len(dng_files)} DNG → TIFF16...")

    for dng_file in dng_files:
        tiff_file = seq_folder / f"{dng_file.stem}.tiff"
        convert_dng_to_tiff(dng_file, tiff_file)

    print("[convert] Conversione completata.")


if __name__ == "__main__":
    folder = Path("output/seq_0001")
    convert_sequence_folder(folder)

