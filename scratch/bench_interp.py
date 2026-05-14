import numpy as np
import time

N = 345600
ambient = np.random.uniform(10, 40, N)
xp = np.array([10, 20, 30, 40])
yp = np.array([1000, 2000, 3000, 4000])

start = time.time()
for i in range(N):
    v = np.interp(ambient[i], xp, yp)
print(f"np.interp in loop: {time.time() - start:.3f}s")

start = time.time()
profile = np.interp(ambient, xp, yp)
for i in range(N):
    v = profile[i]
print(f"Pre-interp array lookup: {time.time() - start:.3f}s")
