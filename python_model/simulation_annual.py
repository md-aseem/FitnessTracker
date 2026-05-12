import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import time
from functools import partial
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor

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
    def __init__(self, n_workers=None, months=None):
        self.n_workers = n_workers
        self.months = months if months is not None else list(range(1, 13))
        self.config = load_input_config()
        self.library_data = load_library_data()
        self.location = self.config.location if self.config.location else "Default Location"
        self.system_specs = build_system_specs(self.config, self.library_data)
        self._executor = None
        
        # Pre-cache weather data sequentially in the main process to avoid 
        # parallel API hits and race conditions on the cache file.
        self._precache_weather()

    def _precache_weather(self):
        """Sequential weather fetch to populate cache before parallel workers start."""
        if self.location and self.location != "Default Location":
            print(f"Ensuring weather data for {self.location} is cached...")
            for month in self.months:
                # fetch_historical_weather checks cache internally
                fetch_historical_weather(self.location, month)

    @staticmethod
    def _run_month_task(month, soh, input_config, library_data, system_specs):
        """
        Static task function for ProcessPoolExecutor.
        Runs a single day simulation for the 15th of the month.
        """
        # 1. Update specs with specific SOH
        # Note: system_specs is passed in, we just override the battery part for SOH
        battery_specs = build_battery_specs(input_config, library_data, soh=soh)
        system_specs.battery_specs = battery_specs 
        
        # 2. Generate operational profile for the month
        operational_specs = load_operation_specs(
            month_override=month, 
            input_config=input_config, 
            library_data=library_data
        )
        
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
        Executes simulations for the configured months in parallel and aggregates metrics.
        """
        start_run = time.time()
        print(f"Starting simulation for {self.location} ({len(self.months)} months, SOH={soh:.3f})...")
        months = self.months

        if self._executor is None:
            self._executor = ProcessPoolExecutor(max_workers=self.n_workers)
            
        task_func = partial(
            self._run_month_task, 
            soh=soh, 
            input_config=self.config, 
            library_data=self.library_data,
            system_specs=self.system_specs
        )
        results = list(self._executor.map(task_func, months))
            
        results.sort(key=lambda x: x['month'])
        self._generate_outputs(results)
        summary = self._aggregate_year_metrics(results)
        
        total_time = time.time() - start_run
        print(f"Annual simulation complete in {total_time:.2f}s. Avg Temp: {summary['avg_temp_c']:.2f}C, Avg Discharge C-Rate: {summary['avg_discharge_c']:.3f}")
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
        
        # 2. Aux Energy
        ax2.bar(months, [r['total_aux_energy_kwh'] for r in results], color='salmon', alpha=0.8)
        ax2.set_ylabel('Total Aux Energy (kWh)')
        ax2.set_xlabel('Month')
        ax2.set_title(f'Monthly Total Auxiliary Energy Consumption ({self.location})')
        ax2.set_xticks(months)
        ax2.grid(axis='y', linestyle='--', alpha=0.7)
        plt.tight_layout()
        plt.savefig('results/annual_summary_results.png')

    def shutdown(self):
        """Shuts down the persistent process pool."""
        if self._executor:
            self._executor.shutdown()
            self._executor = None

if __name__ == "__main__":
    SimulationAnnual().run()
