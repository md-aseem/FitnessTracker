import os
import pandas as pd
import matplotlib.pyplot as plt
from quantum_thermal_model.simulation_annual import SimulationAnnual
from quantum_thermal_model.preprocess.aging import DegradationModel
from quantum_thermal_model.preprocess.loaders import load_input_config
import time

class SimulationMultiYear:
    """
    Orchestrates a sequential multi-year simulation to capture the 
    thermal-degradation feedback loop.
    """
    def __init__(self, n_years=None, n_workers=None):
        self.config = load_input_config()
        self.n_years = n_years if n_years is not None else self.config.n_years
        self.n_workers = n_workers
        
        self.sim_annual = SimulationAnnual(n_workers=self.n_workers)
        self.aging_model = DegradationModel()
        self.location = self.config.location or "Default Location"

    def run(self):
        """Runs the simulation sequentially for N years."""
        start_time = time.time()
        print(f"=== Starting Multi-Year Simulation for {self.location} ({self.n_years} years) ===")
        
        current_soh = self.config.soh_init
        history = []
        
        for year in range(1, self.n_years + 1):
            year_start = time.time()
            print(f"\n--- Year {year} | SOH: {current_soh:.4f} ---")
            
            # 1. Simulate the Year
            year_metrics = self.sim_annual.run(soh=current_soh)
            
            # 2. Record state
            history.append({
                'year': year,
                'soh_start': current_soh,
                **{k: year_metrics[k] for k in ['avg_temp_c', 'max_temp_c', 'max_soc', 'avg_discharge_c', 'total_ah', 'total_aux_energy_kwh']}
            })
            
            # 3. Predict Degradation for next year (8760 hours)
            current_soh = self.aging_model.update_soh(
                initial_soh=current_soh,
                avg_cp_rate=year_metrics['avg_cp_rate'],
                max_temperature=year_metrics['max_temp_c'],
                max_soc=year_metrics['max_soc'],
                time_hours=8760.0
            )
            print(f"Year {year} complete in {time.time() - year_start:.2f}s")
            
        total_time = time.time() - start_time
        print(f"\n=== Simulation Complete | Final SOH: {current_soh:.4f} | Total Time: {total_time:.2f}s ===")
        
        self._generate_summary(history)
        self.sim_annual.shutdown()
        return history

    def _generate_summary(self, history):
        """Saves summary data and generates multi-year trends."""
        df = pd.DataFrame(history)
        os.makedirs('results', exist_ok=True)
        df.to_csv('results/multi_year_summary.csv', index=False)
        
        fig, axs = plt.subplots(4, 1, figsize=(10, 20), sharex=True)
        
        # SOH Trend
        axs[0].plot(df['year'], df['soh_start'], marker='o', color='forestgreen', lw=2)
        axs[0].set_ylabel('State of Health (SOH)')
        axs[0].set_title(f'Multi-Year Battery Degradation ({self.location})')
        axs[0].grid(True, alpha=0.3)
        
        # Temperature Trend
        axs[1].plot(df['year'], df['avg_temp_c'], marker='s', color='darkred', lw=2)
        axs[1].set_ylabel('Avg Battery Temp (°C)')
        axs[1].set_title('Thermal Feedback Trend')
        axs[1].grid(True, alpha=0.3)

        # C-Rate Trend
        axs[2].plot(df['year'], df['avg_discharge_c'], marker='d', color='darkorange', lw=2)
        axs[2].set_ylabel('Avg Discharge C-Rate')
        axs[2].set_title('Operational Stress Evolution (C-Rate Rise)')
        axs[2].grid(True, alpha=0.3)
        
        # Energy Trend
        axs[3].plot(df['year'], df['total_aux_energy_kwh'], marker='^', color='steelblue', lw=2)
        axs[3].set_ylabel('Total Aux Energy (kWh)')
        axs[3].set_xlabel('Year')
        axs[3].set_title('Yearly Auxiliary Energy Consumption')
        axs[3].grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig('results/multi_year_summary.png')
        print(f"Results: results/multi_year_summary.csv & .png")

if __name__ == "__main__":
    SimulationMultiYear().run()
