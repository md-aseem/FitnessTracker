import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import sys
import os

def compare_case(case_dir):
    python_path = os.path.join(case_dir, "python_simulation_results.csv")
    c_path = os.path.join(case_dir, "transient.out")

    if not os.path.exists(python_path) or not os.path.exists(c_path):
        print(f"Error: Missing results in {case_dir}")
        return

    p_df = pd.read_csv(python_path)
    c_df = pd.read_csv(c_path, sep=r"\s+", engine="python")

    # Align by time
    p_df['time_s_rounded'] = p_df['time_s'].round(2)
    c_df['Time(s)_rounded'] = c_df['Time(s)'].round(2)
    merged = pd.merge(p_df, c_df, left_on='time_s_rounded', right_on='Time(s)_rounded')

    if merged.empty:
        print("Error: No matching time steps found.")
        return

    print(f"\n--- Comparison Summary for {os.path.basename(case_dir)} ---")
    vars = [
        ('SOC', 'soc', 0, 'SOC'),
        ('Bat_temp_6', 'battery_top_temp_c', -273.15, 'Batt Top Temp'),
        ('Bat_temp_0', 'battery_bottom_temp_c', -273.15, 'Batt Bottom Temp'),
        ('Internal_Air_Temp(C)', 'internal_air_temp_c', 0, 'Internal Air Temp'),
        ('Current(A)', 'current_a', 0, 'Current'),
        ('Bat_Coolant_Temp_Leaving_Chiller(C)', 'batt_coolant_temp_leaving_chiller', -273.15, 'Chiller Outlet Temp'),
    ]

    for c_col, p_col, offset, label in vars:
        diff = np.abs((merged[c_col] + offset) - merged[p_col])
        print(f"{label:20}: Max Diff = {diff.max():.6f}, Mean Diff = {diff.mean():.6f}")

    # Plotting
    fig, axs = plt.subplots(7, 1, figsize=(10, 18), sharex=True)
    time_h = merged['time_s'] / 3600.0

    axs[0].plot(time_h, merged['SOC'], label='C')
    axs[0].plot(time_h, merged['soc'], label='P', linestyle='--')
    axs[0].set_ylabel("SOC")
    
    axs[1].plot(time_h, merged['Bat_temp_6']-273.15, label='C')
    axs[1].plot(time_h, merged['battery_top_temp_c'], label='P', linestyle='--')
    axs[1].set_ylabel("Batt Top Temp (C)")

    axs[2].plot(time_h, merged['Internal_Air_Temp(C)'], label='C')
    axs[2].plot(time_h, merged['internal_air_temp_c'], label='P', linestyle='--')
    axs[2].set_ylabel("Air Temp (C)")

    axs[3].plot(time_h, merged['Current(A)'], label='C')
    axs[3].plot(time_h, merged['current_a'], label='P', linestyle='--')
    axs[3].set_ylabel("Current (A)")

    axs[4].plot(time_h, merged['Bat_Coolant_Temp_Leaving_Chiller(C)']-273.15, label='C')
    axs[4].plot(time_h, merged['batt_coolant_temp_leaving_chiller'], label='P', linestyle='--')
    axs[4].set_ylabel("Chiller Outlet (C)")

    # Chiller Mode comparison
    c_mode_map = {0: 'AUTO', 1: 'COOL', 2: 'HEAT', 3: 'CIRC', 4: 'STBY'}
    p_mode_map = {0: 'STBY', 1: 'COOL', 2: 'HEAT', 3: 'CIRC'}
    axs[5].step(time_h, merged['chillerMode'].map(c_mode_map), where='post', label='C')
    axs[5].step(time_h, merged['chiller_mode'].map(p_mode_map), where='post', label='P', linestyle='--')
    axs[5].set_ylabel("Mode")

    axs[6].plot(time_h, merged['Ambient_Temp(C)'], label='C')
    axs[6].plot(time_h, merged['ambient_temp_c'], label='P', linestyle='--')
    axs[6].set_ylabel("Ambient (C)")

    for ax in axs: ax.legend(); ax.grid(True)
    plt.xlabel("Time (hours)")
    plt.tight_layout()
    plot_path = os.path.join(case_dir, "comparison_plot.png")
    plt.savefig(plot_path)
    print(f"Plot saved to {plot_path}")

if __name__ == "__main__":
    case = sys.argv[1] if len(sys.argv) > 1 else "case_1"
    base_path = "/Users/mas985/code/quantum-thermal-model/compare_results"
    compare_case(os.path.join(base_path, case))