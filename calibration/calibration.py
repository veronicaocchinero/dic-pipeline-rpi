"""
calibration.py
--------------
Acquisizione di immagini di checkerboard per la calibrazione della camera.

Motivi per cui NON salviamo in RAW:
- la calibrazione è insensibile alla profondità 12/16 bit
- JPG o PNG sono molto più leggere e veloci
- il checkerboard ha contrasto alto → compressione non distorce
"""

from picamera2 import Picamera2
from pathlib import Path
import cv2
import numpy as np
import time

CALIB_FOLDER = Path("output/calibration")
PREVIEW_SIZE = (1280, 720)     # preview più fluida per la finestra OpenCV
SAVE_SIZE = (1920, 1080)       # immagini salvate per calibrazione


# ======================================================
# Funzione principale
# ======================================================

def capture_calibration_images(num_images=20):

    CALIB_FOLDER.mkdir(parents=True, exist_ok=True)

    picam2 = Picamera2()

    config = picam2.create_still_configuration(
        main={"size": SAVE_SIZE, "format": "RGB888"},
        lores={"size": PREVIEW_SIZE, "format": "RGB888"},
        display="lores"     # preview veloce → CPU più libera
    )

    picam2.configure(config)
    picam2.start()

    time.sleep(0.2)  # pipeline warm-up

    print("\n[calib] Premi 's' per salvare un'immagine, 'q' per uscire")
    print("[calib] Assicurati che il checkerboard sia ben illuminato e nitido\n")

    counter = 0
    while counter < num_images:

        # Preview veloce (lores)
        frame = picam2.capture_array("lores")
        cv2.imshow("Calibration Preview", frame)

        key = cv2.waitKey(1) & 0xFF

        if key == ord('s'):

            # Salviamo la versione ad alta risoluzione
            highres = picam2.capture_array("main")

            filepath = CALIB_FOLDER / f"calib_{counter:03d}.jpg"
            cv2.imwrite(str(filepath), highres)

            print(f"[calib] Salvata {filepath.name}")
            counter += 1

        elif key == ord('q'):
            break

    picam2.stop()
    cv2.destroyAllWindows()
    print("[calib] Fine acquisizione.")


if __name__ == "__main__":
    capture_calibration_images()
