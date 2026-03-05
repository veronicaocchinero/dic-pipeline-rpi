from picamera2 import Picamera2
import time
import csv
import numpy as np

# ==========================
# CONFIG
# ==========================

RESOLUTION = (2028, 1520)  # usa 2K
EXPOSURE = 15000
NUM_FRAMES = 1000

CSV_FILE = "still_vs_video_deterministic.csv"


# ==========================
# TEST FUNZIONE
# ==========================

def run_test(mode):

    cam = Picamera2()

    if mode == "still":
        config = cam.create_still_configuration(
            main={"size": (640, 480), "format": "RGB888"},
            raw={"size": RESOLUTION},
            buffer_count=4
        )
    else:
        config = cam.create_video_configuration(
            main={"size": (640, 480), "format": "RGB888"},
            raw={"size": RESOLUTION},
            buffer_count=6
        )

    cam.configure(config)
    cam.start()

    cam.set_controls({
        "AeEnable": False,
        "AwbEnable": False,
        "AnalogueGain": 1.0,
        "FrameDurationLimits": (EXPOSURE, EXPOSURE),
        "ExposureTime": EXPOSURE
    })

    time.sleep(0.7)  # warm-up

    # Warm-up frames non misurati
    for _ in range(20):
        req = cam.capture_request()
        req.release()

    timestamps = []
    exposures = []
    durations = []

    start = time.perf_counter()

    for i in range(NUM_FRAMES):

        t = time.perf_counter()

        request = cam.capture_request()
        metadata = request.get_metadata()
        request.release()

        timestamps.append(t)
        exposures.append(metadata.get("ExposureTime"))
        durations.append(metadata.get("FrameDuration"))

    total = time.perf_counter() - start

    cam.stop()
    cam.close()

    # ==========================
    # CALCOLI
    # ==========================

    timestamps = np.array(timestamps)
    exposures = np.array(exposures)
    durations = np.array(durations)

    delta_t = np.diff(timestamps)

    fps_mean = NUM_FRAMES / total
    dt_mean = np.mean(delta_t)
    dt_std = np.std(delta_t)

    exp_mean = np.mean(exposures)
    exp_std = np.std(exposures)

    dur_mean = np.mean(durations)
    dur_std = np.std(durations)

    return [
        mode,
        round(fps_mean, 3),
        round(dt_mean * 1000, 4),  # ms
        round(dt_std * 1000, 4),   # ms
        round(exp_mean, 2),
        round(exp_std, 4),
        round(dur_mean, 2),
        round(dur_std, 4)
    ]


# ==========================
# MAIN
# ==========================

def main():

    print("\n=== STILL vs VIDEO DETERMINISTIC TEST ===\n")

    results = []

    for mode in ["still", "video"]:
        print(f"Testing {mode}...")
        res = run_test(mode)
        results.append(res)

    with open(CSV_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Mode",
            "FPS_mean",
            "Delta_t_mean_ms",
            "Delta_t_std_ms",
            "Exposure_mean_us",
            "Exposure_std_us",
            "FrameDuration_mean_us",
            "FrameDuration_std_us"
        ])
        writer.writerows(results)

    print("\n=== COMPLETATO ===")
    print("Risultati salvati in:", CSV_FILE)


if __name__ == "__main__":
    main()