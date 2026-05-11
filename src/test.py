import numpy as np

WIDTH = 1520
HEIGHT = 2028

data = np.fromfile("output/seq_0027/frame_0000.raw", dtype=np.uint16)
img = data[:WIDTH*HEIGHT].reshape((HEIGHT, WIDTH))

print(img.min(), img.max())