#!/usr/bin/env python3
"""
install_dependencies.py
-----------------------

Installa tutte le dipendenze necessarie per il progetto DIC su Raspberry Pi 5.

Include:
- dipendenze APT di sistema (OpenCV, libcamera, rawpy build deps…)
- creazione ambiente virtuale Python
- installazione pacchetti Python
- check della presenza NVMe
"""

import os
import subprocess
import sys
from pathlib import Path


# ==========================================================
# Funzione helper per eseguire comandi
# ==========================================================

def run(cmd, shell=False):
    print(f"\n[RUN] {cmd}")
    subprocess.run(cmd, shell=shell, check=True)


# ==========================================================
# Sezione 1 — Installazione pacchetti di sistema via APT
# ==========================================================

def install_system_packages():
    print("\n=== INSTALLAZIONE PACCHETTI DI SISTEMA ===")

    run(["sudo", "apt", "update"])
    run(["sudo", "apt", "install", "-y",
         "python3-venv",
         "python3-dev",
         "python3-numpy",
         "libatlas-base-dev",
         "libglib2.0-dev",
         "libopencv-dev",
         "libtiff5",
         "libtiff-dev",
         "libraw-dev",
         "libjpeg-dev",
         "libpng-dev",
         "libcamera-dev",
         "libcamera-apps",
         "git"
    ])

    print("\n[OK] Pacchetti di sistema installati.")


# ==========================================================
# Sezione 2 — Creazione ambiente virtuale
# ==========================================================

def create_venv():
    print("\n=== CREAZIONE AMBIENTE VIRTUALE ===")
    venv_dir = Path("venv")

    if not venv_dir.exists():
        run(["python3", "-m", "venv", "venv"])
        print("[OK] Ambiente virtuale creato.")
    else:
        print("[INFO] Ambiente virtuale già presente.")

    print("\nAttiva l'ambiente con:")
    print("    source venv/bin/activate")


# ==========================================================
# Sezione 3 — Installazione pacchetti Python
# ==========================================================

def install_python_packages():
    print("\n=== INSTALLAZIONE PACCHETTI PYTHON ===")

    pip = "venv/bin/pip"

    run([pip, "install", "--upgrade", "pip"])

    run([pip, "install",
         "rawpy",
         "imageio",
         "opencv-python-headless",
         "tqdm",
         "numpy",
         "matplotlib"
    ])

    print("\n[OK] Pacchetti Python installati.")


# ==========================================================
# Sezione 4 — Check presenza NVMe
# ==========================================================

def check_nvme():
    print("\n=== CHECK DISCO NVMe ===")

    try:
        output = subprocess.check_output("lsblk -o NAME,MODEL | grep nvme", shell=True).decode()
        print("[OK] NVMe rilevata:")
        print(output)
        print("Assicurati che sia montata correttamente prima di salvare sequenze RAW.")
    except subprocess.CalledProcessError:
        print("[WARN] Nessuna NVMe rilevata.")
        print("Puoi installare tutto lo stesso, ma la pipeline DIC andrà più lenta.")
        print("Controlla il M.2 HAT e la SSD.")


# ==========================================================
# ENTRYPOINT
# ==========================================================

if __name__ == "__main__":
    print("\n=== INSTALLER PER PROGETTO DIC — Raspberry Pi 5 ===")

    install_system_packages()
    create_venv()
    install_python_packages()
    check_nvme()

    print("\n=== INSTALLAZIONE COMPLETATA ===")
    print("Ora attiva l'ambiente virtuale:")
    print("   source venv/bin/activate")
    print("E puoi eseguire tutti gli script del progetto.")
