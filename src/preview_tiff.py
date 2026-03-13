import numpy as np
import cv2
import tifffile as tiff
from pathlib import Path
import argparse

WIDTH = 2028
HEIGHT = 1520


def convert_preview(raw_path: Path):

    raw = np.fromfile(raw_path, dtype=np.uint8)

    expected = WIDTH * HEIGHT

    if raw.size < expected:
        print("File troppo piccolo:", raw_path)
        return

    # reshape
    bayer = raw[:expected].reshape((HEIGHT, WIDTH))

    # debayer (IMX477 = RGGB)
    rgb = cv2.cvtColor(bayer, cv2.COLOR_BAYER_RG2RGB)

    # salva TIFF RGB
    tiff_path = raw_path.with_suffix(".preview.tiff")

    tiff.imwrite(tiff_path, rgb)

    print("saved:", tiff_path)


def main(folder):

    raw_files = sorted(Path(folder).glob("*.raw"))

    print("RAW trovati:", len(raw_files))

    for raw in raw_files:
        convert_preview(raw)


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("folder")

    args = parser.parse_args()

    main(args.folder)