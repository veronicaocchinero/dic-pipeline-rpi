"""
capture_sequence.py
-------------------
Acquisizione RAW ultra-veloce per DIC dinamico.

• Nessun sleep
• Nessuna conversione TIFF
• Salvataggio RAW8 puro
• Salvataggio timestamp hardware
"""

import time
import csv
from pathlib import Path

from src.config import (
    DEFAULT_NUM_FRAMES,
)

from src.storage import (
    create_new_sequence_folder,
    get_frame_filename,
)

from src.camera_module import (
    create_camera,
)


# ============================================================
# FUNZIONE PRINCIPALE
# ============================================================

def capture_sequence(num_frames: int = DEFAULT_NUM_FRAMES):

    print("\n=== ACQUISIZIONE RAW8 MAX FPS (DIC MODE) ===")

    # 1️⃣ Crea cartella sequenza
    seq_dir = create_new_sequence_folder()

    # 2️⃣ Inizializza camera
    cam = create_camera()

    # 3️⃣ CSV timestamp
    timestamp_file = seq_dir / "timestamps.csv"

    with open(timestamp_file, "w", newline="") as csvfile:

        writer = csv.writer(csvfile)
        writer.writerow(["frame", "sensor_timestamp_ns", "exposure_us", "gain"])

        start_time = time.perf_counter()

        for i in range(num_frames):

            request = cam.capture_request()

            metadata = request.get_metadata()

            raw = request.make_array("raw")

            request.release()

            # metadata
            sensor_ts = metadata.get("SensorTimestamp")
            exposure = metadata.get("ExposureTime")
            gain = metadata.get("AnalogueGain")

            # filepath
            filepath = get_frame_filename(seq_dir, i, "raw")

            # 🔴 RAW8 diretto
            with open(filepath, "wb") as f:
                f.write(raw)
            

            # timestamp
            writer.writerow([i, sensor_ts, exposure, gain])

            print(
                f"[frame {i:04d}] "
                f"exp:{exposure} "
                f"gain:{gain:.2f}"
            )

        total_time = time.perf_counter() - start_time
        fps_real = num_frames / total_time

    print("\n=== SEQUENZA COMPLETATA ===")
    print(f"Durata totale: {total_time:.3f} s")
    print(f"FPS reali medi: {fps_real:.2f}")
    print(f"Cartella: {seq_dir}")

    cam.stop()
    cam.close()

    print("[seq] Camera chiusa correttamente.")
    print(raw.dtype)

# ============================================================
# ENTRYPOINT
# ============================================================

if __name__ == "__main__":
    capture_sequence()
