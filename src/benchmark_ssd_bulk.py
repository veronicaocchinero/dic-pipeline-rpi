"""
benchmark_ssd_bulk.py
---------------------
Benchmark SSD scientifico pulito.

• still vs video
• full, 4K, 2K, FHD
• exposure 15000 / 10000
• scrittura reale RAW
• misura FPS
• misura MB/s
• cancella RAW dopo ogni test
"""

from picamera2 import Picamera2
import time
import csv
import shutil
from pathlib import Path


# ============================
# CONFIGURAZIONE TEST
# ============================

RESOLUTIONS = [
    ("FULL_SENSOR", (4056, 3040)),
    ("4K", (3840, 2160)),
    ("2K", (2028, 1520)),
    ("FHD", (1920, 1080)),
]

MODES = ["still", "video"]

EXPOSURES = [15000, 10000, 5000, 1000]

NUM_FRAMES = 100

SSD_DIR = Path("/mnt/ssd/benchmark_bulk")
SSD_DIR.mkdir(parents=True, exist_ok=True)

CSV_FILE = Path("benchmark_ssd_results.csv")


# ============================
# TEST SINGOLO
# ============================

def run_test(mode, res_name, resolution, exposure):

    cam = Picamera2()

    if mode == "still":
        config = cam.create_still_configuration(
            main={"size": resolution, "format": "RGB888"},
            raw={"size": resolution},
            buffer_count=4
        )
    else:
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

    test_dir = SSD_DIR / f"{mode}_{res_name}_{exposure}"
    test_dir.mkdir(parents=True, exist_ok=True)

    start = time.perf_counter()

    for i in range(NUM_FRAMES):
        request = cam.capture_request()
        raw = request.make_array("raw")
        request.release()

        filepath = test_dir / f"frame_{i:04d}.raw"
        raw.astype("uint16").tofile(filepath)

    total = time.perf_counter() - start
    fps = NUM_FRAMES / total

    cam.stop()
    cam.close()

    # ============================
    # CALCOLI PRESTAZIONALI
    # ============================

    width, height = resolution
    bytes_per_frame = width * height * 2
    total_bytes = bytes_per_frame * NUM_FRAMES

    mb_written = total_bytes / (1024**2)
    mb_per_sec = mb_written / total
    mp_per_sec = (width * height * fps) / 1e6

    # ============================
    # PULIZIA FILE RAW
    # ============================

    shutil.rmtree(test_dir)

    return fps, total, mb_per_sec, mp_per_sec


# ============================
# MAIN
# ============================

def main():

    results = []

    print("\n=== BENCHMARK SSD SCIENTIFICO ===\n")

    for mode in MODES:
        for res_name, resolution in RESOLUTIONS:
            for exposure in EXPOSURES:

                print(f"\nTesting {mode} | {res_name} | exp={exposure}")

                try:
                    fps, total, mbps, mpps = run_test(mode, res_name, resolution, exposure)

                    print(f"FPS: {fps:.2f}")
                    print(f"MB/s: {mbps:.1f}")
                    print(f"MP/s: {mpps:.1f}")

                    results.append([
                        mode,
                        res_name,
                        resolution[0],
                        resolution[1],
                        exposure,
                        round(fps, 2),
                        round(mbps, 1),
                        round(mpps, 1)
                    ])

                except Exception as e:
                    print("ERROR:", e)
                    results.append([
                        mode,
                        res_name,
                        resolution[0],
                        resolution[1],
                        exposure,
                        "ERROR",
                        "ERROR",
                        "ERROR"
                    ])

    with open(CSV_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Mode",
            "Resolution",
            "Width",
            "Height",
            "Exposure_us",
            "FPS_real",
            "MB_per_s",
            "MP_per_s"
        ])
        writer.writerows(results)

    print("\n=== COMPLETATO ===")
    print("Risultati salvati in:", CSV_FILE)


if __name__ == "__main__":
    main()