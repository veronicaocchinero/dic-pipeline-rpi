"""
test_raw8_all_resolutions.py
----------------------------
Verifica che tutte le risoluzioni usino:

Sensor format: SBGGR8_1X8
CFE format: BYR2

Nessuna compressione PC1B.
"""

from picamera2 import Picamera2
import time

RESOLUTIONS = [
    ("FULL_SENSOR", (4056, 3040)),
    ("4K",          (4056, 2160)),
    ("2K",          (2028, 1520)),
    ("FHD",         (2028, 1080)),
]

def test_resolution(name, size):

    print("\n====================================")
    print(f"Testing: {name} {size}")
    print("====================================\n")

    cam = Picamera2()

    config = cam.create_video_configuration(
        main={"size": (640, 480), "format": "YUV420"},
        raw={"size": size, "format": "SBGGR8"},
        buffer_count=4
    )

    cam.configure(config)
    cam.start()

    time.sleep(1)

    cam.stop()
    cam.close()


def main():

    for name, size in RESOLUTIONS:
        test_resolution(name, size)


if __name__ == "__main__":
    main()
    