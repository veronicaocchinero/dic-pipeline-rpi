"""
benchmark_fps_with_write.py
---------------------------
Benchmark FPS reale con scrittura TIFF su SSD.
"""

from picamera2 import Picamera2
import time
import csv
from pathlib import Path
import numpy as np
import imageio.v3 as iio

# ===============================
# PARAMETRI
# ===============================

RESOLUTIONS = [
    (2028, 1520),
    (1920, 1080),
    (1332, 990),
]

EXPOSURES = [25000, 15000, 10000]

NUM_FRAMES = 200

OUTPUT_DIR = Path("/mnt/ssd/fps_test")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

CSV_FILE = Path("fps_with_write_results.csv")


# ===============================
# Salvataggio RAW → TIFF16
# ===============================

def save_tiff(raw, filepath):

    black = 64
    raw = raw.astype(np.int32) - black
    raw[raw < 0] = 0

    h, w = raw.shape
    green = raw[0:h:2, 1:w:2]
    green = np.clip(green, 0, 4095)

    tiff16 = (green.astype(np.uint16) << 4)

    iio.imwrite(str(filepath), tiff16)


# ===============================
# Test singolo
# ===============================

def run_test(resolution, exposure):

    cam = Picamera2()

    config = cam.create_video_configuration(
        main={"size": resolution, "format": "RGB888"},
        raw={"size": resolution},
        buffer_count=6
    )

    cam.configure(config)
    cam.start()

    cam.set_controls({
        "AeEnable": False,
        "AwbEnable": False,
        "ExposureTime": exposure,
        "AnalogueGain": 1.0
    })

    time.sleep(0.5)

    start = time.perf_counter()

    for i in range(NUM_FRAMES):

        request = cam.capture_request()
        raw = request.make_array("raw")
        request.release()

        filepath = OUTPUT_DIR / f"{resolution[0]}x{resolution[1]}_{exposure}_{i:04d}.tiff"
        save_tiff(raw, filepath)

    total = time.perf_counter() - start
    fps = NUM_FRAMES / total

    cam.stop()
    cam.close()

    return fps, total


# ===============================
# MAIN
# ===============================

def main():

    results = []

    print("\n=== BENCHMARK CON SCRITTURA SSD ===\n")

    for res in RESOLUTIONS:
        for exp in EXPOSURES:

            print(f"Testing {res} | exp={exp}")

            try:
                fps, total = run_test(res, exp)

                print(f" -> FPS reale: {fps:.2f}")

                results.append([
                    f"{res[0]}x{res[1]}",
                    exp,
                    round(fps, 2),
                    round(total, 3)
                ])

            except Exception as e:
                print("ERROR:", e)
                results.append([
                    f"{res[0]}x{res[1]}",
                    exp,
                    "ERROR",
                    "ERROR"
                ])

    with open(CSV_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Resolution", "Exposure_us", "FPS_real", "Total_time_s"])
        writer.writerows(results)

    print("\n=== COMPLETATO ===")
    print("Risultati salvati in:", CSV_FILE)


if __name__ == "__main__":
    main()