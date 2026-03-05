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

EXPOSURES = [1000, 2000, 4000, 8000, 16000, 32000]
FRAMES_PER_EXPOSURE = 20

BLACK_LEVEL = 64
ROI_SIZE = 1024

CSV_FILE = Path("benchmark_linearity.csv")


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

    config = cam.create_still_configuration(
        main={"size": (640, 480), "format": "RGB888"},
        raw={"size": RESOLUTION},
        buffer_count=4
    )

    cam.configure(config)
    cam.start()

    cam.set_controls({
        "AeEnable": False,
        "AwbEnable": False,
        "AnalogueGain": GAIN,
        "FrameDurationLimits": (1000, 500000)
    })

    time.sleep(0.7)

    results = []

    print("\n=== TEST LINEARITÀ ===\n")

    for exposure in EXPOSURES:

        print(f"Exposure impostata: {exposure} us")

        cam.set_controls({"ExposureTime": exposure})
        time.sleep(0.4)

        means = []

        for _ in range(FRAMES_PER_EXPOSURE):

            request = cam.capture_request()
            metadata = request.get_metadata()
            raw = request.make_array("raw")
            request.release()

            real_exp = metadata.get("ExposureTime")

            green = extract_green(raw)
            roi = central_roi(green, ROI_SIZE)

            means.append(roi.mean())

        mean_signal = np.mean(means)
        std_signal = np.std(means)

        print(f"Mean: {mean_signal:.2f}  Std(frame-to-frame): {std_signal:.2f}")

        results.append([
            exposure,
            real_exp,
            round(mean_signal, 2),
            round(std_signal, 4)
        ])

    cam.stop()
    cam.close()

    with open(CSV_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Exposure_set_us",
            "Exposure_real_us",
            "Mean_signal",
            "Frame_to_frame_std"
        ])
        writer.writerows(results)

    print("\n=== COMPLETATO ===")
    print("Salvato in:", CSV_FILE)


if __name__ == "__main__":
    main()