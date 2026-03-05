"""
auto_setup.py
-------------
Script da lanciare all'inizio per avere dei valori consigliati per:

- Esposizione (ExposureTime, in microsecondi)
- Gain (AnalogueGain)
- Intervallo tra frame (DEFAULT_FRAME_INTERVAL_S) e FPS
- Numero di frame per una durata desiderata
- FOV teorico (mm) in funzione della distanza e del provino
- pixel/mm
- distanza teorica camera–provino

Si appoggia a:
- la camera IMX477 (sensor size noto)
- lente 25 mm
- parametri di risoluzione da config.py
"""

import time
import math
from pathlib import Path

from picamera2 import Picamera2
from src.config import CAMERA_RESOLUTION
from src.storage import create_new_sequence_folder, get_frame_filename

# === COSTANTI OTTICHE (IMX477 + LENTE 25 mm) ================================

# Dimensioni sensore IMX477 (approx) in mm
SENSOR_WIDTH_MM = 7.9
SENSOR_HEIGHT_MM = 5.3

# Lunghezza focale obiettivo (C-mount 25 mm)
FOCAL_LENGTH_MM = 25.0


# ============================================================================
# 1. Misura esposizione e gain automatici come base per valori manuali
# ============================================================================

def suggest_exposure_and_gain():
    """
    Attiva l'auto-exposure e auto-gain, lascia stabilizzare,
    e poi legge i valori usati dalla camera come base per la configurazione manuale.
    """
    picam2 = Picamera2()

    config = picam2.create_still_configuration(
        main={"size": CAMERA_RESOLUTION, "format": "RGB888"},
        buffer_count=4
    )
    picam2.configure(config)
#Costruisce una pipeline libcamera ottimizzata per immagini singole, NON video.


    # Auto exposure e auto white balance ON
    picam2.set_controls({"AeEnable": 1, "AwbEnable": 1})

    picam2.start()
    print("[auto_setup] Attendo che l'esposizione automatica si stabilizzi...")
    time.sleep(2.0)  # qualche secondo per stabilizzazione 

    metadata = picam2.capture_metadata()
    exposure_auto = metadata.get("ExposureTime", None)
    gain_auto = metadata.get("AnalogueGain", None)

    picam2.stop()
    picam2.close()
    time.sleep(0.5)

    print(f"[auto_setup] Exposure auto: {exposure_auto} us")
    print(f"[auto_setup] Gain auto: {gain_auto}")

    return exposure_auto, gain_auto


# ============================================================================
# 2. Misura FPS reali salvando N frame (RAW/JPG) e calcola intervallo consigliato
# ============================================================================

def benchmark_fps(num_frames=30, ext="dng"):
    """
    Salva num_frames immagini e misura il tempo medio per frame.
    Da qui ricava gli FPS reali e un intervallo consigliato tra i frame.
    """
    print("\n=== BENCHMARK FPS REALI ===")

    seq_dir = create_new_sequence_folder()
    picam2 = Picamera2()

    config = picam2.create_still_configuration(
        main={"size": CAMERA_RESOLUTION, "format": "RGB888"},
        buffer_count=4
    )
    picam2.configure(config)
    picam2.start()

    times = []

    for i in range(num_frames):
        filepath = get_frame_filename(seq_dir, i, ext)

        t0 = time.time()
        # Per il benchmark possiamo usare capture_file con formato leggibile
        picam2.capture_file(str(filepath))
        t1 = time.time()

        dt = t1 - t0
        times.append(dt)
        print(f"[bench] frame {i+1}/{num_frames}: {dt:.4f} s")

    picam2.stop()

    avg_time = sum(times) / len(times)
    fps_real = 1.0 / avg_time

    # Intervallo consigliato = tempo medio per frame + 10% margine
    interval_s = avg_time * 1.10

    print("\n=== RISULTATO BENCHMARK ===")
    print(f"Tempo medio per frame: {avg_time:.4f} s")
    print(f"FPS reali massimi: {fps_real:.2f} fps")
    print(f"Intervallo consigliato (con margine): {interval_s:.4f} s")

    return fps_real, interval_s


# ============================================================================
# 3. Calcolo FOV, pixel/mm e distanza teorica per un provino
# ============================================================================

def compute_geometry(specimen_width_mm=50.0, margin_factor=1.2):
    """
    Calcola:

    - FOV orizzontale (mm) in modo da includere specimen_width_mm * margin_factor
    - distanza necessaria camera–provino
    - FOV verticale corrispondente (mm)
    - pixel/mm in orizzontale e verticale

    Assunzione: si usa l'intera larghezza del sensore.
    """

    # FOV orizzontale desiderato = larghezza provino * margine
    fov_width_mm = specimen_width_mm * margin_factor

    # Formula pinhole: FOV_width = (SENSOR_WIDTH * distanza) / focale
    # → distanza = (FOV_width * focale) / SENSOR_WIDTH
    distance_mm = (fov_width_mm * FOCAL_LENGTH_MM) / SENSOR_WIDTH_MM

    # FOV verticale coerente con rapporto d'aspetto del sensore
    fov_height_mm = fov_width_mm * (SENSOR_HEIGHT_MM / SENSOR_WIDTH_MM)

    # Pixel/mm (usiamo la risoluzione impostata in config)
    width_px = CAMERA_RESOLUTION[0]
    height_px = CAMERA_RESOLUTION[1]

    px_per_mm_x = width_px / fov_width_mm
    px_per_mm_y = height_px / fov_height_mm

    return {
        "specimen_width_mm": specimen_width_mm,
        "margin_factor": margin_factor,
        "fov_width_mm": fov_width_mm,
        "fov_height_mm": fov_height_mm,
        "distance_mm": distance_mm,
        "px_per_mm_x": px_per_mm_x,
        "px_per_mm_y": px_per_mm_y,
    }


# ============================================================================
# MAIN: esegue tutto e stampa valori consigliati per config.py
# ============================================================================

def main():
    print("\n=== AUTO-SETUP SISTEMA DIC ===\n")

    # 1) Misura esposizione e gain automatici come base
    exposure_auto, gain_auto = suggest_exposure_and_gain()

    # 2) Benchmark FPS reali
    fps_real, interval_s = benchmark_fps(num_frames=20, ext="jpg")

    # 3) Chiedi info sul test e provino
    try:
        durata_test_s = float(input("\nDurata del test desiderata (secondi, es. 10): ") or "10")
    except ValueError:
        durata_test_s = 10.0

    try:
        specimen_width_mm = float(input("Larghezza provino in mm (es. 50): ") or "50")
    except ValueError:
        specimen_width_mm = 50.0

    try:
        margin_factor = float(input("Margine FOV (es. 1.2 → 20% in più): ") or "1.2")
    except ValueError:
        margin_factor = 1.2

    # Numero di frame consigliato in base alla durata e all'intervallo
    num_frames_suggeriti = int(durata_test_s / interval_s)

    geom = compute_geometry(specimen_width_mm, margin_factor)

    print("\n=== RISULTATI CONSIGLIATI (da usare in config.py) ===\n")

    print("# --- Parametri camera ---")
    if exposure_auto is not None:
        print(f"EXPOSURE_TIME_US = {int(exposure_auto)}    # suggerito dall'auto-exposure")
    else:
        print("EXPOSURE_TIME_US = 15000    # valore di default (auto-exposure non letto)")

    if gain_auto is not None:
        print(f"ANALOG_GAIN = {gain_auto:.2f}    # suggerito dall'auto-gain (poi arrotonda se vuoi)")
    else:
        print("ANALOG_GAIN = 1.0    # valore di default (auto-gain non letto)")

    print("\n# --- Parametri sequenza ---")
    print(f"DEFAULT_FRAME_INTERVAL_S = {interval_s:.4f}    # derivato dal benchmark FPS reali")
    print(f"DEFAULT_NUM_FRAMES = {num_frames_suggeriti}    # per circa {durata_test_s}s di test")

    print("\n# --- Geometria ottica (teorica) ---")
    print(f"# Provino: {geom['specimen_width_mm']} mm di larghezza, margine {geom['margin_factor']*100 - 100:.0f}%")
    print(f"# FOV orizzontale ~ {geom['fov_width_mm']:.1f} mm")
    print(f"# FOV verticale   ~ {geom['fov_height_mm']:.1f} mm")
    print(f"# Distanza camera–provino ~ {geom['distance_mm'] / 10:.1f} cm")
    print(f"# pixel/mm (orizzontale) ~ {geom['px_per_mm_x']:.2f}")
    print(f"# pixel/mm (verticale)   ~ {geom['px_per_mm_y']:.2f}")

    print("\nCopia questi valori in config.py adattandoli se necessario.\n")


if __name__ == "__main__":
    main()


# cd dic_project
# python3 -m src.auto_setup

