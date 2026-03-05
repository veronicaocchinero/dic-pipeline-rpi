"""
benchmark_fps_matrix.py
-----------------------
Esegue benchmark automatico FPS su diverse:
- Risoluzioni
- Modalità (still / video)
- Exposure

Salva risultati in CSV.
"""

from picamera2 import Picamera2
import time
import csv
from pathlib import Path

# ===============================
# PARAMETRI TEST
# ===============================

RESOLUTIONS = [
    (4056, 3040),
    (2028, 1520),
    (1920, 1080),
    (1332, 990),
]

MODES = ["still", "video"]

EXPOSURES = [
    25000,
    15000,
    10000,
]

NUM_FRAMES = 200

OUTPUT_CSV = Path("fps_benchmark_results.csv")


# ===============================
# Funzione benchmark singolo test
# ===============================

def run_test(mode, resolution, exposure):

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
        "AnalogueGain": 1.0,
        "FrameDurationLimits": (1000, 300000)
    })

    time.sleep(0.5)

    start = time.perf_counter()

    for _ in range(NUM_FRAMES):
        request = cam.capture_request()
        request.release()

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

    print("\n=== FPS BENCHMARK MATRIX ===\n")

    for mode in MODES:
        for res in RESOLUTIONS:
            for exp in EXPOSURES:

                print(f"Testing: {mode} | {res} | exp={exp}")

                try:
                    fps, total = run_test(mode, res, exp)

                    print(f" -> FPS: {fps:.2f}")

                    results.append([
                        mode,
                        f"{res[0]}x{res[1]}",
                        exp,
                        round(fps, 2),
                        round(total, 3)
                    ])

                except Exception as e:
                    print(f" -> ERROR: {e}")
                    results.append([
                        mode,
                        f"{res[0]}x{res[1]}",
                        exp,
                        "ERROR",
                        "ERROR"
                    ])

    # Scrivi CSV
    with open(OUTPUT_CSV, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Mode", "Resolution", "Exposure_us", "FPS", "Total_time_s"])
        writer.writerows(results)

    print("\n=== COMPLETATO ===")
    print(f"Risultati salvati in: {OUTPUT_CSV}")


if __name__ == "__main__":
    main()