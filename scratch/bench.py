import numpy as np
import time

N = 345600
arr = np.zeros((N, 7))
arr[0] = np.arange(7)
dt_mass_cp = 0.1
R1 = 0.5

start = time.time()
for i in range(1, N):
    t_prev = arr[i-1]
    flux_left = (t_prev[0:5] - t_prev[1:6]) * R1
    flux_right = (t_prev[2:7] - t_prev[1:6]) * R1
    arr[i, 1:6] = t_prev[1:6] + (flux_left + flux_right) * dt_mass_cp
print(f"NumPy slice time: {time.time() - start:.3f}s")

arr = np.zeros((N, 7))
arr[0] = np.arange(7)
start = time.time()
# pre-extract scalar vars for speed
for i in range(1, N):
    t0, t1, t2, t3, t4, t5, t6 = arr[i-1]
    arr[i, 1] = t1 + ((t0 - t1)*R1 + (t2 - t1)*R1) * dt_mass_cp
    arr[i, 2] = t2 + ((t1 - t2)*R1 + (t3 - t2)*R1) * dt_mass_cp
    arr[i, 3] = t3 + ((t2 - t3)*R1 + (t4 - t3)*R1) * dt_mass_cp
    arr[i, 4] = t4 + ((t3 - t4)*R1 + (t5 - t4)*R1) * dt_mass_cp
    arr[i, 5] = t5 + ((t4 - t5)*R1 + (t6 - t5)*R1) * dt_mass_cp
print(f"Unrolled pure scalar time: {time.time() - start:.3f}s")
