"""
camera_module.py
----------------
Versione ultra-veloce per acquisizione RAW pura.

Pipeline:
RAW12 → salvataggio binario diretto (.raw)

Nessuna conversione TIFF.
Nessuna elaborazione live.
Massima velocità di scrittura.
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
# 1️⃣ Inizializzazione camera (VIDEO mode per max FPS)
# ============================================================

def create_camera():

    cam = Picamera2()

    # 🔴 Usare VIDEO configuration per massima velocità
    config = cam.create_video_configuration(
        main={"size": (640, 480), "format": "RGB888"},
        raw={"size": CAMERA_RESOLUTION},
        buffer_count=6
    )

    cam.configure(config)
    cam.start()

    # 🔴 Disabilita automatismi
    cam.set_controls({
        "AeEnable": False,
        "AwbEnable": False,
        "ExposureTime": EXPOSURE_TIME_US,
        "AnalogueGain": ANALOG_GAIN,
        "FrameDurationLimits": (1000, 300000)
    })

    time.sleep(0.5)

    metadata = cam.capture_metadata()

    print("\n[camera] RAW ULTRA-FAST MODE")
    print("[camera] Config Exposure:", EXPOSURE_TIME_US)
    print("[camera] Config Gain:", ANALOG_GAIN)
    print("[camera] REAL Exposure:", metadata.get("ExposureTime"))
    print("[camera] REAL Gain:", metadata.get("AnalogueGain"))
    print()

    return cam


# ============================================================
# 2️⃣ Acquisizione RAW pura (NO conversione)
# ============================================================

def capture_raw_fast(cam, filepath: Path):

    filepath.parent.mkdir(parents=True, exist_ok=True)

    # 🔴 Cattura richiesta completa
    request = cam.capture_request()

    metadata = request.get_metadata()
    real_exp = metadata.get("ExposureTime")
    real_gain = metadata.get("AnalogueGain")

    raw = request.make_array("raw")
    request.release()

    # 🔴 Salvataggio diretto binario (ULTRA VELOCE)
    raw.astype(np.uint16).tofile(filepath)

    # 🔴 Log minimale (senza calcoli pesanti)
    print(
        f"[frame] exp:{real_exp} gain:{real_gain:.2f} "
        f"saved:{filepath.name}"
    )