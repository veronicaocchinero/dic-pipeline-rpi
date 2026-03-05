"""
undistort_tiff16.py
-------------------
Applica la calibrazione (intrinseche + distorsione) ad un TIFF16.

La correzione è lineare e non altera la profondità di bit.
"""

import json
import cv2
import numpy as np
from pathlib import Path

CALIB_FILE = Path("camera_calibration.json")


def load_calibration():
    with open(CALIB_FILE, "r") as f:
        data = json.load(f)
    K = np.array(data["intrinsic_matrix"])
    dist = np.array(data["distortion_coeffs"])
    return K, dist


def undistort_tiff16(input_path: Path, output_path: Path):

    K, dist = load_calibration()

    img16 = cv2.imread(str(input_path), cv2.IMREAD_UNCHANGED)

    h, w = img16.shape
    new_K, _ = cv2.getOptimalNewCameraMatrix(K, dist, (w, h), 1)

    undist = cv2.undistort(img16, K, dist, None, new_K)

    cv2.imwrite(str(output_path), undist)
    print(f"[undist] {input_path.name} → {output_path.name}")
