import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

base_path = "one_cycle_35C"
c_path = os.path.join(base_path, "c_code", 'transient.out')
p_path = os.path.join(base_path, "python", 'python_simulation_results.csv')

# loading
df_c = pd.read_csv(c_path, delim_whitespace=True)
df_p = pd.read_csv(p_path)

# preprocessing
df_c['Time(hr)'] = df_c['Time(s)'] / 3600
df_p['time_hr'] = df_p['time_s'] / 3600

# Chiller Mode Mapping
# C Model: 0=AUTO, 1=COOL, 2=HEAT, 3=CIRCULATE, 4=STANDBY
c_mode_map = {
    0: 'AUTO',
    1: 'COOL',
    2: 'HEAT',
    3: 'CIRCULATE',
    4: 'STANDBY'
}
df_c['chillerMode'] = df_c['chillerMode'].map(c_mode_map)

# Python Model: 0=STANDBY, 1=COOL, 2=HEAT, 3=CIRCULATE
p_mode_map = {
    0: 'STANDBY',
    1: 'COOL',
    2: 'HEAT',
    3: 'CIRCULATE'
}
df_p['chiller_mode'] = df_p['chiller_mode'].map(p_mode_map)

fig, axs = plt.subplots(5, 1, sharex=True, figsize=(5, 10))

axs[0].plot(df_c['Time(hr)'], df_c['SOC'], label='c')
axs[0].plot(df_p['time_hr'], df_p['soc'], label='p')
axs[0].legend()
axs[0].set_ylabel("SOC")

axs[1].plot(df_c['Time(hr)'], df_c['Current(A)'], label='C')
axs[1].plot(df_p['time_hr'], df_p['current_a'], label='P')
axs[1].legend()
axs[1].set_ylabel("Current (A)")

axs[2].plot(df_c['Time(hr)'], df_c['Bat_temp_6'] - 273.16, label="Battery Max - C")
axs[2].plot(df_p['time_hr'], df_p['battery_top_temp_c'], label="Battery Max - Python")
axs[2].legend()
axs[2].set_ylabel("Temperature (C)")

axs[3].plot(df_c['Time(hr)'], df_c['compressorSetPcnt'], label='C')
axs[3].plot(df_p['time_hr'], df_p['compressor_pct'], label='p')
axs[3].legend()
axs[3].set_ylabel("Compressor Percentage")

axs[4].plot(df_c['Time(hr)'], df_c['chillerMode'])
axs[4].plot(df_p['time_hr'], df_p['chiller_mode'])
axs[4].set_ylabel("Chiller Mode")
axs[4].set_xlabel("Time (hr)")

fig.tight_layout()
fig.show()
pass