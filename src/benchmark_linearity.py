from picamera2 import Picamera2
import numpy as np
import time
import csv
from pathlib import Path

# =============================
# CONFIG
# =============================

RESOLUTION = (2028,1520)

EXPOSURES = [
1000,
2000,
4000,
8000,
16000,
32000
]

FRAMES_PER_EXPOSURE = 50
ROI_SIZE = 1024

CSV_FILE = Path("sensor_linearity_2k_raw8.csv")

# =============================
# UTILS
# =============================

def extract_green(raw):

    h,w = raw.shape
    return raw[0:h:2,1:w:2]

def central_roi(img,size):

    h,w = img.shape
    cy = h//2
    cx = w//2
    half = size//2

    return img[cy-half:cy+half, cx-half:cx+half]

# =============================
# MAIN
# =============================

def main():

    cam = Picamera2()

    config = cam.create_video_configuration(

        main={"size":(640,480),"format":"YUV420"},

        raw={
        "size":RESOLUTION,
        "format":"SBGGR8"
        },

        buffer_count=6
    )

    cam.configure(config)
    cam.start()

    cam.set_controls({

        "AeEnable":False,
        "AwbEnable":False,

        "AnalogueGain":1.0,

        "ColourGains":(1.0,1.0)
    })

    time.sleep(2)

    with open(CSV_FILE,"w",newline="") as f:

        writer = csv.writer(f)

        writer.writerow([
        "Exposure_set_us",
        "Exposure_real_us",
        "Mean_signal",
        "Std_signal"
        ])

        for exp in EXPOSURES:

            cam.set_controls({
                "ExposureTime":exp,
                "FrameDurationLimits":(exp,exp)
            })

            time.sleep(0.5)

            means = []

            for i in range(FRAMES_PER_EXPOSURE):

                request = cam.capture_request()
                metadata = request.get_metadata()

                raw = request.make_array("raw")
                request.release()

                green = extract_green(raw)
                roi = central_roi(green,ROI_SIZE)

                means.append(roi.mean())

                real_exp = metadata.get("ExposureTime")

            mean_signal = np.mean(means)
            std_signal = np.std(means)

            print(f"EXP={exp} | mean={mean_signal:.2f}")

            writer.writerow([
                exp,
                real_exp,
                round(mean_signal,4),
                round(std_signal,4)
            ])

    cam.stop()
    cam.close()

    print("=== LINEARITY TEST COMPLETED ===")

if __name__ == "__main__":
    main()