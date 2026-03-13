from picamera2 import Picamera2
import numpy as np
import time

RESOLUTION = (2028, 1520)
EXPOSURE = 8000
GAIN = 1.0

OUTPUT = "prova2.raw"

def main():

    cam = Picamera2()

    # SOLO STREAM RAW
    config = cam.create_still_configuration(
        raw={
            "size": RESOLUTION,
            "format": "SBGGR8"   # 8-bit nativo sensore
        },
        buffer_count=4
    )

    cam.configure(config)
    cam.start()

    cam.set_controls({
        "AeEnable": False,
        "AwbEnable": False,
        "ExposureTime": EXPOSURE,
        "AnalogueGain": GAIN
    })

    time.sleep(1)

    print("Acquisizione RAW 8-bit lineare...")

    request = cam.capture_request()

    raw = request.make_array("raw")
    request.release()

    cam.stop()
    cam.close()

    # raw arriva come uint16 (container SBGGR16)
    print("dtype:", raw.dtype)
    print("shape:", raw.shape)

    raw.tofile(OUTPUT)

    print("Salvato:", OUTPUT)


if __name__ == "__main__":
    main()