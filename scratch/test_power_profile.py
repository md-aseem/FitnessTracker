import sys
import os
sys.path.append(os.getcwd())
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from quantum_thermal_model.preprocess.profiles.power import process_custom_power_profile

# Mock OCV curve
ocv_data = {
    'soc': [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
    'ocv': [3.0, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9, 4.0, 4.2]
}
ocv_df = pd.DataFrame(ocv_data)

# Custom power profile (constant 100W for 1000 seconds)
custom_time = np.array([0, 1000, 2000])
custom_power = np.array([100, 100, 0])

battery_capacity_ah = 50.0
soc_init = 0.8
dt = 1.0

time_s, soc, current, power_watts = process_custom_power_profile(
    custom_time=custom_time,
    custom_power=custom_power,
    ocv_df=ocv_df,
    battery_capacity_ah=battery_capacity_ah,
    soc_init=soc_init,
    dt=dt
)

print(f"SOC[0]: {soc[0]}")
print(f"SOC[1]: {soc[1]}")
print(f"SOC[2]: {soc[2]}")
print(f"Current[0]: {current[0]}")
print(f"Current[1]: {current[1]}")

# Plotting to see the "jumping"
plt.figure(figsize=(10, 6))
plt.subplot(3, 1, 1)
plt.plot(time_s[:10], soc[:10], marker='o')
plt.title('SOC (first 10 steps)')
plt.ylabel('SOC')

plt.subplot(3, 1, 2)
plt.plot(time_s[:10], current[:10], marker='o')
plt.title('Current (first 10 steps)')
plt.ylabel('Current (A)')

plt.subplot(3, 1, 3)
plt.plot(time_s[:10], power_watts[:10], marker='o')
plt.title('Power (first 10 steps)')
plt.ylabel('Power (W)')

plt.tight_layout()
plt.savefig('test_output.png')
print("Plot saved to test_output.png")
