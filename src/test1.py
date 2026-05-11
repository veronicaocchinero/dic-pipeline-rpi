
import numpy as np
import tifffile as tiff

WIDTH = 1520
HEIGHT = 2028

RAW_H = 2032
RAW_W = 4320

path = "output/seq_0027/frame_0000.raw"

data = np.fromfile("output/seq_0027/frame_0000.raw", dtype=np.uint16)

img = data.reshape((RAW_H, RAW_W))

# crop verticale (tolgo padding sotto)
img = img[:HEIGHT, :]

# crop orizzontale (prendo solo immagine utile)
img = img[:, :WIDTH]

# conversione 8-bit
img8 = (img >> 8).astype(np.uint8)

tiff.imwrite("out.tiff", img8)

print("done")