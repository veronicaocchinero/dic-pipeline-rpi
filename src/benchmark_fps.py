"""
benchmark_fps.py
----------------
Benchmark delle prestazioni REALI della pipeline RAW12/DNG:
- Nessuna pausa tra i frame (stress test)
- Misura tempi con alta precisione tramite perf_counter()
- Calcola throughput MB/s, avg, std, min, max
"""

import time
import statistics
from pathlib import Path

from src.camera_module import create_camera, capture_raw_frame
from src.storage import create_new_sequence_folder, get_frame_filename
from src.config import IMAGE_FORMAT, CAMERA_RESOLUTION, EXPOSURE_TIME_US


def benchmark_fps(num_frames=100):
    print("\n=== BENCHMARK RAW12 → STORAGE (NVMe) ===")

    # Cartella di output
    seq_dir = create_new_sequence_folder()

    # Inizializza camera
    cam = create_camera()

    times = []
    total_start = time.perf_counter()

    for i in range(num_frames):

        filepath = get_frame_filename(seq_dir, i, IMAGE_FORMAT)

        t0 = time.perf_counter()
        capture_raw_frame(cam, filepath)
        t1 = time.perf_counter()

        dt = t1 - t0
        times.append(dt)

        print(f"[bench] frame {i+1}/{num_frames}: {dt:.4f} s")

    total_end = time.perf_counter()
    total_time = total_end - total_start
    fps_real = num_frames / total_time

    avg = statistics.mean(times)  #avg = tempo medio per frame (lento = attenzione)
    std = statistics.stdev(times) if len(times) > 1 else 0.0  # std = jitter → instabilità
    t_min = min(times)
    t_max = max(times)  # min/max molto lontani = pipeline instabile (in DIC dinamica)

    # Calcolo throughput teorico (stima dimensione DNG)
    # Formula approssimata per IMX477 RAW12 → DNG
    width, height = CAMERA_RESOLUTION
    approx_raw_bytes = width * height * 2          # RAW12 → 16 bit in DNG
    approx_mb = approx_raw_bytes / (1024 * 1024)
    throughput = approx_mb / avg

    print("\n=== RISULTATI BENCHMARK ===")
    print(f"Frame totali      : {num_frames}")
    print(f"Tempo totale      : {total_time:.3f} s")
    print(f"FPS reali medi    : {fps_real:.2f}")
    print(f"Tempo medio frame : {avg:.4f} s")
    print(f"Deviazione std    : {std:.4f} s   (jitter)")
    print(f"Frame più veloce  : {t_min:.4f} s")
    print(f"Frame più lento   : {t_max:.4f} s")
    print(f"Throughput stimato: {throughput:.1f} MB/s")
    print(f"Dati salvati in   : {seq_dir}\n")

    cam.stop()
    cam.close()

    return fps_real, avg, std


if __name__ == "__main__":
    benchmark_fps()
