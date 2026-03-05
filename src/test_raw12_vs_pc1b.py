from picamera2 import Picamera2
import numpy as np
import time

RESOLUTION = (2028, 1520)
EXPOSURE = 8000

def acquire(mode):

    cam = Picamera2()

    if mode == "pc1b":
        config = cam.create_still_configuration(
            main={"size": (640, 480), "format": "RGB888"},
            raw={"size": RESOLUTION}
        )
    else:
        # Forziamo RAW 12-bit non compresso
        config = cam.create_still_configuration(
            main={"size": (640, 480), "format": "RGB888"},
            raw={
                "size": RESOLUTION,
                "format": "SBGGR12"
            }
        )

    cam.configure(config)
    cam.start()

    cam.set_controls({
        "AeEnable": False,
        "AwbEnable": False,
        "AnalogueGain": 1.0,
        "ExposureTime": EXPOSURE
    })

    time.sleep(0.5)

    request = cam.capture_request()
    raw = request.make_array("raw")
    metadata = request.get_metadata()
    request.release()

    cam.stop()
    cam.close()

    print(f"\n=== MODE: {mode} ===")
    print("dtype:", raw.dtype)
    print("shape:", raw.shape)
    print("min:", raw.min())
    print("max:", raw.max())

    return raw


raw_pc1b = acquire("pc1b")
raw_12bit = acquire("raw12")

# confronto istogrammi base
print("\nMean PC1B:", raw_pc1b.mean())
print("Mean RAW12:", raw_12bit.mean())