"""
benchmark_snr_global_v2.py
--------------------------
Versione diagnostica SNR globale.

Include:
- Verifica ExposureTime reale
- FrameDurationLimits forzato
- Controllo mean RAW globale
"""

import time
import csv
import numpy as np
from pathlib import Path
from picamera2 import Picamera2

# ============================================================
# CONFIG
# ============================================================

RESOLUTION = (2028, 1520)
GAIN = 1.0

EXPOSURES = [1000, 5000, 10000, 20000, 40000]
FRAMES_PER_EXPOSURE = 20

ROI_SIZE = 1024
BLACK_LEVEL = 64

CSV_FILE = Path("benchmark_snr_global_v2.csv")

# ============================================================
# UTILS
# ============================================================

def extract_green(raw):
    raw = raw.astype(np.int32) - BLACK_LEVEL
    raw[raw < 0] = 0
    h, w = raw.shape
    green = raw[0:h:2, 1:w:2]
    return green

def central_roi(img, size):
    h, w = img.shape
    cy = h // 2
    cx = w // 2
    half = size // 2
    return img[cy-half:cy+half, cx-half:cx+half]

# ============================================================
# MAIN
# ============================================================

def main():

    cam = Picamera2()

    config = cam.create_still_configuration(
        main={"size": (640, 480), "format": "RGB888"},
        raw={"size": RESOLUTION},
        buffer_count=4
    )

    cam.configure(config)
    cam.start()

    # 🔴 Modalità manuale totale
    cam.set_controls({
        "AeEnable": False,
        "AwbEnable": False,
        "AnalogueGain": GAIN,
        "FrameDurationLimits": (1000, 500000)
    })

    time.sleep(0.5)

    results = []

    print("\n=== BENCHMARK SNR GLOBALE V2 ===\n")

    for exposure in EXPOSURES:

        print(f"\nExposure impostata = {exposure} us")

        cam.set_controls({
            "ExposureTime": exposure
        })

        time.sleep(0.4)

        means = []
        stds = []

        for i in range(FRAMES_PER_EXPOSURE):

            request = cam.capture_request()
            metadata = request.get_metadata()
            raw = request.make_array("raw")
            request.release()

            real_exp = metadata.get("ExposureTime")

            green = extract_green(raw)
            roi = central_roi(green, ROI_SIZE)

            means.append(roi.mean())
            stds.append(roi.std())

        mean_signal = np.mean(means)
        std_noise = np.mean(stds)

        snr = mean_signal / std_noise
        snr_db = 20 * np.log10(snr)

        print(f"Exposure reale media: {real_exp}")
        print(f"Mean: {mean_signal:.2f}")
        print(f"Std:  {std_noise:.2f}")
        print(f"SNR:  {snr:.2f}")
        print(f"SNR dB: {snr_db:.2f}")

        results.append([
            exposure,
            real_exp,
            round(mean_signal, 2),
            round(std_noise, 2),
            round(snr, 2),
            round(snr_db, 2)
        ])

    cam.stop()
    cam.close()

    # ============================================================
    # SALVATAGGIO
    # ============================================================

    with open(CSV_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Exposure_set_us",
            "Exposure_real_us",
            "Mean_signal",
            "Std_noise",
            "SNR",
            "SNR_dB"
        ])
        writer.writerows(results)

    print("\n=== COMPLETATO ===")
    print("Risultati salvati in:", CSV_FILE)


if __name__ == "__main__":
    main()