"""
calibra_camera.py
-----------------
Estrae i parametri di calibrazione della camera IMX477 a partire dalle foto
del checkerboard salvate in output/calibration.

Usa:
- cornerSubPix
- calibrateCamera
- salva intrinseche e distorsione in JSON
"""

import cv2
import numpy as np
from pathlib import Path
import json


# ==========================================================
# Parametri checkerboard (modifica se necessario)
# ==========================================================

CHECKERBOARD = (9, 6)   # numero di corner interni (orizzontali, verticali)
SQUARE_SIZE = 5.0       # mm (modifica secondo il tuo checkerboard)


CALIB_FOLDER = Path("output/calibration")
OUTPUT_JSON = Path("camera_calibration.json")


# ==========================================================
# Funzione principale
# ==========================================================

def calibrate_camera():

    images = sorted(CALIB_FOLDER.glob("*.jpg"))
    if not images:
        print("[calib] Nessuna immagine trovata.")
        return

    print(f"[calib] Trovate {len(images)} immagini per la calibrazione.")

    # punti 3D nello spazio reale
    objp = np.zeros((CHECKERBOARD[0] * CHECKERBOARD[1], 3), np.float32)
    objp[:, :2] = np.mgrid[0:CHECKERBOARD[0],
                           0:CHECKERBOARD[1]].T.reshape(-1, 2)
    objp *= SQUARE_SIZE

    objpoints = []   # punti 3D reali
    imgpoints = []   # punti 2D rilevati nelle immagini

    for img_file in images:
        img = cv2.imread(str(img_file))
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        success, corners = cv2.findChessboardCorners(gray, CHECKERBOARD, None)

        if success:
            # raffina corner
            corners = cv2.cornerSubPix(
                gray,
                corners,
                winSize=(11, 11),
                zeroZone=(-1, -1),
                criteria=(
                    cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER,
                    30,
                    0.001
                )
            )

            objpoints.append(objp)
            imgpoints.append(corners)

            print(f"[calib] Corner trovati in {img_file.name}")
        else:
            print(f"[calib] NON trovati: {img_file.name}")

    if len(objpoints) < 5:
        print("[calib] Non abbastanza immagini valide.")
        return

    ret, K, dist, rvecs, tvecs = cv2.calibrateCamera(
        objpoints, imgpoints, gray.shape[::-1], None, None
    )

    print("\n=== RISULTATI CALIBRAZIONE ===")
    print("Errore RMS:", ret)
    print("Matrice intrinseca K:\n", K)
    print("Distorsione:", dist.ravel())

    calib_data = {
        "rms_error": float(ret),
        "intrinsic_matrix": K.tolist(),
        "distortion_coeffs": dist.ravel().tolist(),
        "checkerboard": CHECKERBOARD,
        "square_size_mm": SQUARE_SIZE
    }

    with open(OUTPUT_JSON, "w") as f:
        json.dump(calib_data, f, indent=4)

    print(f"\n[calib] Salvato camera_calibration.json")


if __name__ == "__main__":
    calibrate_camera()
