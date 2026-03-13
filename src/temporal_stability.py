from picamera2 import Picamera2
import numpy as np
import time
import csv
from pathlib import Path

# =============================
# CONFIG
# =============================

RESOLUTION = (2028, 1520)   # 2K sensor mode
GAIN = 1.0
EXPOSURE = 8000             # us
DURATION_SEC = 1200         # 20 min

ROI_SIZE = 1024

CSV_FILE = Path("temporal_stability_video_2k_raw8.csv")

# =============================
# UTILS
# =============================

def extract_green(raw):
    """
    Extract one green channel from Bayer RAW8
    pattern SBGGR8
    """

    raw = raw.astype(np.uint8)

    h, w = raw.shape

    # Green pixels
    green = raw[0:h:2, 1:w:2]

    return green


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

        main={"size": (640,480), "format":"YUV420"},

        raw={
            "size": RESOLUTION,
            "format": "SBGGR8"
        },

        buffer_count=6
    )

    cam.configure(config)

    cam.start()

    cam.set_controls({
    "AeEnable": False,
    "AwbEnable": False,

    "AnalogueGain": GAIN,
    "ExposureTime": EXPOSURE,
    "FrameDurationLimits": (EXPOSURE, EXPOSURE),

    "ColourGains": (1.0, 1.0)
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

            # Green extraction
            green = extract_green(raw)

            # ROI
            roi = central_roi(green, ROI_SIZE)

            mean_signal = roi.mean()
            std_signal = roi.std()

            real_exp = metadata.get("ExposureTime")
            frame_dur = metadata.get("FrameDuration")

            t = time.time() - start_time

            print(f"t={t:.1f}s | mean={mean_signal:.2f} | std={std_signal:.2f} | FD={frame_dur}")

            writer.writerow([
                round(t, 3),
                round(mean_signal, 4),
                round(std_signal, 4),
                real_exp,
                frame_dur
            ])

    cam.stop()
    cam.close()

    print("=== COMPLETATO VIDEO RAW8 TEST ===")


if __name__ == "__main__":
    main()