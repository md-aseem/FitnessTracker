import pandas as pd
import matplotlib.pyplot as plt
import os

def main():
    # Load data
    baseline = pd.read_csv('results/baseline_results.csv')
    fixed = pd.read_csv('results/fixed_results.csv')
    
    # Convert time to hours
    baseline['time_h'] = baseline['time_s'] / 3600.0
    fixed['time_h'] = fixed['time_s'] / 3600.0
    
    fig, axs = plt.subplots(3, 1, figsize=(10, 15))
    
    # 1. Battery Temperature Comparison
    axs[0].plot(baseline['time_h'], baseline['battery_top_temp_c'], label='Baseline (Incorrect Capacity)', color='blue', alpha=0.7)
    axs[0].plot(fixed['time_h'], fixed['battery_top_temp_c'], label='Fixed (Scaled Capacity)', color='red', alpha=0.7)
    axs[0].set_ylabel('Battery Top Temp (°C)')
    axs[0].set_title('Impact on Battery Temperature (Coef = 0.55)')
    axs[0].legend()
    axs[0].grid(True)
    
    # 2. Total Aux Power Comparison
    axs[1].plot(baseline['time_h'], baseline['total_aux_power_w'], label='Baseline Power', color='blue', alpha=0.5)
    axs[1].plot(fixed['time_h'], fixed['total_aux_power_w'], label='Fixed Power', color='red', alpha=0.5)
    axs[1].set_ylabel('Aux Power (W)')
    axs[1].set_title('Impact on Aux Power Consumption')
    axs[1].legend()
    axs[1].grid(True)
    
    # 3. Cumulative Energy Comparison
    axs[2].plot(baseline['time_h'], baseline['cumulative_aux_energy_wh'], label='Baseline Energy', color='blue')
    axs[2].plot(fixed['time_h'], fixed['cumulative_aux_energy_wh'], label='Fixed Energy', color='red')
    axs[2].set_ylabel('Cumulative Energy (Wh)')
    axs[2].set_xlabel('Time (Hours)')
    axs[2].set_title('Impact on Total Energy Consumption')
    axs[2].legend()
    axs[2].grid(True)
    
    plt.tight_layout()
    plt.savefig('results/comparison_report.png')
    print("Comparison plot saved to results/comparison_report.png")

    # Print summary metrics
    b_energy = baseline['cumulative_aux_energy_wh'].iloc[-1]
    f_energy = fixed['cumulative_aux_energy_wh'].iloc[-1]
    b_max_temp = baseline['battery_top_temp_c'].max()
    f_max_temp = fixed['battery_top_temp_c'].max()
    
    print(f"\nSummary Metrics (Bergstrom /8 variant):")
    print(f"Baseline Max Temp: {b_max_temp:.2f}°C")
    print(f"Fixed Max Temp:    {f_max_temp:.2f}°C")
    print(f"Baseline Energy:   {b_energy:.2f} Wh")
    print(f"Fixed Energy:      {f_energy:.2f} Wh")
    print(f"Energy Difference: {f_energy - b_energy:.2f} Wh ({(f_energy/b_energy - 1)*100:.1f}%)")

if __name__ == "__main__":
    main()
