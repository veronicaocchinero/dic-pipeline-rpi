import numpy as np

WIDTH = 2028
HEIGHT = 1520

data = np.fromfile("output/seq_0021/frame_0001.raw", dtype=np.uint16)
img = data[:WIDTH*HEIGHT].reshape((HEIGHT, WIDTH))

print(img.min(), img.max())