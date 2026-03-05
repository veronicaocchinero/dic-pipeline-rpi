"""
capture_video_raw.py
--------------------
Acquisizione RAW ad alta velocità usando video pipeline.
"""

from picamera2 import Picamera2
import time
from src.config import EXPOSURE_TIME_US, ANALOG_GAIN

# ===============================
# PARAMETRI
# ===============================

VIDEO_RES = (1920, 1080)  # prova 1332x990 high-speed
NUM_FRAMES = 300

# ===============================
# MAIN
# ===============================

def main():

    cam = Picamera2()

    config = cam.create_video_configuration(
        main={"size": VIDEO_RES, "format": "RGB888"},
        raw={"size": VIDEO_RES},
        buffer_count=6
    )

    cam.configure(config)
    cam.start()

    # Modalità manuale pura
    cam.set_controls({
        "AeEnable": False,
        "AwbEnable": False,
        "ExposureTime": EXPOSURE_TIME_US,
        "AnalogueGain": ANALOG_GAIN,
        "FrameDurationLimits": (1000, 300000)
    })

    time.sleep(0.5)

    print("\n=== VIDEO RAW MAX FPS ===")
    print("Exposure:", EXPOSURE_TIME_US)
    print("Gain:", ANALOG_GAIN)

    start = time.perf_counter()

    for i in range(NUM_FRAMES):

        request = cam.capture_request()

        raw = request.make_array("raw")
        metadata = request.get_metadata()

        request.release()

        if i % 20 == 0:
            print(
                f"[{i}] exp:{metadata['ExposureTime']} "
                f"gain:{metadata['AnalogueGain']}"
            )

    total = time.perf_counter() - start
    fps = NUM_FRAMES / total

    print("\n=== RISULTATO ===")
    print("Durata:", total)
    print("FPS reali:", fps)

    cam.stop()
    cam.close()


if __name__ == "__main__":
    main()