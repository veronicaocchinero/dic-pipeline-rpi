from picamera2 import Picamera2
import numpy as np
import time
import csv
from pathlib import Path

# =============================
# CONFIG
# =============================

RESOLUTION = (2028, 1520)
GAIN = 1.0
EXPOSURE = 8000
DURATION_SEC = 1200  # 20 min
BLACK_LEVEL = 64
ROI_SIZE = 1024

CSV_FILE = Path("temporal_stability_video_2k.csv")

# =============================
# UTILS
# =============================

def extract_green(raw):
    raw = raw.astype(np.int32) - BLACK_LEVEL
    raw[raw < 0] = 0
    h, w = raw.shape
    return raw[0:h:2, 1:w:2]

def central_roi(img, size):
    h, w = img.shape
    cy = h // 2
    cx = w // 2
    half = size // 2
    return img[cy-half:cy+half, cx-half:cx+half]

# =============================
# MAIN
# =============================

def main():

    cam = Picamera2()

    config = cam.create_video_configuration(
        main={"size": (640, 480)},
        raw={"size": RESOLUTION},
        buffer_count=6
    )

    cam.configure(config)
    cam.start()

    cam.set_controls({
        "AeEnable": False,
        "AwbEnable": False,
        "AnalogueGain": GAIN,
        "ExposureTime": EXPOSURE
    })

    time.sleep(1)

    start_time = time.time()

    with open(CSV_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Time_s",
            "Mean_signal",
            "Std_signal",
            "Exposure_real_us",
            "FrameDuration_us"
        ])

        while (time.time() - start_time) < DURATION_SEC:

            request = cam.capture_request()
            metadata = request.get_metadata()
            raw = request.make_array("raw")
            request.release()

            green = extract_green(raw)
            roi = central_roi(green, ROI_SIZE)

            mean_signal = roi.mean()
            std_signal = roi.std()

            real_exp = metadata.get("ExposureTime")
            frame_dur = metadata.get("FrameDuration")

            t = time.time() - start_time

            print(f"t={t:.1f}s | mean={mean_signal:.2f} | FD={frame_dur}")

            writer.writerow([
                round(t, 3),
                round(mean_signal, 4),
                round(std_signal, 4),
                real_exp,
                frame_dur
            ])

    cam.stop()
    cam.close()

    print("=== COMPLETATO VIDEO TEST ===")

if __name__ == "__main__":
    main()