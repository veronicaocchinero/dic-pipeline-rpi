"""
config.py
---------
Parametri configurabili del sistema DIC.
Tutto centralizzato qui per evitare numeri "magici".
"""

from pathlib import Path

# ============================================================
# PERCORSI
# ============================================================

# Cartella base progetto
BASE_DIR = Path(__file__).resolve().parent.parent

# Cartella output sequenze
SEQUENCES_DIR = BASE_DIR / "output"

# Se userai SSD/NVMe:
# SEQUENCES_DIR = Path("/mnt/nvme/dic_sequences")


# ============================================================
# PARAMETRI CAMERA
# ============================================================

# Risoluzione sensore (RAW8)
# Consigliato per DIC + FPS decenti
CAMERA_RESOLUTION = (2028, 1520)

# Formato frame salvato
# RAW8 → file binario puro
IMAGE_FORMAT = "raw"

# Parametri esposizione

# microsecondi
# 8000 = luce forte
# 15000 = luce media
# 30000 = luce bassa
EXPOSURE_TIME_US = 15000

# Guadagno analogico
# 1.0 = base
# 2.0 = più luminoso ma più rumore
ANALOG_GAIN = 1.0


# ============================================================
# PARAMETRI ACQUISIZIONE SEQUENZA
# ============================================================

# Numero frame per sequenza
DEFAULT_NUM_FRAMES = 200

# Intervallo tra frame (solo se usi capture temporizzata)
DEFAULT_FRAME_INTERVAL_S = 0.05

# Prefisso cartelle sequenza
SEQUENCE_FOLDER_PREFIX = "seq_"

# Prefisso file frame
FRAME_FILENAME_PREFIX = "frame_"


# ============================================================
# FUNZIONI UTILI
# ============================================================

def get_sequence_base_dir() -> Path:
    """
    Cartella base dove salvare le sequenze DIC.
    """
    return SEQUENCES_DIR


def get_frame_size_bytes() -> int:
    """
    Dimensione di un frame RAW8 in byte.
    Utile per benchmark velocità disco.
    """

    width, height = CAMERA_RESOLUTION

    return width * height