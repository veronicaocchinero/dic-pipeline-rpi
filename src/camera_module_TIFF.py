"""
camera_module.py
----------------
Gestione camera IMX477 per acquisizione scientifica DIC.

Pipeline:
RAW12 → black level correction → green channel → TIFF16

Include:
- Modalità manuale pura (AE OFF)
- FrameDuration configurabile
- Lettura metadata reali per ogni frame
"""

from picamera2 import Picamera2
import numpy as np
import imageio.v3 as iio
from pathlib import Path
import time

from src.config import (
    CAMERA_RESOLUTION,
    EXPOSURE_TIME_US,
    ANALOG_GAIN
)

# ============================================================
# 1️⃣ Inizializzazione camera in modalità MANUALE pura
# ============================================================

def create_camera():

    cam = Picamera2()

    config = cam.create_still_configuration(
        main={"size": (640, 480), "format": "RGB888"},
        raw={"size": CAMERA_RESOLUTION},
        buffer_count=4
    )

    cam.configure(config)
    cam.start()

    # 🔴 Disabilita completamente automatismi
    cam.set_controls({
        "AeEnable": False,
        "AwbEnable": False,
        "AeExposureMode": 0,
        "AeConstraintMode": 0
    })

    time.sleep(0.2)

    # 🔴 Imposta frame duration con range ampio
    cam.set_controls({
        "FrameDurationLimits": (10000, 300000)
    })

    time.sleep(0.1)

    # 🔴 Imposta exposure e gain manuali
    cam.set_controls({
        "ExposureTime": EXPOSURE_TIME_US,
        "AnalogueGain": ANALOG_GAIN
    })

    time.sleep(0.3)

    # 🔎 Verifica reale
    metadata = cam.capture_metadata()

    print("\n[camera] Modalità MANUALE attiva")
    print("[camera] Config Exposure:", EXPOSURE_TIME_US)
    print("[camera] Config Gain:", ANALOG_GAIN)
    print("[camera] REAL Exposure:", metadata.get("ExposureTime"))
    print("[camera] REAL Gain:", metadata.get("AnalogueGain"))
    print()

    return cam


# ============================================================
# 2️⃣ Acquisizione RAW → TIFF16 con metadata reali
# ============================================================

def capture_raw_tiff(cam, filepath: Path):

    filepath.parent.mkdir(parents=True, exist_ok=True)

    # ========================================================
    # Cattura richiesta completa (RAW + metadata)
    # ========================================================
    request = cam.capture_request()

    metadata = request.get_metadata()
    real_exp = metadata.get("ExposureTime")
    real_gain = metadata.get("AnalogueGain")

    raw = request.make_array("raw")
    request.release()

    # ========================================================
    # Black level correction
    # ========================================================
    black = 64
    raw = raw.astype(np.int32) - black
    raw[raw < 0] = 0

    # ========================================================
    # Estrazione canale verde (RGGB → G1)
    # ========================================================
    h, w = raw.shape
    green = raw[0:h:2, 1:w:2]

    # Clip 12 bit
    green = np.clip(green, 0, 4095)

    # ========================================================
    # Conversione 12 → 16 bit
    # ========================================================
    tiff16 = (green.astype(np.uint16) << 4)

    iio.imwrite(str(filepath), tiff16)

    # ========================================================
    # Monitor dinamica
    # ========================================================
    min_v = green.min()
    max_v = green.max()
    mean_v = green.mean()
    std_v = green.std()
    sat_pct = (green >= 4095).sum() / green.size * 100

    print(
        f"[frame] exp:{real_exp} gain:{real_gain:.2f} "
        f"min:{min_v} max:{max_v} "
        f"mean:{mean_v:.1f} std:{std_v:.1f} "
        f"sat:{sat_pct:.2f}%"
    )