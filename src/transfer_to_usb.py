#!/usr/bin/env python3
"""
transfer_to_usb.py
==================
Trasferisce una o piu' sequenze di acquisizione dall'NVMe alla chiavetta
USB, con verifica di integrita' del trasferimento. NON cancella nulla
dall'NVMe (per quello c'e' clean_nvme.py).

PATH FISSI (modificare se la tua configurazione cambia):
  - sorgente:    /home/dic/Desktop/dic_project/output/    (symlink a /mnt/ssd/output/)
  - destinazione: /media/dic/ESD-USB/dic_backup/

USO
---
    # Trasferisce UNA sequenza specifica:
    python3 transfer_to_usb.py seq_0015

    # Trasferisce piu' sequenze:
    python3 transfer_to_usb.py seq_0015 seq_0016 seq_0017

    # Trasferisce TUTTE le sequenze presenti su NVMe:
    python3 transfer_to_usb.py --all

    # Mostra cosa farebbe senza copiare nulla:
    python3 transfer_to_usb.py --all --dry-run

VERIFICA DI INTEGRITA'
----------------------
Per ogni sequenza copiata, lo script verifica:
  - stesso numero di file su NVMe e USB
  - stessa dimensione totale (byte per byte)
  - dimensione esatta uguale per ogni singolo file
Se la verifica fallisce, la sequenza viene marcata come 'FAILED' e
non e' sicuro cancellarla dall'NVMe.
"""

import argparse
import shutil
import sys
from datetime import datetime
from pathlib import Path

# ============================================================
#  PATH FISSI
# ============================================================

SOURCE_DIR = Path("/home/dic/Desktop/dic_project/output")
USB_DIR    = Path("/media/dic/ESD-USB/dic_backup")

# Margine minimo di spazio libero da lasciare sulla USB dopo il trasferimento
MIN_FREE_SPACE_MB = 100


# ============================================================
#  UTILITIES
# ============================================================

def folder_size_bytes(path: Path) -> int:
    """Calcola dimensione totale ricorsiva di una cartella."""
    return sum(f.stat().st_size for f in path.rglob('*') if f.is_file())


def count_files(path: Path) -> int:
    """Conta i file (ricorsivi) in una cartella."""
    return sum(1 for f in path.rglob('*') if f.is_file())


def bytes_human(n: int) -> str:
    """Format leggibile di una dimensione in byte."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if n < 1024:
            return f"{n:.2f} {unit}"
        n /= 1024
    return f"{n:.2f} PB"


def free_space_bytes(path: Path) -> int:
    """Spazio libero sul filesystem che contiene path."""
    stat = shutil.disk_usage(path)
    return stat.free


# ============================================================
#  VERIFICA INTEGRITA'
# ============================================================

def verify_copy(src: Path, dst: Path) -> tuple[bool, str]:
    """
    Verifica che src e dst contengano esattamente gli stessi file
    con le stesse dimensioni.

    Returns:
        (ok, messaggio)
    """
    if not dst.exists():
        return False, f"destinazione non esiste: {dst}"

    src_files = {f.relative_to(src): f.stat().st_size
                 for f in src.rglob('*') if f.is_file()}
    dst_files = {f.relative_to(dst): f.stat().st_size
                 for f in dst.rglob('*') if f.is_file()}

    if len(src_files) != len(dst_files):
        return False, (f"numero file diverso: "
                       f"sorgente={len(src_files)}, destinazione={len(dst_files)}")

    missing = set(src_files.keys()) - set(dst_files.keys())
    if missing:
        return False, f"file mancanti in destinazione: {len(missing)} files"

    extra = set(dst_files.keys()) - set(src_files.keys())
    if extra:
        return False, f"file extra in destinazione: {len(extra)} files"

    # confronto dimensioni file per file
    size_mismatches = []
    for rel_path, src_size in src_files.items():
        dst_size = dst_files[rel_path]
        if src_size != dst_size:
            size_mismatches.append((rel_path, src_size, dst_size))

    if size_mismatches:
        msg_lines = [f"file con dimensione diversa: {len(size_mismatches)}"]
        for rp, ss, ds in size_mismatches[:5]:
            msg_lines.append(f"  {rp}: src={ss} byte, dst={ds} byte")
        if len(size_mismatches) > 5:
            msg_lines.append(f"  ... e altri {len(size_mismatches)-5}")
        return False, "\n".join(msg_lines)

    return True, f"OK: {len(src_files)} file, {bytes_human(sum(src_files.values()))}"


# ============================================================
#  TRASFERIMENTO
# ============================================================

def transfer_sequence(seq_name: str, dry_run: bool = False) -> bool:
    """
    Trasferisce una singola sequenza dalla NVMe alla USB.

    Returns:
        True se il trasferimento e la verifica sono andati bene.
    """
    src = SOURCE_DIR / seq_name
    dst = USB_DIR / seq_name

    print(f"\n{'='*60}")
    print(f"Sequenza: {seq_name}")
    print(f"{'='*60}")

    # Verifica sorgente
    if not src.exists():
        print(f"  ERRORE: sorgente non trovata: {src}")
        return False
    if not src.is_dir():
        print(f"  ERRORE: sorgente non e' una cartella: {src}")
        return False

    # Statistiche sorgente
    n_files = count_files(src)
    size = folder_size_bytes(src)
    print(f"  Sorgente:    {src}")
    print(f"  File:        {n_files}")
    print(f"  Dimensione:  {bytes_human(size)}")

    # Verifica spazio USB
    if not USB_DIR.parent.exists():
        print(f"  ERRORE: chiavetta USB non montata: {USB_DIR.parent}")
        return False

    free = free_space_bytes(USB_DIR.parent)
    needed = size + MIN_FREE_SPACE_MB * 1024 * 1024
    print(f"  Spazio USB libero: {bytes_human(free)}")
    if free < needed:
        print(f"  ERRORE: spazio insufficiente sulla USB.")
        print(f"          Servono {bytes_human(needed)} (sequenza + margine),"
              f" disponibili {bytes_human(free)}")
        return False

    # Se destinazione gia' esiste, salta (sicurezza)
    if dst.exists():
        print(f"  ATTENZIONE: destinazione esiste gia': {dst}")
        # Verifica se e' gia' completa
        ok, msg = verify_copy(src, dst)
        if ok:
            print(f"  Gia' presente e verificata: {msg}")
            print(f"  -> SKIP (gia' presente correttamente)")
            return True
        else:
            print(f"  Gia' presente ma INCOMPLETA: {msg}")
            print(f"  -> SKIP. Cancella manualmente {dst} e rilancia.")
            return False

    if dry_run:
        print(f"  [DRY-RUN] Avrei copiato in: {dst}")
        return True

    # Crea cartella destinazione padre se serve
    USB_DIR.mkdir(parents=True, exist_ok=True)

    # Copia
    print(f"  Copia in corso verso: {dst}")
    t0 = datetime.now()
    try:
        shutil.copytree(src, dst)
    except Exception as e:
        print(f"  ERRORE durante copia: {e}")
        return False
    elapsed = (datetime.now() - t0).total_seconds()
    speed = size / elapsed / (1024*1024) if elapsed > 0 else 0
    print(f"  Copia completata in {elapsed:.1f} s ({speed:.1f} MB/s)")

    # Verifica integrita'
    print(f"  Verifica integrita'...")
    ok, msg = verify_copy(src, dst)
    if ok:
        print(f"  VERIFICA OK: {msg}")
        return True
    else:
        print(f"  VERIFICA FALLITA: {msg}")
        print(f"  -> la cartella {dst} potrebbe essere corrotta. NON cancellare la sorgente.")
        return False


# ============================================================
#  MAIN
# ============================================================

def list_all_sequences():
    """Lista tutte le seq_NNNN presenti su NVMe."""
    if not SOURCE_DIR.exists():
        return []
    seqs = [d.name for d in SOURCE_DIR.iterdir()
            if d.is_dir() and d.name.startswith('seq_')]
    return sorted(seqs)


def main():
    ap = argparse.ArgumentParser(
        description="Trasferisce sequenze di acquisizione da NVMe a USB."
    )
    ap.add_argument('sequences', nargs='*',
                    help="Nomi delle sequenze da trasferire (es. seq_0015 seq_0016). "
                         "Ignorato se si usa --all.")
    ap.add_argument('--all', action='store_true',
                    help="Trasferisci TUTTE le sequenze presenti su NVMe.")
    ap.add_argument('--dry-run', action='store_true',
                    help="Simula senza copiare nulla.")
    args = ap.parse_args()

    # Determina la lista delle sequenze da trasferire
    if args.all:
        seqs = list_all_sequences()
        if not seqs:
            print("Nessuna sequenza trovata su NVMe.")
            sys.exit(0)
        print(f"Trovate {len(seqs)} sequenze su NVMe: {', '.join(seqs)}")
    else:
        if not args.sequences:
            ap.print_help()
            print("\nERRORE: specifica almeno una sequenza, o usa --all")
            sys.exit(1)
        seqs = args.sequences

    if args.dry_run:
        print("\n*** MODALITA' DRY-RUN: niente verra' copiato ***")

    # Statistiche iniziali
    print(f"\nDestinazione USB: {USB_DIR}")
    if USB_DIR.parent.exists():
        free = free_space_bytes(USB_DIR.parent)
        print(f"Spazio libero USB: {bytes_human(free)}")
    else:
        print(f"ERRORE: USB non montata su {USB_DIR.parent}")
        sys.exit(1)

    # Trasferisci
    results = {}
    for seq in seqs:
        results[seq] = transfer_sequence(seq, dry_run=args.dry_run)

    # Riepilogo
    print(f"\n{'='*60}")
    print(f"  RIEPILOGO")
    print(f"{'='*60}")
    n_ok = sum(1 for v in results.values() if v)
    n_failed = sum(1 for v in results.values() if not v)
    for seq, ok in results.items():
        status = "OK" if ok else "FAILED"
        print(f"  {seq:20s} {status}")
    print(f"\n  Totale: {n_ok} OK, {n_failed} FALLITE")

    if n_failed > 0:
        print(f"\n  NON cancellare le sequenze fallite dall'NVMe.")
        sys.exit(2)
    else:
        print(f"\n  Tutte le sequenze trasferite correttamente.")
        print(f"  Puoi usare clean_nvme.py per cancellarle dall'NVMe.")
        sys.exit(0)


if __name__ == '__main__':
    main()
