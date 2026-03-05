"""
config.py
---------
In questo file mettiamo TUTTI i parametri configurabili del sistema DIC.
Così il resto del codice può usarli senza avere numeri "magici" sparsi ovunque.
"""

from pathlib import Path

# === PERCORSI ===============================================================

# Cartella di base del progetto (cartella "dic_project")
BASE_DIR = Path(__file__).resolve().parent.parent

# Cartella dove salveremo le sequenze di immagini per il DIC
# (per ora dentro "output"; quando avrai l'SSD basterà cambiare solo questa riga)
SEQUENCES_DIR = BASE_DIR / "output"

#SEQUENCES_DIR = Path("/mnt/nvme/dic_sequences")


# === PARAMETRI CAMERA =======================================================

# Risoluzione del sensore (larghezza, altezza)
# Per test: 1920x1080; per DIC serio userai probabilmente la piena risoluzione del sensore IMX477
#Opzione (full res 12MP)
#CAMERA_RESOLUTION = (4056, 3040)

#Opzione B – più FPS (Full HD)
#CAMERA_RESOLUTION = (1920, 1080)


CAMERA_RESOLUTION = (2028, 1080)

# Formato file immagine salvata.
# Opzioni:
#  - "jpg"  → compresso, leggero ma con perdita (NON consigliato per DIC)
#  - "png"  → lossless ma 8 bit (meglio, ma non ideale)
#  - "dng"  → RAW a 12 bit del sensore IMX477 (SCELTA MIGLIORE per DIC)
IMAGE_FORMAT = "dng"

# Profondità RAW del sensore (IMX477 = 12 bit)
#commentare se si usa IMAGE FORMAT jpg o png
RAW_BIT_DEPTH = 12

# Parametri di esposizione (che poi imposteremo nel modulo della camera)
# Valori in microsecondi (µs). 15000 µs = 1/66 s circa.
#Valori tipici: 8000 µs → luce forte -- 15000 µs → normale -- 30000 µs → poca luce
EXPOSURE_TIME_US =  15000  # per ora solo segnaposto, verrà usato dopo

# Guadagno analogico (ISO). Valore 1.0 = base, >1 = più luminoso ma più rumore.
ANALOG_GAIN = 1.0        #Se serve più luce: 2.0


# === PARAMETRI DI ACQUISIZIONE SEQUENZA =====================================

# Numero di frame da acquisire in una sequenza standard
DEFAULT_NUM_FRAMES = 200

# Intervallo tra i frame espresso in secondi.
# Esempio: 0.05 s = 20 frame al secondo "target" (poi vedremo gli fps reali)
DEFAULT_FRAME_INTERVAL_S = 0.05

# Prefisso del nome cartella di ogni sequenza (es. seq_0001, seq_0002, ...)
SEQUENCE_FOLDER_PREFIX = "seq_"

# Prefisso dei file contenenti i frame (es. frame_0000.jpg, frame_0001.jpg, ...)
FRAME_FILENAME_PREFIX = "frame_"


# === FUNZIONI DI SUPPORTO (OPZIONALI MA COMODE) =============================

def get_sequence_base_dir() -> Path:
    """
    Ritorna la cartella base dove verranno salvate le sequenze.
    (Per ora è <BASE_DIR>/output, ma in futuro potrà essere /mnt/nvme/dic_sequences)
    """
    return SEQUENCES_DIR

