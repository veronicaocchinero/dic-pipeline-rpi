"""
camera_module.py
----------------
Acquisizione RAW8 pura.

Pipeline:
sensore → RAW8 → file .raw

Nessuna ISP
Nessun main stream
Nessuna conversione
"""

from picamera2 import Picamera2
import numpy as np
from pathlib import Path
import time

from src.config import (
    CAMERA_RESOLUTION,
    EXPOSURE_TIME_US,
    ANALOG_GAIN
)

# ============================================================
# 1️⃣ Inizializzazione camera
# ============================================================

def create_camera():

    cam = Picamera2()

    # 🔴 SOLO STREAM RAW (come nello script che funzionava)
    config = cam.create_still_configuration(

        raw={
            "size": CAMERA_RESOLUTION,
            "format": "SBGGR8"   # RAW8 sensore
        },

        buffer_count=8
    )

    cam.configure(config)
    cam.start()

    cam.set_controls({

        "AeEnable": False,
        "AwbEnable": False,

        "ExposureTime": EXPOSURE_TIME_US,
        "AnalogueGain": ANALOG_GAIN

    })

    time.sleep(1)

    metadata = cam.capture_metadata()

    print("\n[camera] RAW8 PURE MODE")
    print("[camera] Config Exposure:", EXPOSURE_TIME_US)
    print("[camera] Config Gain:", ANALOG_GAIN)
    print("[camera] REAL Exposure:", metadata.get("ExposureTime"))
    print("[camera] REAL Gain:", metadata.get("AnalogueGain"))
    print()

    return cam


# ============================================================
# 2️⃣ Acquisizione RAW
# ============================================================

def capture_raw_fast(cam, filepath: Path):

    filepath.parent.mkdir(parents=True, exist_ok=True)

    request = cam.capture_request()

    metadata = request.get_metadata()

    real_exp = metadata.get("ExposureTime")
    real_gain = metadata.get("AnalogueGain")

    raw = request.make_array("raw")

    request.release()

    # RAW8 → uint8
    raw.astype(np.uint8).tofile(filepath)

    print(
        f"[frame] exp:{real_exp} gain:{real_gain:.2f} "
        f"saved:{filepath.name}"
    )

    print(raw.dtype)
    print(raw.max())