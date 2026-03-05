from picamera2 import Picamera2
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
    ("FULL_SENSOR", (4056, 3040)),
    ("4K",          (4056, 2160)),
    ("2K",          (2028, 1520)),
    ("FHD",         (2028, 1080)),
]

EXPOSURES = [1000, 5000, 10000, 15000]

NUM_FRAMES = 300
N_RUNS = 3

STRIDE = 4096

OUTPUT_DIR = Path("/mnt/ssd/benchmark_picam_raw8")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

CSV_FILE = Path("benchmark_picam_raw8_timestamp.csv")


# ============================
# UTILS
# ============================

def flush_cache():
    os.sync()


def run_mode(resolution, exposure, mode):

    width, height = resolution

    cam = Picamera2()

    if mode == "VIDEO":
        config = cam.create_video_configuration(
            main={"size": (640, 480), "format": "YUV420"},
            raw={"size": resolution, "format": "SBGGR8"},
            buffer_count=6
        )
    else:
        config = cam.create_still_configuration(
            main={"size": (640, 480), "format": "YUV420"},
            raw={"size": resolution, "format": "SBGGR8"},
            buffer_count=4
        )

    cam.configure(config)
    cam.start()

    cam.set_controls({
        "AeEnable": False,
        "AwbEnable": False,
        "ExposureTime": exposure,
        "FrameDurationLimits": (exposure, exposure)
    })

    time.sleep(0.5)

    timestamps = []

    for i in range(NUM_FRAMES):

        request = cam.capture_request()
        metadata = request.get_metadata()

        raw = request.make_array("raw")

        request.release()

        sensor_ts = metadata.get("SensorTimestamp")
        timestamps.append(sensor_ts)

        # scrittura su SSD
        filepath = OUTPUT_DIR / f"tmp_{i:04d}.raw"
        raw.astype(np.uint8).tofile(filepath)

    cam.stop()
    cam.close()

    flush_cache()

    # rimozione file temporanei
    for f in OUTPUT_DIR.glob("tmp_*.raw"):
        f.unlink()

    # calcolo FPS da timestamp hardware
    timestamps = np.array(timestamps)
    dt = np.diff(timestamps) / 1e9  # ns → s

    fps = 1 / np.mean(dt)
    jitter_std = np.std(dt)

    return fps, jitter_std


# ============================
# MAIN
# ============================

def main():

    results = []

    print("\n=== PICAMERA2 RAW8 TIMESTAMP BENCHMARK ===\n")

    for res_name, resolution in RESOLUTIONS:
        width, height = resolution

        for exposure in EXPOSURES:

            for mode in ["STILL", "VIDEO"]:

                fps_runs = []
                jitter_runs = []

                for _ in range(N_RUNS):
                    fps, jitter = run_mode(resolution, exposure, mode)
                    fps_runs.append(fps)
                    jitter_runs.append(jitter)

                fps_mean = np.mean(fps_runs)
                fps_std  = np.std(fps_runs)

                # MIPI data rate
                mipi_MBps = (width * height * fps_mean) / (1024**2)

                # Storage data rate
                storage_MBps = (STRIDE * height * fps_mean) / (1024**2)

                print(
                    f"{res_name} | {mode} | exp={exposure} | "
                    f"FPS={fps_mean:.2f} | "
                    f"Jitter={np.mean(jitter_runs)*1000:.3f} ms | "
                    f"MIPI={mipi_MBps:.1f} MB/s | "
                    f"Storage={storage_MBps:.1f} MB/s"
                )

                results.append([
                    res_name,
                    mode,
                    exposure,
                    round(fps_mean, 2),
                    round(fps_std, 2),
                    round(np.mean(jitter_runs), 6),
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
            "Jitter_std_s",
            "MIPI_MB_per_s",
            "Storage_MB_per_s"
        ])
        writer.writerows(results)

    print("\nCSV salvato in:", CSV_FILE)


if __name__ == "__main__":
    main()