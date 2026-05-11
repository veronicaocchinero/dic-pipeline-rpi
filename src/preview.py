from picamera2 import Picamera2
import cv2
import numpy as np
import time
from src.config import EXPOSURE_TIME_US, ANALOG_GAIN, CAMERA_RESOLUTION

def preview_live():

    picam2 = Picamera2()

    config = picam2.create_still_configuration(
        main={"size":CAMERA_RESOLUTION, "format": "RGB888"},
        raw={"size": CAMERA_RESOLUTION},
        buffer_count=4
    )

    picam2.configure(config)
    picam2.start()

    # 🔴 Disattiva completamente automatismi
    picam2.set_controls({
        "AeEnable": False,
        "AwbEnable": False,
        "AeExposureMode": 0,
        "AeConstraintMode": 0
    })

    time.sleep(0.2)

    # 🔴 Imposta frame duration PRIMA
    picam2.set_controls({
        "FrameDurationLimits": (10000, 300000)
    })

    time.sleep(0.1)

    # 🔴 Poi exposure e gain
    picam2.set_controls({
        "ExposureTime": EXPOSURE_TIME_US,
        "AnalogueGain": ANALOG_GAIN
    })

    time.sleep(0.3)

    metadata = picam2.capture_metadata()
    print("\n=== PREVIEW MANUALE SCIENTIFICA ===")
    print("Config Exposure:", EXPOSURE_TIME_US)
    print("Config Gain:", ANALOG_GAIN)
    print("REAL Exposure:", metadata["ExposureTime"])
    print("REAL Gain:", metadata["AnalogueGain"])
    print("Premi 'q' per uscire\n")

    while True:

        frame = picam2.capture_array()
        cv2.imshow("Preview RGB", frame)

        raw = picam2.capture_array("raw")

        black = 64
        raw = raw.astype(np.int32) - black
        raw[raw < 0] = 0

        h, w = raw.shape
        green = raw[0:h:2, 1:w:2]
        green = np.clip(green, 0, 4095)

        print(
            f"min:{green.min()} "
            f"max:{green.max()} "
            f"mean:{green.mean():.1f} "
            f"sat:{(green>=4095).sum()/green.size*100:.2f}%   ",
            end="\r"
        )

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    picam2.stop()
    picam2.close()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    preview_live()