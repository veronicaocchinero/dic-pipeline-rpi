#!/usr/bin/env python3
"""
clean_nvme.py
=============
Cancella sequenze di acquisizione dall'NVMe, MA SOLO dopo aver
verificato che siano state copiate correttamente sulla USB.

LOGICA DI SICUREZZA (a strati):
  1. Per ogni sequenza, verifica che esista su USB con stesso numero
     di file e stessa dimensione totale (byte-per-byte).
  2. Se la verifica fallisce -> la sequenza viene SALTATA, non cancellata.
  3. Anche se la verifica passa, mostra cosa cancellera' e chiede
     conferma esplicita ("y" + Invio).
  4. Modalita' di default = dry-run: per cancellare davvero serve --confirm.

PATH FISSI:
  - NVMe:  /home/dic/Desktop/dic_project/output/   (symlink a /mnt/ssd/output/)
  - USB:   /media/dic/ESD-USB/dic_backup/

USO
---
    # Mostra cosa cancellerebbe (DEFAULT, sicuro):
    python3 clean_nvme.py seq_0015

    # Cancella davvero (richiede comunque conferma interattiva):
    python3 clean_nvme.py seq_0015 --confirm

    # Cancella TUTTE le sequenze gia' su USB:
    python3 clean_nvme.py --all --confirm

    # Cancella senza chiedere conferma interattiva (NON CONSIGLIATO):
    python3 clean_nvme.py --all --confirm --yes
"""

import argparse
import shutil
import sys
from pathlib import Path

# ============================================================
#  PATH FISSI
# ============================================================

SOURCE_DIR = Path("/home/dic/Desktop/dic_project/output")
USB_DIR    = Path("/media/dic/ESD-USB/dic_backup")


# ============================================================
#  UTILITIES
# ============================================================

def folder_size_bytes(path: Path) -> int:
    return sum(f.stat().st_size for f in path.rglob('*') if f.is_file())

def count_files(path: Path) -> int:
    return sum(1 for f in path.rglob('*') if f.is_file())

def bytes_human(n: int) -> str:
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if n < 1024:
            return f"{n:.2f} {unit}"
        n /= 1024
    return f"{n:.2f} PB"


# ============================================================
#  VERIFICA INTEGRITA' (identica a transfer_to_usb.py)
# ============================================================

def verify_copy(src: Path, dst: Path) -> tuple[bool, str]:
    """Verifica che src e dst contengano stessi file con stesse dimensioni."""
    if not dst.exists():
        return False, f"backup mancante: {dst}"

    src_files = {f.relative_to(src): f.stat().st_size
                 for f in src.rglob('*') if f.is_file()}
    dst_files = {f.relative_to(dst): f.stat().st_size
                 for f in dst.rglob('*') if f.is_file()}

    if len(src_files) != len(dst_files):
        return False, (f"numero file diverso: "
                       f"NVMe={len(src_files)}, USB={len(dst_files)}")

    missing = set(src_files.keys()) - set(dst_files.keys())
    if missing:
        return False, f"file non presenti sulla USB: {len(missing)} files"

    size_mismatches = sum(1 for rp, ss in src_files.items()
                          if dst_files[rp] != ss)
    if size_mismatches > 0:
        return False, f"file con dimensione diversa su USB: {size_mismatches}"

    return True, f"backup OK: {len(src_files)} file, "\
                 f"{bytes_human(sum(src_files.values()))}"


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
        description="Cancella sequenze dall'NVMe (solo se gia' su USB)."
    )
    ap.add_argument('sequences', nargs='*',
                    help="Nomi delle sequenze da cancellare. Ignorato se --all.")
    ap.add_argument('--all', action='store_true',
                    help="Considera tutte le sequenze presenti su NVMe.")
    ap.add_argument('--confirm', action='store_true',
                    help="Conferma cancellazione (senza questo flag, modalita' dry-run).")
    ap.add_argument('--yes', action='store_true',
                    help="Salta la conferma interattiva (USARE CON CAUTELA).")
    args = ap.parse_args()

    # Determina la lista delle sequenze
    if args.all:
        seqs = list_all_sequences()
        if not seqs:
            print("Nessuna sequenza presente su NVMe.")
            sys.exit(0)
    else:
        if not args.sequences:
            ap.print_help()
            print("\nERRORE: specifica almeno una sequenza, o usa --all")
            sys.exit(1)
        seqs = args.sequences

    is_dry_run = not args.confirm
    if is_dry_run:
        print("*** MODALITA' DRY-RUN (default): nessuna cancellazione verra' eseguita ***")
        print("*** Per cancellare davvero aggiungi --confirm                            ***\n")

    # Verifica ogni sequenza
    print(f"{'='*60}")
    print(f"  VERIFICA PRESENZA BACKUP SU USB")
    print(f"{'='*60}")

    to_delete = []
    to_skip = []

    for seq in seqs:
        src = SOURCE_DIR / seq
        dst = USB_DIR / seq

        if not src.exists():
            print(f"  {seq:20s}  -> non esiste su NVMe, SKIP")
            to_skip.append((seq, "non esiste su NVMe"))
            continue

        size = folder_size_bytes(src)
        n_files = count_files(src)

        ok, msg = verify_copy(src, dst)
        if ok:
            print(f"  {seq:20s}  {n_files:6d} file  {bytes_human(size):>12s}  -> "
                  f"backup verificato, OK per cancellazione")
            to_delete.append((seq, src, n_files, size))
        else:
            print(f"  {seq:20s}  {n_files:6d} file  {bytes_human(size):>12s}  -> "
                  f"FAIL: {msg}")
            to_skip.append((seq, msg))

    # Riepilogo
    print(f"\n{'='*60}")
    print(f"  RIEPILOGO PRE-CANCELLAZIONE")
    print(f"{'='*60}")
    print(f"  Da cancellare:  {len(to_delete)} sequenze")
    print(f"  Saltate:        {len(to_skip)} sequenze (backup mancante o incompleto)")

    if to_delete:
        total_size = sum(s for _, _, _, s in to_delete)
        total_files = sum(n for _, _, n, _ in to_delete)
        print(f"  Spazio totale recuperabile: {bytes_human(total_size)}")
        print(f"  Totale file da cancellare:   {total_files}")
        print(f"\n  Sequenze:")
        for seq, _, n, s in to_delete:
            print(f"    - {seq}  ({n} file, {bytes_human(s)})")

    if to_skip:
        print(f"\n  Sequenze SALTATE (non cancellate):")
        for seq, reason in to_skip:
            print(f"    - {seq}: {reason}")
        print(f"\n  Per cancellarle dovresti prima fare backup con transfer_to_usb.py")

    if not to_delete:
        print("\n  Niente da cancellare.")
        sys.exit(0)

    if is_dry_run:
        print(f"\n  [DRY-RUN] Nessuna cancellazione eseguita.")
        print(f"  Per cancellare davvero, rilancia con --confirm")
        sys.exit(0)

    # Conferma interattiva
    if not args.yes:
        print(f"\n  Stai per CANCELLARE PERMANENTEMENTE {len(to_delete)} sequenze dall'NVMe.")
        print(f"  Spazio recuperato: {bytes_human(sum(s for _, _, _, s in to_delete))}")
        print(f"  Tutte le sequenze hanno backup verificato su USB.")
        answer = input(f"\n  Sei sicura? Scrivi 'si' per confermare, qualsiasi altra cosa per annullare: ")
        if answer.strip().lower() not in ('si', 'sì', 'yes', 'y'):
            print("  Annullato. Niente cancellato.")
            sys.exit(0)

    # CANCELLAZIONE EFFETTIVA
    print(f"\n{'='*60}")
    print(f"  CANCELLAZIONE IN CORSO")
    print(f"{'='*60}")

    n_done = 0
    n_err = 0
    for seq, src, n_files, size in to_delete:
        print(f"  Cancellando {seq} ...", end='', flush=True)
        try:
            shutil.rmtree(src)
            print(f" OK ({bytes_human(size)} liberati)")
            n_done += 1
        except Exception as e:
            print(f" ERRORE: {e}")
            n_err += 1

    print(f"\n  Cancellate: {n_done} sequenze")
    if n_err > 0:
        print(f"  Errori:     {n_err} sequenze")
        sys.exit(2)


if __name__ == '__main__':
    main()
