"""
capture_sequence.py
-------------------
Acquisizione RAW ultra-veloce per DIC dinamico.

• Avvio e stop manuali da tastiera (INVIO per partire, INVIO per fermare)
• Nessuno sleep nel loop
• Nessuna conversione TIFF
• Salvataggio RAW8 puro
• Salvataggio timestamp hardware
"""

import time
import csv
import sys
import threading
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
# CONTROLLO START/STOP DA TASTIERA
# ============================================================

def _wait_for_enter(prompt: str):
    """
    Blocca finché l'utente non preme INVIO.
    """
    try:
        input(prompt)
    except EOFError:
        # se stdin viene chiuso, non bloccare
        pass


def _stop_listener(stop_flag: dict):
    """
    Thread di ascolto: aspetta che l'utente prema INVIO e
    setta stop_flag['stop'] = True.

    Gira come daemon in modo da non bloccare l'uscita del programma.
    """
    try:
        sys.stdin.readline()
    except Exception:
        pass
    stop_flag["stop"] = True


# ============================================================
# FUNZIONE PRINCIPALE
# ============================================================

def capture_sequence(max_frames: int | None = None):
    """
    Acquisisce frame RAW8 fino a quando l'utente non preme INVIO
    una seconda volta per fermare.

    Parametri
    ---------
    max_frames : int | None
        Se valorizzato, fa da limite di sicurezza (stop forzato dopo
        N frame anche se l'utente non ha premuto stop).
        Se None, acquisisce indefinitamente fino allo stop manuale.
    """

    print("\n=== ACQUISIZIONE RAW8 MAX FPS (DIC MODE) ===")

    # 1) Crea cartella sequenza
    seq_dir = create_new_sequence_folder()

    # 2) Inizializza camera
    cam = create_camera()

    # 3) CSV timestamp
    timestamp_file = seq_dir / "timestamps.csv"

    # 4) Aspetta START dall'utente
    _wait_for_enter(">>> Premi INVIO per AVVIARE l'acquisizione...")

    # 5) Avvia thread che ascolta lo STOP
    stop_flag = {"stop": False}
    listener = threading.Thread(
        target=_stop_listener,
        args=(stop_flag,),
        daemon=True,
    )
    listener.start()

    print(">>> Acquisizione in corso. Premi INVIO per FERMARE.\n")

    i = 0
    raw = None  # per il print finale del dtype

    with open(timestamp_file, "w", newline="") as csvfile:

        writer = csv.writer(csvfile)
        writer.writerow(["frame", "sensor_timestamp_ns", "exposure_us", "gain"])

        start_time = time.perf_counter()

        while not stop_flag["stop"]:

            # limite di sicurezza opzionale
            if max_frames is not None and i >= max_frames:
                print(f"\n[seq] Raggiunto max_frames={max_frames}, stop automatico.")
                break

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

            # RAW8 diretto
            with open(filepath, "wb") as f:
                f.write(raw)

            # timestamp
            writer.writerow([i, sensor_ts, exposure, gain])

            print(
                f"[frame {i:04d}] "
                f"exp:{exposure} "
                f"gain:{gain:.2f}"
            )

            i += 1

        total_time = time.perf_counter() - start_time
        num_frames = i
        fps_real = (num_frames / total_time) if total_time > 0 else 0.0

    print("\n=== SEQUENZA COMPLETATA ===")
    print(f"Frame acquisiti: {num_frames}")
    print(f"Durata totale: {total_time:.3f} s")
    print(f"FPS reali medi: {fps_real:.2f}")
    print(f"Cartella: {seq_dir}")

    cam.stop()
    cam.close()

    print("[seq] Camera chiusa correttamente.")
    if raw is not None:
        print(raw.dtype)


# ============================================================
# ENTRYPOINT
# ============================================================

if __name__ == "__main__":
    # Esempio: nessun limite -> acquisisci finché non premi stop
    capture_sequence()

    # In alternativa, con limite di sicurezza:
    # capture_sequence(max_frames=DEFAULT_NUM_FRAMES)