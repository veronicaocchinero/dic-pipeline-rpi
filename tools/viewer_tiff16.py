"""
viewer_tiff16.py
----------------
Viewer lineare per immagini TIFF16 usate nella DIC.

Funzioni:
- visualizzazione lineare (no auto-contrasto)
- scaling 16 bit → 8 bit lineare
- zoom con + / -
- frame avanti/indietro con frecce
"""

import cv2
import numpy as np
from pathlib import Path


def linear_to_8bit(img16):
    """Scala linearmente 16→8 bit senza auto-contrasto."""
    max_val = img16.max()
    if max_val == 0:
        max_val = 1
    img8 = (img16.astype(np.float32) / max_val * 255.0).astype(np.uint8)
    return img8


def view_tiff_sequence(folder: Path):
    files = sorted(folder.glob("*.tiff"))
    if not files:
        print("Nessun TIFF trovato.")
        return

    idx = 0
    zoom = 1.0

    while True:
        tiff_path = files[idx]
        img16 = cv2.imread(str(tiff_path), cv2.IMREAD_UNCHANGED)

        img8 = linear_to_8bit(img16)

        # Applica zoom
        if zoom != 1.0:
            img8 = cv2.resize(img8, None, fx=zoom, fy=zoom,
                              interpolation=cv2.INTER_NEAREST)

        cv2.imshow("TIFF16 Viewer (lineare)", img8)

        key = cv2.waitKey(0) & 0xFF

        if key == ord('q'):
            break
        elif key == 82:   # freccia su
            idx = max(0, idx - 1)
        elif key == 84:   # freccia giù
            idx = min(len(files) - 1, idx + 1)
        elif key == ord('+'):
            zoom *= 1.2
        elif key == ord('-'):
            zoom /= 1.2

    cv2.destroyAllWindows()


if __name__ == "__main__":
    folder = Path("output/seq_0001")
    view_tiff_sequence(folder)
