"""
storage.py
----------
Gestisce tutto ciò che riguarda il salvataggio su filesystem:
- Cartelle per le sequenze
- Nomi dei file frame
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
# 1. Trova il prossimo indice libero per le sequenze (seq_0001, seq_0002, ...)
# ============================================================================

def get_next_sequence_index() -> int:
    """
    Analizza la cartella base delle sequenze e determina qual è il prossimo
    numero da assegnare. Se non esistono sequenze parte da 1.
    """

    base_dir = get_sequence_base_dir().resolve()

    # 🔴 Se è un symlink valido, NON fare mkdir
    
    base_dir.mkdir(parents=True, exist_ok=True)

    indices = []

    for item in base_dir.iterdir():
        if item.is_dir() and item.name.startswith(SEQUENCE_FOLDER_PREFIX):
            num_str = item.name.replace(SEQUENCE_FOLDER_PREFIX, "")
            if num_str.isdigit():
                indices.append(int(num_str))

    return 1 if not indices else max(indices) + 1

# ============================================================================
# 2. Crea cartella per una nuova sequenza
# ============================================================================

def create_new_sequence_folder() -> Path:
    """
    Crea una cartella di sequenza in formato:
        seq_0001/
        seq_0002/
    """

    base_dir = get_sequence_base_dir()
    index = get_next_sequence_index()

    folder_name = f"{SEQUENCE_FOLDER_PREFIX}{index:04d}"
    seq_path = base_dir / folder_name

    # mkdir eseguito sempre una volta sola
    seq_path.mkdir(parents=True, exist_ok=False)

    print(f"[storage] Creata cartella sequenza: {seq_path}")

    return seq_path


# ============================================================================
# 3. Genera nome del file frame
# ============================================================================

def get_frame_filename(sequence_dir: Path, frame_number: int, ext: str) -> Path:
    """
    Restituisce: frame_0000.dng
    """
    filename = f"{FRAME_FILENAME_PREFIX}{frame_number:04d}.{ext}"
    return sequence_dir / filename


# ============================================================================
# 4. Salva metadata JSON
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
# 5. Timestamp leggibile ISO-8601
# ============================================================================

def now_timestamp() -> str:
    return datetime.now().isoformat()
