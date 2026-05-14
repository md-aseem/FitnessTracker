import numpy as np
import time

N = 345600
arr = np.random.rand(N)
lst = arr.tolist()

start = time.time()
s = 0
for i in range(N):
    s += arr[i]
print(f"NumPy indexing: {time.time() - start:.3f}s")

start = time.time()
s = 0
for i in range(N):
    s += lst[i]
print(f"List indexing: {time.time() - start:.3f}s")

start = time.time()
s = 0
for i in range(N):
    s += arr.item(i)
print(f"NumPy .item(): {time.time() - start:.3f}s")
