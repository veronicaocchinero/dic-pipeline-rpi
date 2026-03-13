"""
storage.py
----------
Gestisce il salvataggio su filesystem:

- Cartelle sequenze
- Nomi file frame RAW
- Metadata JSON
"""

from pathlib import Path
import json
from datetime import datetime

from src.config import (
    get_sequence_base_dir,
    SEQUENCE_FOLDER_PREFIX,
    FRAME_FILENAME_PREFIX,
)

# ============================================================================
# 1️⃣ Trova il prossimo indice libero per le sequenze
# ============================================================================

def get_next_sequence_index() -> int:
    """
    Analizza la cartella base e trova il prossimo indice sequenza.

    Esempio:
    seq_0001
    seq_0002
    """

    base_dir = get_sequence_base_dir().resolve()

    # crea cartella base se non esiste
    if not base_dir.exists():
        base_dir.mkdir(parents=True)

    indices = []

    for item in base_dir.iterdir():

        if not item.is_dir():
            continue

        if not item.name.startswith(SEQUENCE_FOLDER_PREFIX):
            continue

        num_str = item.name.replace(SEQUENCE_FOLDER_PREFIX, "")

        if num_str.isdigit():
            indices.append(int(num_str))

    return 1 if not indices else max(indices) + 1


# ============================================================================
# 2️⃣ Crea cartella sequenza
# ============================================================================

def create_new_sequence_folder() -> Path:
    """
    Crea cartella sequenza:

    seq_0001/
    seq_0002/
    """

    base_dir = get_sequence_base_dir()
    index = get_next_sequence_index()

    folder_name = f"{SEQUENCE_FOLDER_PREFIX}{index:04d}"
    seq_path = base_dir / folder_name

    seq_path.mkdir(parents=True, exist_ok=False)

    print(f"[storage] Creata cartella sequenza: {seq_path}")

    return seq_path


# ============================================================================
# 3️⃣ Genera nome file frame
# ============================================================================

def get_frame_filename(sequence_dir: Path, frame_number: int, ext: str = "raw") -> Path:
    """
    Restituisce nome file frame.

    esempio:
    frame_0000.raw
    frame_0001.raw
    """

    filename = f"{FRAME_FILENAME_PREFIX}{frame_number:04d}.{ext}"

    return sequence_dir / filename


# ============================================================================
# 4️⃣ Salva metadata JSON
# ============================================================================

def save_metadata(sequence_dir: Path, metadata: dict):
    """
    Salva metadata.json nella cartella della sequenza.
    """

    metadata_path = sequence_dir / "metadata.json"

    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=4)

    print(f"[storage] Metadata salvati in: {metadata_path}")


# ============================================================================
# 5️⃣ Timestamp ISO-8601
# ============================================================================

def now_timestamp() -> str:
    """
    Timestamp leggibile per metadata.
    """
    return datetime.now().isoformat()