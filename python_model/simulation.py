### This file contains the logic to run the simulation. This is the heart of the model. ###
from python_model.preprocess.builders import load_operation_specs
from python_model.preprocess.properties import SystemSpecs, OperationalSpecs
from python_model.preprocess.builders.system import build_system_specs
import os
import numpy as np
from scipy.interpolate import RegularGridInterpolator
import matplotlib.pyplot as plt
import time
import pandas as pd
from python_model.core import (
    run_physics_engine, BatterySpecs, WallSpecs, ChillerSpecs, 
    SetpointSpecs, ProfileSpecs, ThermalState, ControlState, PowerState, FluxState
)

class Simulation:
    # Control Constants
    OFF = 0
    ON = 1
    
    # Modes
    STANDBY_MODE = 0
    COOL_MODE = 1
    HEAT_MODE = 2
    CIRCULATE_MODE = 3

    def __init__(self, system_specs: SystemSpecs, operational_specs: OperationalSpecs):
        self.system_specs = system_specs
        self.operational_specs = operational_specs
        print(f"Simulation initialized with battery_type: {self.system_specs.battery_specs.battery_type}")

        self.n = self.operational_specs.n
        self.dt = self.operational_specs.dt
        self.time_s = self.operational_specs.time_s.copy()
        self.power_profile = self.operational_specs.power_profile.copy()
        self.soc = self.operational_specs.soc_profile.copy()
        self.current_profile = self.operational_specs.current_profile.copy()
        self.ambient_temp_profile = self.operational_specs.ambient_profile.copy()
        self.radiation_heat_load = self.calculate_radiation_load()

        ### dissecting system specs here for easy access
        self.steel_wall_specs = self.system_specs.steel_wall_specs
        self.insulation_wall_specs = self.system_specs.insulation_wall_specs

        # heat and temperature 2D vectors. First dim is time, Second is space/nodes
        # Initialize with initial ambient temperature
        initial_batt_temp = self.system_specs.battery_specs.initial_temperature
        
        # Internal Air Temp
        # Initialize to initial battery temperature (matching C model behavior)
        self.internal_air_temp = np.ones([self.n], dtype=np.float64) * initial_batt_temp

        # Wall Initialization (Linear Gradient from Internal to Ambient)
        initial_ambient = self.ambient_temp_profile[0]

        # Generate gradient: Start at internal (virtual), end at ambient (Node 6)
        wall_grad = initial_batt_temp + (initial_ambient - initial_batt_temp) / 7.0 * np.arange(7)
        self.steel_walls_temp = np.tile(wall_grad, (self.n, 1))
        self.insulation_walls_temp = np.tile(wall_grad, (self.n, 1))

        # Battery Temp
        self.battery_temp = np.full([self.n, 7], float(initial_batt_temp), dtype=np.float64)

        # SOC
        # self.soc was initialized from profile above

        # Setup Heat Generation Interpolator
        self.heat_gen_interpolator = self.generate_heat_gen_interpolator()
        self.cell_heat_gen_profile = self.calculate_battery_heat_generation()

        # --- Control State Initialization ---
        self.chiller_mode = np.ones([self.n], dtype=np.float64) * self.CIRCULATE_MODE
        self.came_from_standby = np.zeros([self.n], dtype=bool)
        self.circ_run_timer = np.zeros([self.n], dtype=np.float64)
        
        # Component States (Percent 0.0 - 1.0)
        self.compressor_pcnt = np.zeros([self.n], dtype=np.float64)
        self.heater_pcnt = np.zeros([self.n], dtype=np.float64)
        self.fan_pcnt = np.zeros([self.n], dtype=np.float64)
        self.battery_pump_pcnt = np.zeros([self.n], dtype=np.float64)
        self.inverter_pump_pcnt = np.zeros([self.n], dtype=np.float64)
        
        # On/Off States
        self.b_turned_on = np.zeros([self.n], dtype=bool) # Battery loop active?
        self.p_turned_on = np.zeros([self.n], dtype=bool) # PCS loop active?
        self.fans_on_off = np.full([self.n], self.OFF, dtype=np.int32)
        self.compressor_on_off = np.full([self.n], self.OFF, dtype=np.int32)
        
        # Liquid Loop States
        self.chiller_outlet_temp = np.full([self.n], initial_batt_temp) # Start with battery temp
        self.chiller_inlet_temp = np.full([self.n], initial_batt_temp)
        self.refrigerant_temp = np.full([self.n], initial_batt_temp) # Internal variable for chiller
        self.battery_stream_mass_flow = 0.0
        
        # HVAC & Dehumidifier
        self.hvac_air_temp = np.full([self.n], initial_batt_temp) # ACC internal air temp? Or is it same as internal?
        
        self.hvac_cooling_power = np.zeros([self.n])
        self.hvac_aux_power = np.zeros([self.n])
        
        self.dehumidifier_on_time = np.zeros([self.n], dtype=np.float64)
        self.dehumidifier_aux_power = np.zeros([self.n], dtype=np.float64)
        
        # Power Consumption
        self.total_aux_power = np.zeros([self.n])

        # Internal Heat States
        self.heat_into_cold_plate = np.zeros([self.n], dtype=np.float64)
        self.heat_from_walls_to_air = np.zeros([self.n], dtype=np.float64)
        self.heat_from_battery_to_air = np.zeros([self.n], dtype=np.float64)

        # Energy Aggregation
        self.operating_aux_energy = 0.0
        self.resting_aux_energy = 0.0
        self.idling_aux_energy = 0.0
        self.time_spent_operating = 0.0
        self.time_spent_resting = 0.0
        self.time_spent_idling = 0.0

        self.chiller_aux_energy = 0.0
        self.hvac_aux_energy = 0.0
        self.dehumidifier_aux_energy = 0.0
        self.inverter_aux_energy = 0.0
        self.aux_load_energy = 0.0
        
        self.batt_ave_temp_operating = 0.0
        self.batt_ave_temp_not_operating = 0.0
        
        self.idle_rest_cutoff_temp = 23.0 # Matches C-Code equivalents

        # Chiller Curves pre-calculated for speed
        chiller_df = self.system_specs.chiller_specs.chiller_curves_df
        c18_df = chiller_df[chiller_df['temp'] == 18]
        c23_df = chiller_df[chiller_df['temp'] == 23]
        self._chiller_amb_18 = c18_df['ambient_temp_C'].values.astype(np.float64)
        self._chiller_pwr_18 = c18_df['cooling_power_W'].values.astype(np.float64)
        self._chiller_amb_23 = c23_df['ambient_temp_C'].values.astype(np.float64)
        self._chiller_pwr_23 = c23_df['cooling_power_W'].values.astype(np.float64)


    def generate_heat_gen_interpolator(self):
        df = self.system_specs.battery_specs.heat_gen_df
        # heat_gen_df format: cols 1..N are C-rates, col 0 is SOC
        c_rate_cols = df.columns[1:].astype(float).values
        soc_col = df.iloc[:, 0].values
        heat_data = df.iloc[:, 1:].values

        # Initialize interpolator
        # Points must be strictly ascending/descending. Assuming input df follows this.
        return RegularGridInterpolator(
            (soc_col, c_rate_cols),
            heat_data,
            bounds_error=False,
            fill_value=None
        )

    def get_chiller_cooling_power(self, ambient_temp, curve_temp_c):
        """
        Interpolate cooling power from cached chiller curves.
        """
        if curve_temp_c == 18:
            return np.interp(ambient_temp, self._chiller_amb_18, self._chiller_pwr_18)
        else:
            return np.interp(ambient_temp, self._chiller_amb_23, self._chiller_pwr_23)

    def run(self, steps: int = None):
        print(f"Running simulation with Numba...")

        start_time = time.time()
        limit = self.time_s.size if steps is None else min(steps, self.time_s.size)
        
        # Unpack specs
        sys = self.system_specs
        s_wall = sys.steel_wall_specs
        i_wall = sys.insulation_wall_specs
        b_spec = sys.battery_specs
        c_spec = sys.chiller_specs
        sp = sys.setpoints

        print(f"Chiller Coef: {c_spec.cooling_power_coef}")
        steel_inv_cap = self.dt / (s_wall.mass * s_wall.cp / 7.0)
        insul_inv_cap = self.dt / (i_wall.mass * i_wall.cp / 7.0)
        print(f"Mass: {b_spec.mass}, CP: {b_spec.cp}")
        batt_inv_cap = self.dt / (b_spec.mass * b_spec.cp / 7.0)

        # Create Data Structures for Solver
        print(f"Cells: {b_spec.n_cells}, Total Heat Sample: {self.cell_heat_gen_profile[0] * b_spec.n_cells}")
        print(f"Inv Cap: {batt_inv_cap}")
        batt_specs = BatterySpecs(b_spec.R, batt_inv_cap, b_spec.n_cells, b_spec.cell_capacity_ah)
        steel_specs = WallSpecs(s_wall.R, steel_inv_cap)
        insul_specs = WallSpecs(i_wall.R, insul_inv_cap)
        chiller_specs = ChillerSpecs(
            c_spec.circulation_time_limit, c_spec.temp_stable, c_spec.battery_sensitivity, 
            c_spec.pump_aux_cap, c_spec.cooling_power_coef, c_spec.heater_heat, c_spec.bat_volume_flow_rate_lpm
        )
        setpoint_specs = SetpointSpecs(
            sp.b_coolant_target, sp.battery_cool_min, sp.battery_heat_min, 
            sp.battery_heat_target, sp.battery_heat_max, sp.battery_heat_exit, sp.chiller_setpoint
        )
        # Pre-calculate chiller cooling power profiles (Vectorized)
        chiller_pwr_18c_profile = np.interp(
            self.ambient_temp_profile, self._chiller_amb_18, self._chiller_pwr_18
        ) if self._chiller_amb_18.size > 0 else np.zeros_like(self.ambient_temp_profile)
        
        chiller_pwr_23c_profile = np.interp(
            self.ambient_temp_profile, self._chiller_amb_23, self._chiller_pwr_23
        ) if self._chiller_amb_23.size > 0 else np.zeros_like(self.ambient_temp_profile)

        profile_specs = ProfileSpecs(
            self.current_profile, self.ambient_temp_profile, self.cell_heat_gen_profile, self.radiation_heat_load,
            chiller_pwr_18c_profile, chiller_pwr_23c_profile
        )
        thermal_state = ThermalState(
            self.internal_air_temp, self.steel_walls_temp, self.insulation_walls_temp, self.battery_temp,
            self.chiller_outlet_temp, self.chiller_inlet_temp, self.refrigerant_temp, self.hvac_air_temp
        )
        control_state = ControlState(
            self.chiller_mode, self.came_from_standby, self.circ_run_timer,
            self.b_turned_on, self.p_turned_on, self.fans_on_off, self.compressor_on_off, self.dehumidifier_on_time
        )
        power_state = PowerState(
            self.compressor_pcnt, self.heater_pcnt, self.fan_pcnt, self.battery_pump_pcnt, self.inverter_pump_pcnt,
            self.hvac_cooling_power, self.hvac_aux_power, self.dehumidifier_aux_power
        )
        flux_state = FluxState(
            self.heat_into_cold_plate, self.heat_from_walls_to_air, self.heat_from_battery_to_air
        )

        # Call Physics Engine
        run_physics_engine(
            limit, self.dt, sys.hvac_present,
            batt_specs, steel_specs, insul_specs, chiller_specs, setpoint_specs,
            profile_specs, thermal_state, control_state, power_state, flux_state
        )

        # Post-Simulation Metrics
        self.calculate_metrics()
        print(f"Time taken: {time.time() - start_time}")

    def calculate_battery_heat_generation(self):
        # Interpolate 2D: SOC and C-Rate

        c_rate_profile = self.current_profile / self.system_specs.battery_specs.cell_capacity_ah
        soc_profile = self.soc
        cell_heat_gen_profile = self.heat_gen_interpolator((soc_profile, c_rate_profile))

        return cell_heat_gen_profile

    def calculate_radiation_load(self):

        container_wall_area = self.system_specs.container_specs.container_wall_area
        radiation_surface_prcnt = self.system_specs.container_specs.radiation_surface_prcnt

        radiation_surface_area = container_wall_area * radiation_surface_prcnt
        radiation_profile = self.operational_specs.radiation_profile

        radiation_load = radiation_profile * radiation_surface_area

        return radiation_load

    def calculate_metrics(self):
        # Optimized metric calculation using numpy
        
        # 1. Reconstruct component powers (vectorized)
        # Note: self.compressor_pcnt, etc. are full arrays
        comp_power = self.compressor_pcnt * 5000.0
        pump_power = self.battery_pump_pcnt * 500.0
        fan_power = self.fan_pcnt * 1000.0
        elec_power = 100.0 # Constant overhead, but arguably only when system is "active"? 
                           # In tabulate_aux_energy logic it seemed constant.
                           # Let's assume it applies at all steps for now or improve logic if needed.
                           
        heater_power = self.heater_pcnt * self.system_specs.chiller_specs.heater_heat
        
        # PCS Logic
        # if chargeOrDischargeIsHappening { currentAuxPower = 100.0; }
        current_sq = self.current_profile ** 2
        inverter_aux_power = np.where(current_sq > 0.001, 100.0, 0.0)
        
        chiller_current_power = comp_power + pump_power + fan_power + elec_power + heater_power
        
        hvac_current_power = self.hvac_aux_power
        dehumidifier_current_power = self.dehumidifier_aux_power
        aux_load_current_power = np.zeros_like(self.time_s) # Placeholder from original
        
        total_instant_power = chiller_current_power + hvac_current_power + dehumidifier_current_power + \
                              inverter_aux_power + aux_load_current_power
                              
        self.total_aux_power = total_instant_power # Store array
        
        # Accumulate component energies (Total sum)
        # Using Simpson's rule or Trapezoidal would be better for variable steps, but dt is const here.
        # Simple sum * dt matches original logic.
        self.chiller_aux_energy = np.sum(chiller_current_power) * self.dt
        self.hvac_aux_energy = np.sum(hvac_current_power) * self.dt
        self.dehumidifier_aux_energy = np.sum(dehumidifier_current_power) * self.dt
        self.inverter_aux_energy = np.sum(inverter_aux_power) * self.dt
        self.aux_load_energy = np.sum(aux_load_current_power) * self.dt
        
        # Bucketing Logic
        # 1. OPERATING (Current > 0.01A)
        is_operating = np.abs(self.current_profile) > 0.01
        self.operating_aux_energy = np.sum(total_instant_power[is_operating]) * self.dt
        self.time_spent_operating = np.sum(is_operating) * self.dt
        self.batt_ave_temp_operating = np.sum(self.battery_temp[is_operating, 6]) * self.dt
        self.avg_temp_operating = np.mean(self.battery_temp[is_operating, 6]) if np.any(is_operating) else 0.0
        
        # 2. RESTING (All non-operating: Current <= 0.01A)
        is_resting = ~is_operating
        self.resting_aux_energy = np.sum(total_instant_power[is_resting]) * self.dt
        self.time_spent_resting = np.sum(is_resting) * self.dt
        self.avg_temp_resting = np.mean(self.battery_temp[is_resting, 6]) if np.any(is_resting) else 0.0
        
        # 3. IDLING (Resting AND temp < cutoff)
        bat_temp_top = self.battery_temp[:, 6]
        is_idling = is_resting & (bat_temp_top < self.idle_rest_cutoff_temp)
        
        self.idling_aux_energy = np.sum(total_instant_power[is_idling]) * self.dt
        self.time_spent_idling = np.sum(is_idling) * self.dt
        self.avg_temp_idling = np.mean(bat_temp_top[is_idling]) if np.any(is_idling) else 0.0
        
        # Legacy tracking (accumulating for all non-op)
        self.batt_ave_temp_not_operating = np.sum(bat_temp_top[is_resting]) * self.dt
        
        self.peak_aux_power = np.max(total_instant_power)
        self.cumulative_aux_energy_history = np.cumsum(total_instant_power) * self.dt / 3600.0 # Wh


    def plot_results(self):
        time_hours = self.time_s / 3600.0
        
        fig, axs = plt.subplots(6, 1, figsize=(12, 24))
        
        # 1. Temperatures
        axs[0].plot(time_hours, self.battery_temp[:, 6], label='Battery Top Temp')
        axs[0].plot(time_hours, self.battery_temp[:, 0], label='Battery Bottom Temp', linestyle='--')
        axs[0].plot(time_hours, self.ambient_temp_profile, label='Ambient Temp', alpha=0.6)
        axs[0].set_ylabel('Temperature (°C)')
        axs[0].set_title('System Temperatures')
        axs[0].legend(loc='upper left')
        axs[0].grid(True)
        
        # Add Horizontal Reference Lines for Averages
        max_time = time_hours[-1]
        for val, label, color in [
            (self.avg_temp_operating, 'Avg Op', 'tab:red'),
            (self.avg_temp_resting, 'Avg Rest', 'tab:green'),
            (self.avg_temp_idling, 'Avg Idle', 'tab:blue')
        ]:
            if val > 0:
                axs[0].axhline(y=val, color=color, linestyle=':', alpha=0.7)
                axs[0].text(max_time * 1.01, val, f'{label}: {val:.1f}°C', 
                            color=color, va='bottom', fontweight='bold', fontsize=9)
        
        # Expand X limit slightly for labels
        axs[0].set_xlim(right=max_time * 1.12)
        
        # Helper to share X axis for the first 4 plots
        for i in range(1, 4):
            axs[i].sharex(axs[0])
        
        # 2. Electrical (Current & SOC)
        ax2 = axs[1]
        ax2.plot(time_hours, self.current_profile, label='Current (A)', color='blue')
        ax2.set_ylabel('Current (A)', color='blue')
        ax2.grid(True)
        
        ax2_right = ax2.twinx()
        ax2_right.plot(time_hours, self.soc * 100.0, label='SOC (%)', color='green')
        ax2_right.set_ylabel('SOC (%)', color='green')
        axs[1].set_title('Electrical Stats')
        
        # 3. Aux Power
        axs[2].plot(time_hours, self.total_aux_power, label='Total Aux Power', color='red', alpha=0.8)
        axs[2].set_ylabel('Power (W)', color='red')
        axs[2].tick_params(axis='y', labelcolor='red')
        axs[2].set_title('Auxiliary Power Consumption')
        
        ax3_right = axs[2].twinx()
        ax3_right.plot(time_hours, self.cumulative_aux_energy_history, label='Cumulative Aux (Wh)', color='darkred', linestyle='--')
        ax3_right.set_ylabel('Energy (Wh)', color='darkred')
        ax3_right.tick_params(axis='y', labelcolor='darkred')
        
        # Combine legends
        lines, labels = axs[2].get_legend_handles_labels()
        lines2, labels2 = ax3_right.get_legend_handles_labels()
        axs[2].legend(lines + lines2, labels + labels2, loc='upper left')
        axs[2].grid(True)
        
        # 4. Chiller State
        axs[3].plot(time_hours, self.chiller_mode, label='Chiller Mode', drawstyle='steps-post')
        axs[3].set_yticks([0, 1, 2, 3])
        axs[3].set_yticklabels(['Standby', 'Cool', 'Heat', 'Circulate'])
        axs[3].set_ylabel('Mode')
        axs[3].set_xlabel('Time (Hours)')
        axs[3].set_title('Thermal Management State')
        axs[3].grid(True)
        
        plt.tight_layout()
        plt.savefig('results/simulation_results.png')
        print("Plot saved to simulation_results.png")
        # plt.show() # Commented out to prevent blocking in headless env, uncomment to see plot

    def save_results_to_csv(self, filename='results/python_simulation_results.csv'):
        df = pd.DataFrame({
            'time_s': self.time_s,
            'battery_top_temp_c': self.battery_temp[:, 6],
            'battery_bottom_temp_c': self.battery_temp[:, 0],
            'ambient_temp_c': self.ambient_temp_profile,
            'current_a': self.current_profile,
            'soc': self.soc,
            'total_aux_power_w': self.total_aux_power,
            'chiller_mode': self.chiller_mode,
            'came_from_standby': self.came_from_standby,
            'circ_timer': self.circ_run_timer,
            'b_on': self.b_turned_on,
            'fans_on_off': self.fans_on_off,
            'comp_on_off': self.compressor_on_off,
            'dehumid_time': self.dehumidifier_on_time,
            'compressor_pct': self.compressor_pcnt,
            'cell_heat': self.cell_heat_gen_profile,
            'batt_coolant_temp_leaving_chiller': self.chiller_outlet_temp,
            'batt_coolant_temp_entering_chiller': self.chiller_inlet_temp,
            'internal_air_temp_c': self.internal_air_temp,
            'heat_from_walls_to_air_w': self.heat_from_walls_to_air,
            'heat_from_battery_to_air_w': self.heat_from_battery_to_air,
            'radiation_load_w': self.radiation_heat_load,
            'cumulative_aux_energy_wh': self.cumulative_aux_energy_history,
        })
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        df.to_csv(filename, index=False)
        print(f"Results saved to {filename}")

if __name__ == "__main__":
    system_specs = build_system_specs()
    operational_specs = load_operation_specs()
    sim = Simulation(system_specs, operational_specs)
    sim.run()
    sim.save_results_to_csv()
    sim.plot_results()

