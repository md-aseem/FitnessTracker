import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import time
from functools import partial
from concurrent.futures import ProcessPoolExecutor

from python_model.simulation import Simulation
from python_model.preprocess.builders.system import build_system_specs
from python_model.preprocess.builders.operational import load_operation_specs
from python_model.preprocess.builders.battery import build_battery_specs
from python_model.preprocess.loaders import load_input_config, load_library_data
from python_model.preprocess.profiles.weather import fetch_historical_weather

class SimulationAnnual:
    """
    Handles parallel execution of monthly thermal simulations and generates annual reports.
    Supports SOH overrides for multi-year simulations.
    """
    def __init__(self, n_workers=None):
        self.n_workers = n_workers
        self.config = load_input_config()
        self.location = self.config.location if self.config.location else "Default Location"
        
        # Pre-cache weather data sequentially in the main process to avoid 
        # parallel API hits and race conditions on the cache file.
        self._precache_weather()

    def _precache_weather(self):
        """Sequential weather fetch to populate cache before parallel workers start."""
        if self.location and self.location != "Default Location":
            print(f"Ensuring weather data for {self.location} is cached...")
            for month in range(1, 13):
                # fetch_historical_weather checks cache internally
                fetch_historical_weather(self.location, month)

    @staticmethod
    def _run_month_task(month, soh=1.0):
        """
        Static task function for ProcessPoolExecutor.
        Runs a single day simulation for the 15th of the month.
        """
        input_config = load_input_config()
        library_data = load_library_data()
        
        # 1. Build specs with specific SOH
        battery_specs = build_battery_specs(input_config, library_data, soh=soh)
        system_specs = build_system_specs()
        system_specs.battery_specs = battery_specs 
        
        # 2. Generate operational profile for the month
        # This will now hit the cache populated by the main process
        operational_specs = load_operation_specs(month_override=month)
        
        # 3. Execute Simulation
        sim = Simulation(system_specs, operational_specs)
        sim.run()
        
        # 4. Extract Daily Metrics
        current = sim.current_profile
        discharge_mask = current < -0.01 
        avg_discharge_c = (np.mean(np.abs(current[discharge_mask])) / battery_specs.cell_capacity_ah 
                          if np.any(discharge_mask) else 0.0)
            
        return {
            'month': month,
            'avg_batt_temp': np.mean(sim.battery_temp[:, 6]),
            'max_batt_temp': np.max(sim.battery_temp[:, 6]),
            'max_soc': np.max(sim.soc),
            'total_aux_energy_kwh': (sim.chiller_aux_energy + sim.hvac_aux_energy + 
                                   sim.dehumidifier_aux_energy + sim.inverter_aux_energy) / (3600 * 1000),
            'peak_aux_power_w': sim.peak_aux_power,
            'ah_throughput': np.sum(np.abs(sim.current_profile)) * sim.dt / 3600.0,
            'avg_discharge_c': avg_discharge_c
        }

    def run(self, soh=1.0):
        """
        Executes simulations for all 12 months in parallel and aggregates yearly metrics.
        """
        print(f"Starting annual simulation for {self.location} (SOH={soh:.3f})...")
        months = list(range(1, 13))
        
        with ProcessPoolExecutor(max_workers=self.n_workers) as executor:
            task_func = partial(self._run_month_task, soh=soh)
            results = list(executor.map(task_func, months))
            
        results.sort(key=lambda x: x['month'])
        self._generate_outputs(results)
        summary = self._aggregate_year_metrics(results)
        
        print(f"Annual simulation complete. Avg Temp: {summary['avg_temp_c']:.2f}C, Avg Discharge C-Rate: {summary['avg_discharge_c']:.3f}")
        return {**summary, 'results': results}

    def _aggregate_year_metrics(self, results):
        DAYS_IN_MONTH = 30.4375
        avg_temp = np.mean([r['avg_batt_temp'] for r in results])
        max_temp = np.mean([r['max_batt_temp'] for r in results])
        max_soc = np.max([r['max_soc'] for r in results])
        avg_discharge_c = np.mean([r['avg_discharge_c'] for r in results])
        total_ah = sum([r['ah_throughput'] * DAYS_IN_MONTH for r in results])
        total_energy = sum([r['total_aux_energy_kwh'] * DAYS_IN_MONTH for r in results])
        avg_cp_rate = total_ah / (306.0 * 8760.0)
        
        return {
            'avg_temp_c': avg_temp, 'max_temp_c': max_temp, 'max_soc': max_soc,
            'avg_cp_rate': avg_cp_rate, 'avg_discharge_c': avg_discharge_c,
            'total_ah': total_ah, 'total_aux_energy_kwh': total_energy
        }

    def _generate_outputs(self, results):
        df = pd.DataFrame(results)
        os.makedirs('results', exist_ok=True)
        df.to_csv('results/annual_summary_results.csv', index=False)
        months = [r['month'] for r in results]
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 10))
        ax1.bar(months, [r['avg_batt_temp'] for r in results], color='skyblue')
        ax1.set_ylabel('Avg Battery Temp (°C)')
        ax1.set_title(f'Monthly Average Battery Temperature ({self.location})')
        ax1.set_xticks(months)
        ax1.grid(axis='y', linestyle='--', alpha=0.7)
        ax2.bar(months, [r['total_aux_energy_kwh'] for r in results], color='salmon')
        ax2.set_ylabel('Total Aux Energy (kWh)')
        ax2.set_xlabel('Month')
        ax2.set_title(f'Monthly Total Auxiliary Energy Consumption ({self.location})')
        ax2.set_xticks(months)
        ax2.grid(axis='y', linestyle='--', alpha=0.7)
        plt.tight_layout()
        plt.savefig('results/annual_summary_results.png')

if __name__ == "__main__":
    SimulationAnnual().run()
