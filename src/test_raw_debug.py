from picamera2 import Picamera2
import numpy as np
import time

cam = Picamera2()

config = cam.create_still_configuration(
    main={"size": (640, 480), "format": "RGB888"},
    raw={"size": (2028, 1520)},
    buffer_count=4
)

cam.configure(config)
cam.start()

cam.set_controls({
    "AeEnable": False,
    "AwbEnable": False,
    "ExposureTime": 40000,   # metti exposure alto
    "AnalogueGain": 1.0
})

time.sleep(0.5)

request = cam.capture_request()
raw = request.make_array("raw")

print("dtype:", raw.dtype)
print("shape:", raw.shape)
print("max raw:", raw.max())
print("min raw:", raw.min())

unique_vals = np.unique(raw)
print("Top 10 values:", unique_vals[-10:])

request.release()
cam.stop()
cam.close()