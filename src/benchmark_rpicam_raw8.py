import subprocess
import time
import numpy as np
import csv
from pathlib import Path
import shutil
import os

# ============================
# CONFIG
# ============================

RESOLUTIONS = [
    ("FULL_SENSOR", "4056:3040:8", 4056, 3040),
    ("4K",          "4056:2160:8", 4056, 2160),
    ("2K",          "2028:1520:8", 2028, 1520),
    ("FHD",         "2028:1080:8", 2028, 1080),
]

EXPOSURES = [1000, 5000, 10000, 15000]

NUM_FRAMES = 300
N_RUNS = 3

STRIDE = 4096  # verificato empiricamente

OUTPUT_DIR = Path("/mnt/ssd/benchmark_rpicam_raw8")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

CSV_FILE = Path("benchmark_raw8_full_comparison.csv")


# ============================
# UTILS
# ============================

def flush_cache():
    os.sync()


def run_still(mode_string, exposure):
    temp_dir = OUTPUT_DIR / "temp"
    temp_dir.mkdir(exist_ok=True)

    cmd = [
        "rpicam-raw",
        "--mode", mode_string,
        "--shutter", str(exposure),
        "--segment", str(NUM_FRAMES),
        "-o", str(temp_dir / "frame_%04d.raw")
    ]

    start = time.perf_counter()
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    flush_cache()
    total_time = time.perf_counter() - start

    shutil.rmtree(temp_dir)

    return NUM_FRAMES / total_time


def run_video(mode_string, exposure):
    outfile = OUTPUT_DIR / "video.raw"

    cmd = [
        "rpicam-raw",
        "--mode", mode_string,
        "--shutter", str(exposure),
        "--segment", str(NUM_FRAMES),
        "-o", str(outfile)
    ]

    start = time.perf_counter()
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    flush_cache()
    total_time = time.perf_counter() - start

    outfile.unlink()

    return NUM_FRAMES / total_time


# ============================
# MAIN
# ============================

def main():

    results = []

    print("\n=== RAW8 FULL PIPELINE COMPARISON ===\n")

    for res_name, mode_string, width, height in RESOLUTIONS:
        for exposure in EXPOSURES:

            for mode in ["STILL", "VIDEO"]:

                fps_runs = []

                for _ in range(N_RUNS):
                    if mode == "STILL":
                        fps = run_still(mode_string, exposure)
                    else:
                        fps = run_video(mode_string, exposure)

                    fps_runs.append(fps)

                fps_mean = np.mean(fps_runs)
                fps_std  = np.std(fps_runs)

                # MIPI data rate (pixel reali)
                mipi_MBps = (width * height * fps_mean) / (1024**2)

                # Storage data rate (stride padded)
                storage_MBps = (STRIDE * height * fps_mean) / (1024**2)

                print(
                    f"{res_name} | {mode} | exp={exposure} | "
                    f"FPS={fps_mean:.2f} | "
                    f"MIPI={mipi_MBps:.1f} MB/s | "
                    f"Storage={storage_MBps:.1f} MB/s"
                )

                results.append([
                    res_name,
                    mode,
                    exposure,
                    round(fps_mean, 2),
                    round(fps_std, 2),
                    round(mipi_MBps, 1),
                    round(storage_MBps, 1)
                ])

    with open(CSV_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Resolution",
            "Mode",
            "Exposure_us",
            "FPS_mean",
            "FPS_std",
            "MIPI_MB_per_s",
            "Storage_MB_per_s"
        ])
        writer.writerows(results)

    print("\nCSV salvato in:", CSV_FILE)


if __name__ == "__main__":
    main()