#!/usr/bin/env python3
"""
histogram_check_terminal.py
===========================
Versione terminal-only di histogram_check.py - funziona via SSH senza
bisogno di display grafico.

Mostra:
  - istogramma in ASCII art aggiornato a 2 Hz
  - metriche numeriche live
  - giudizio automatico (OK/WARN/BAD) sull'idoneita' per DIC

Avvio:
  python3 histogram_check_terminal.py --exposure 15000 --gain 1.0

Premi Ctrl+C per uscire.
"""

import argparse
import sys
import time
import shutil

import numpy as np


# ============================================================
#  COLORI ANSI per il terminale
# ============================================================
GREEN  = '\033[92m'
YELLOW = '\033[93m'
RED    = '\033[91m'
CYAN   = '\033[96m'
BOLD   = '\033[1m'
DIM    = '\033[2m'
END    = '\033[0m'
CLEAR  = '\033[2J\033[H'   # pulisce lo schermo e va in alto


# ============================================================
#  ANALISI METRICHE
# ============================================================

def analyze(img, bit_depth=12):
    """Calcola metriche di qualita' dell'immagine per DIC."""
    img = img.astype(np.float64)
    max_val = (1 << bit_depth) - 1
    mean = img.mean()
    return {
        'bit_depth':           bit_depth,
        'max_val':             max_val,
        'min':                 float(img.min()),
        'max':                 float(img.max()),
        'mean':                float(mean),
        'median':              float(np.median(img)),
        'std':                 float(img.std()),
        'pct_saturated':       float((img >= 0.95 * max_val).mean() * 100),
        'pct_dark':            float((img <= 0.05 * max_val).mean() * 100),
        'dynamic_range_used':  float((img.max() - img.min()) / max_val * 100),
        'rms_contrast':        float(img.std() / mean) if mean > 0 else 0,
        'mean_pct':            float(mean / max_val * 100),
    }


def judge_overall(m):
    """Restituisce ('OK'|'WARN'|'BAD', messaggio breve)."""
    if m['mean_pct'] < 25 or m['mean_pct'] > 85 or m['pct_saturated'] > 0.5:
        return ('BAD',  'NON ACQUISIRE - sistema esposizione')
    if m['mean_pct'] < 40 or m['mean_pct'] > 70 or m['pct_saturated'] > 0.01 \
       or m['rms_contrast'] < 0.08:
        return ('WARN', 'ACCETTABILE - migliorabile')
    return ('OK', 'OTTIMALE PER DIC')


# ============================================================
#  ISTOGRAMMA ASCII
# ============================================================

def ascii_histogram(img, max_val, n_bins=60, height=15):
    """
    Costruisce un istogramma ASCII art.

    Args:
        img: immagine 2D
        max_val: valore massimo (4095 per 12-bit, 255 per 8-bit)
        n_bins: numero di bin orizzontali
        height: altezza dell'istogramma in righe
    """
    counts, edges = np.histogram(img.ravel(), bins=n_bins, range=(0, max_val))
    # Scala logaritmica (DIC ha distribuzione con code lunghe)
    counts_log = np.log1p(counts)
    if counts_log.max() == 0:
        return ['(immagine vuota)']

    counts_norm = counts_log / counts_log.max() * height

    # Costruisci righe dal top in giu'
    rows = []
    blocks = ' \u2581\u2582\u2583\u2584\u2585\u2586\u2587\u2588'  # 0-8 livelli
    for h in range(height, 0, -1):
        line = ''
        for c in counts_norm:
            if c >= h:
                line += blocks[8]
            elif c >= h - 1:
                idx = int((c - (h - 1)) * 8)
                line += blocks[idx]
            else:
                line += ' '
        rows.append(line)

    # Asse X
    bin_5pct  = int(0.05 * n_bins)
    bin_95pct = int(0.95 * n_bins)
    axis = list('-' * n_bins)
    axis[0]         = '|'
    axis[bin_5pct]  = '!'   # soglia nero
    axis[n_bins//2] = '+'
    axis[bin_95pct] = '!'   # soglia saturazione
    axis[-1]        = '|'

    # Etichette
    labels = f"0{' ' * (bin_5pct-1)}5%{' ' * (n_bins//2 - bin_5pct - 2)}50%" \
             f"{' ' * (bin_95pct - n_bins//2 - 3)}95%{' ' * (n_bins - bin_95pct - 3)}{int(max_val)}"

    return rows, ''.join(axis), labels


# ============================================================
#  CAMERA SETUP - sequenza corretta per IMX477
# ============================================================

def setup_camera(exposure_us, gain):
    """
    Inizializza la camera con la sequenza che evita il bug AE su IMX477:
    1. configure
    2. set_controls PRIMA di start (cosi' AE parte gia' spento)
    3. start
    4. attesa lunga (warm-up)
    5. verifica metadata
    """
    try:
        from picamera2 import Picamera2
    except ImportError:
        print(f"{RED}ERRORE: picamera2 non installato.{END}")
        print("  pip3 install picamera2 --break-system-packages")
        sys.exit(1)

    picam2 = Picamera2()

    # SOLO stream raw - niente main, niente ISP che interferisce
    config = picam2.create_still_configuration(
        raw={"size": (2028, 1520), "format": "SBGGR8"},
        buffer_count=4,
        # Controls passati alla configurazione - applicati PRIMA di start
        controls={
            "AeEnable":     False,
            "AwbEnable":    False,
            "ExposureTime": int(exposure_us),
            "AnalogueGain": float(gain),
            "FrameDurationLimits": (int(exposure_us), int(exposure_us * 2)),
        },
    )
    picam2.configure(config)
    picam2.start()

    # Warm-up lungo per evitare il bug AE
    time.sleep(2.0)

    # Re-imposta per sicurezza
    picam2.set_controls({
        "AeEnable":     False,
        "AwbEnable":    False,
        "ExposureTime": int(exposure_us),
        "AnalogueGain": float(gain),
    })
    time.sleep(1.0)

    # Verifica
    md = picam2.capture_metadata()
    print(f"\n{BOLD}=== CAMERA AVVIATA ==={END}")
    print(f"  Richiesto:  exposure = {exposure_us} us,  gain = {gain}")
    print(f"  Effettivo:  exposure = {md.get('ExposureTime', '?')} us,  "
          f"gain = {md.get('AnalogueGain', '?'):.2f}")

    if abs(md.get('ExposureTime', 0) - exposure_us) > 100 or \
       abs(md.get('AnalogueGain', 0) - gain) > 0.1:
        print(f"\n{RED}{BOLD}ATTENZIONE: i parametri richiesti NON sono stati applicati!{END}")
        print(f"{YELLOW}Probabile bug AE su IMX477. Possibili rimedi:")
        print(f"  - riavvia il Pi e riprova")
        print(f"  - aumenta il warm-up (modifica time.sleep nel codice)")
        print(f"  - verifica che nessun altro processo stia usando la camera{END}\n")
        time.sleep(3)

    return picam2


def extract_green(raw_array, bit_depth=12):
    """
    Estrae il canale verde dal Bayer RGGB.
    Per RAW12 impaccato (SBGGR12_CSI2P), libcamera tipicamente restituisce
    un array uint16 con i 12 bit allineati a destra.
    """
    if raw_array.dtype == np.uint16:
        # 12 bit allineati - i valori sono gia' nel range 0-4095
        img = raw_array & 0x0FFF
    elif raw_array.dtype == np.uint8:
        # RAW8 - range 0-255
        img = raw_array.astype(np.uint16)
        bit_depth = 8
    else:
        img = raw_array

    # Bayer BGGR: B G / G R - prendiamo uno dei due verdi
    # G in posizione (0,1) per BGGR
    if img.ndim == 2:
        green = img[0::2, 1::2]
    else:
        green = img[:, :, 1] if img.shape[2] >= 3 else img[:, :, 0]

    return green, bit_depth


# ============================================================
#  MAIN LOOP
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="Istogramma live in terminale per acquisizione DIC."
    )
    parser.add_argument('--exposure', type=int, default=15000,
                        help='Tempo di esposizione in us (default: 15000 = 15 ms)')
    parser.add_argument('--gain', type=float, default=1.0,
                        help='Gain analogico (default: 1.0 = ISO base)')
    parser.add_argument('--refresh', type=float, default=2.0,
                        help='Refresh in Hz (default: 2)')
    args = parser.parse_args()

    picam2 = setup_camera(args.exposure, args.gain)

    print(f"\n{CYAN}Avvio loop. Premi Ctrl+C per uscire.{END}\n")
    time.sleep(2)

    frame_count = 0
    try:
        while True:
            t0 = time.time()

            req = picam2.capture_request()
            try:
                raw = req.make_array("raw")
                md = req.get_metadata()
            finally:
                req.release()

            green, bit_depth = extract_green(raw)
            m = analyze(green, bit_depth=bit_depth)
            level, banner_msg = judge_overall(m)

            # Pulisci schermo e disegna
            sys.stdout.write(CLEAR)

            # Header
            color = {'OK': GREEN, 'WARN': YELLOW, 'BAD': RED}[level]
            term_w = shutil.get_terminal_size().columns
            banner = f" {banner_msg} ".center(term_w, '=')
            print(f"{BOLD}{color}{banner}{END}")
            print()

            # Stato camera
            real_exp = md.get('ExposureTime', '?')
            real_gain = md.get('AnalogueGain', 0)
            exp_match = ('OK' if abs(int(real_exp) - args.exposure) < 100
                         else 'MISMATCH')
            gain_match = ('OK' if abs(float(real_gain) - args.gain) < 0.1
                          else 'MISMATCH')

            print(f"  {BOLD}Camera:{END}  "
                  f"req exp={args.exposure}us [{exp_match}]  "
                  f"req gain={args.gain} [{gain_match}]  |  "
                  f"real exp={real_exp}us  real gain={float(real_gain):.2f}")

            # Metriche
            print(f"  {BOLD}Frame {frame_count}:{END}  "
                  f"min={m['min']:.0f}  max={m['max']:.0f}  "
                  f"mean={m['mean']:.0f} ({m['mean_pct']:.1f}%)  "
                  f"median={m['median']:.0f}  "
                  f"std={m['std']:.0f}")
            print(f"  {BOLD}DIC:   {END}  "
                  f"sat={m['pct_saturated']:.3f}%  "
                  f"dark={m['pct_dark']:.2f}%  "
                  f"dyn_range={m['dynamic_range_used']:.1f}%  "
                  f"RMS_contrast={m['rms_contrast']:.3f}")
            print()

            # Istogramma ASCII
            rows, axis, labels = ascii_histogram(green, m['max_val'])
            for row in rows:
                print(f"  {CYAN}{row}{END}")
            print(f"  {axis}")
            print(f"  {DIM}{labels}{END}")

            # Suggerimenti specifici
            print()
            tips = []
            if m['mean_pct'] < 40:
                tips.append(f"  {YELLOW}-> aumenta esposizione o illuminazione{END}")
            elif m['mean_pct'] > 70:
                tips.append(f"  {YELLOW}-> riduci esposizione o chiudi diaframma{END}")
            if m['pct_saturated'] > 0.5:
                tips.append(f"  {RED}-> SATURAZIONE: chiudi diaframma SUBITO{END}")
            if m['rms_contrast'] < 0.08:
                tips.append(f"  {YELLOW}-> contrasto basso: verifica speckle pattern{END}")
            if m['pct_dark'] > 10:
                tips.append(f"  {YELLOW}-> troppi pixel neri: aumenta illuminazione{END}")

            if not tips and level == 'OK':
                print(f"  {GREEN}-> esposizione e contrasto ottimali, "
                      f"puoi procedere con l'acquisizione DIC{END}")
            else:
                for tip in tips:
                    print(tip)

            print(f"\n  {DIM}Ctrl+C per uscire.{END}")

            frame_count += 1

            # Pacing
            dt = time.time() - t0
            time.sleep(max(0, 1.0/args.refresh - dt))

    except KeyboardInterrupt:
        print(f"\n\n{CYAN}Uscita richiesta.{END}")
    finally:
        try:
            picam2.stop()
            picam2.close()
        except Exception:
            pass
        print("Camera rilasciata. Bye.")


if __name__ == '__main__':
    main()