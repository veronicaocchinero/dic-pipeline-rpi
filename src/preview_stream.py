"""
preview_stream.py
-----------------
Preview live della camera HQ via streaming MJPEG su browser.

Avvio:
    python -m src.preview_stream

Poi sul PC apri il browser su:
    http://<IP_DEL_PI>:8000

Stessa configurazione scientifica del preview.py originale:
- AE/AWB disabilitati
- Exposure e gain fissi da src.config
- Statistiche del canale verde stampate in console

Chiusura: Ctrl+C nel terminale.
"""

import io
import time
import threading
import socketserver
from http import server

import cv2
import numpy as np
from picamera2 import Picamera2

from src.config import (
    EXPOSURE_TIME_US,
    ANALOG_GAIN,
    CAMERA_RESOLUTION,
)


# ============================================================
# PORTA HTTP
# ============================================================

STREAM_PORT = 8000

# Qualità JPEG del preview (1-100). Più alta = qualità migliore + banda maggiore.
# 70-80 è un buon compromesso per Wi-Fi/hotspot.
JPEG_QUALITY = 90

# Dimensione preview nel browser (downscale da CAMERA_RESOLUTION per
# alleggerire la banda; il sensore continua a girare a piena res).
PREVIEW_SIZE = (2028, 1520)


# ============================================================
# HTML PAGINA
# ============================================================

PAGE = """\
<!DOCTYPE html>
<html>
<head>
<title>DIC Preview - Raspberry Pi HQ</title>
<style>
  body { background:#111; color:#eee; font-family: sans-serif; margin:0; padding:1em; }
  h1 { font-size: 1.1em; margin: 0 0 0.5em 0; }
  img { display:block; max-width:100%; height:auto; border:1px solid #333; }
  .info { margin-top:0.5em; color:#888; font-size:0.85em; }
</style>
</head>
<body>
<h1>DIC Preview - Raspberry Pi HQ Camera (IMX477)</h1>
<img src="stream.mjpg" />
<div class="info">
  Streaming MJPEG. Chiudi il tab per smettere di ricevere.
  Per terminare il server, Ctrl+C nel terminale del Pi.
</div>
</body>
</html>
"""


# ============================================================
# OUTPUT BUFFER (frame condiviso tra producer e HTTP server)
# ============================================================

class StreamingOutput:
    """
    Buffer thread-safe per l'ultimo frame JPEG.
    Producer: il loop di capture.
    Consumer: la GET handler che serve lo stream MJPEG.
    """
    def __init__(self):
        self.frame = None
        self.condition = threading.Condition()

    def write(self, buf):
        with self.condition:
            self.frame = buf
            self.condition.notify_all()


output = StreamingOutput()


# ============================================================
# HTTP HANDLER
# ============================================================

class StreamingHandler(server.BaseHTTPRequestHandler):

    def do_GET(self):

        if self.path == "/":
            self.send_response(301)
            self.send_header("Location", "/index.html")
            self.end_headers()

        elif self.path == "/index.html":
            content = PAGE.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)

        elif self.path == "/stream.mjpg":
            self.send_response(200)
            self.send_header("Age", "0")
            self.send_header("Cache-Control", "no-cache, private")
            self.send_header("Pragma", "no-cache")
            self.send_header(
                "Content-Type",
                "multipart/x-mixed-replace; boundary=FRAME",
            )
            self.end_headers()
            try:
                while True:
                    with output.condition:
                        output.condition.wait()
                        frame = output.frame
                    if frame is None:
                        continue
                    self.wfile.write(b"--FRAME\r\n")
                    self.send_header("Content-Type", "image/jpeg")
                    self.send_header("Content-Length", str(len(frame)))
                    self.end_headers()
                    self.wfile.write(frame)
                    self.wfile.write(b"\r\n")
            except (BrokenPipeError, ConnectionResetError):
                # client ha chiuso il tab: normale, non è un errore
                pass

        else:
            self.send_error(404)
            self.end_headers()

    def log_message(self, format, *args):
        # silenzia i log HTTP per non sporcare la console con le statistiche
        pass


class StreamingServer(socketserver.ThreadingMixIn, server.HTTPServer):
    allow_reuse_address = True
    daemon_threads = True


# ============================================================
# CAMERA + STATISTICHE
# ============================================================

def _camera_setup():
    """
    Stessa configurazione scientifica del preview.py originale:
    AE/AWB off, exposure e gain fissi.
    """
    picam2 = Picamera2()

    config = picam2.create_still_configuration(
        main={"size": CAMERA_RESOLUTION, "format": "RGB888"},
        raw={"size": CAMERA_RESOLUTION},
        buffer_count=4,
    )
    picam2.configure(config)
    picam2.start()

    picam2.set_controls({
        "AeEnable": False,
        "AwbEnable": False,
        "AeExposureMode": 0,
        "AeConstraintMode": 0,
    })
    time.sleep(0.2)

    picam2.set_controls({
        "FrameDurationLimits": (10000, 300000),
    })
    time.sleep(0.1)

    picam2.set_controls({
        "ExposureTime": EXPOSURE_TIME_US,
        "AnalogueGain": ANALOG_GAIN,
    })
    time.sleep(0.3)

    metadata = picam2.capture_metadata()
    print("\n=== PREVIEW STREAM SCIENTIFICA ===")
    print("Config Exposure:", EXPOSURE_TIME_US)
    print("Config Gain:", ANALOG_GAIN)
    print("REAL Exposure:", metadata["ExposureTime"])
    print("REAL Gain:", metadata["AnalogueGain"])
    print(f"\nApri nel browser: http://<IP_DEL_PI>:{STREAM_PORT}")
    print("Ctrl+C per terminare.\n")

    return picam2


def _green_channel_stats(raw):
    """
    Statistiche sul canale verde Bayer (BGGR -> green a (0,1) e (1,0)).
    Identico al preview.py originale.
    """
    black = 64
    raw = raw.astype(np.int32) - black
    raw[raw < 0] = 0
    h, w = raw.shape
    green = raw[0:h:2, 1:w:2]
    green = np.clip(green, 0, 4095)
    return green.min(), green.max(), green.mean(), \
           (green >= 4095).sum() / green.size * 100


# ============================================================
# CAPTURE LOOP (thread separato)
# ============================================================

_stop_flag = threading.Event()


def _capture_loop(picam2):
    """
    Cattura RGB+RAW, comprime in JPEG, aggiorna l'output, stampa stats.
    """
    encode_params = [int(cv2.IMWRITE_JPEG_QUALITY), JPEG_QUALITY]

    while not _stop_flag.is_set():

        # cattura frame RGB per il preview
        frame = picam2.capture_array()

        # downscale per alleggerire lo stream
        small = cv2.resize(frame, PREVIEW_SIZE, interpolation=cv2.INTER_AREA)

        # OpenCV usa BGR per imencode, ma frame è RGB → swap
        small_bgr = cv2.cvtColor(small, cv2.COLOR_RGB2BGR)

        ok, jpeg = cv2.imencode(".jpg", small_bgr, encode_params)
        if ok:
            output.write(jpeg.tobytes())

        # statistiche sul RAW (stesso comportamento del preview.py)
        raw = picam2.capture_array("raw")
        gmin, gmax, gmean, gsat = _green_channel_stats(raw)
        print(
            f"min:{gmin} "
            f"max:{gmax} "
            f"mean:{gmean:.1f} "
            f"sat:{gsat:.2f}%   ",
            end="\r",
        )


# ============================================================
# MAIN
# ============================================================

def main():

    picam2 = _camera_setup()

    # thread di acquisizione
    cap_thread = threading.Thread(
        target=_capture_loop,
        args=(picam2,),
        daemon=True,
    )
    cap_thread.start()

    # server HTTP nel main thread (così Ctrl+C lo chiude pulito)
    address = ("0.0.0.0", STREAM_PORT)
    httpd = StreamingServer(address, StreamingHandler)

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[stream] Ctrl+C ricevuto, chiusura in corso...")
    finally:
        _stop_flag.set()
        cap_thread.join(timeout=2.0)
        try:
            picam2.stop()
            picam2.close()
        except Exception:
            pass
        httpd.server_close()
        print("[stream] Server chiuso, camera rilasciata. Bye.")


if __name__ == "__main__":
    main()