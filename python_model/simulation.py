### This file contains the logic to run the simulation. This is the heart of the model. ###
from python_model.preprocess.builders import load_operation_specs
from python_model.preprocess.properties import SystemSpecs, OperationalSpecs
from python_model.preprocess.builders.system import build_system_specs
import os
import numpy as np
from scipy.interpolate import RegularGridInterpolator
from tqdm import tqdm
import matplotlib.pyplot as plt
import time
import pandas as pd

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
        self.internal_air_temp = np.ones([self.n]) * initial_batt_temp

        # Wall Initialization (Linear Gradient from Internal to Ambient)
        initial_ambient = self.ambient_temp_profile[0]

        # Generate gradient: Start at internal (virtual), end at ambient (Node 6)
        wall_grad = np.linspace(initial_batt_temp, initial_ambient, 8)[1:]
        self.steel_walls_temp = np.tile(wall_grad, (self.n, 1))
        self.insulation_walls_temp = np.tile(wall_grad, (self.n, 1))

        # Battery Temp
        self.battery_temp = np.full([self.n, 7], initial_batt_temp)

        # SOC
        # self.soc was initialized from profile above

        # Setup Heat Generation Interpolator
        self.heat_gen_interpolator = self.generate_heat_gen_interpolator()
        self.cell_heat_gen_profile = self.calculate_battery_heat_generation()

        # --- Control State Initialization ---
        self.chiller_mode = self.CIRCULATE_MODE
        self.chiller_mode_history = np.ones([self.n]) * self.chiller_mode
        self.came_from_standby = False
        self.circ_run_timer = 0.0
        
        # Component States (Percent 0.0 - 1.0)
        self.compressor_pcnt = np.zeros([self.n])
        self.heater_pcnt = np.zeros([self.n])
        self.fan_pcnt = np.zeros([self.n])
        self.battery_pump_pcnt = np.zeros([self.n])
        self.inverter_pump_pcnt = np.zeros([self.n])
        
        # On/Off States
        self.b_turned_on = False # Battery loop active?
        self.p_turned_on = False # PCS loop active?
        self.fans_on_off = self.OFF
        self.compressor_on_off = self.OFF
        
        # Liquid Loop States
        self.battery_stream_temp_leaving_chiller = np.full([self.n], initial_batt_temp) # Start with battery temp
        self.battery_stream_temp_entering_chiller = np.full([self.n], initial_batt_temp)
        self.battery_cold_side_temp = initial_batt_temp # Internal variable for chiller
        self.battery_stream_mass_flow = 0.0
        
        # HVAC & Dehumidifier
        self.hvac_air_temp = np.full([self.n], initial_batt_temp) # ACC internal air temp? Or is it same as internal?
        
        self.hvac_cooling_power = np.zeros([self.n])
        self.hvac_aux_power = np.zeros([self.n])
        
        self.dehumidifier_on_time = 0.0
        self.dehumidifier_aux_power = np.zeros([self.n])
        
        # Power Consumption
        self.total_aux_power = np.zeros([self.n])

        # Internal Heat States
        self.heat_into_cold_plate = np.zeros([self.n])

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
        
        self.idle_rest_cutoff_temp = 296.15 # 23 C (Matches C-Code)


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
        Interpolate cooling power from chiller curves.
        curve_temp_c: 18 or 23
        """
        df = self.system_specs.chiller_specs.chiller_curves_df
        if df.empty:
            return 0.0
            
        # Filter by curve temp (18 or 23)
        # The builder creates a column 'temp' with these values
        curve_df = df[df['temp'] == curve_temp_c]
        
        if curve_df.empty:
            return 0.0
            
        # Interpolate
        # Assuming columns are: ambient_temp_C, cooling_power_W, aux_power_W
        return np.interp(ambient_temp, curve_df['ambient_temp_C'], curve_df['cooling_power_W'])

    def run(self, steps: int = None):
        print(f"Running simulation...")

        start_time = time.time()
        # Main time-stepping loop
        limit = self.time_s.size if steps is None else min(steps, self.time_s.size)
        for i in tqdm(range(1, limit)):

            ### Calculating internal air temp and walls temp
            self.calculate_ambient_heat_load_and_internal_air_temp(i)
            
            # Control Logic Updates
            self.update_control_state(i)
            self.chiller_mode_history[i] = self.chiller_mode
            self.update_chiller_condition_and_cool(i)
            self.update_hvac_condition_and_cool(i)
            self.update_dehumidifier_condition_and_dry_out(i)

            self.update_battery_temp(i)
            
            # Post-Step Calculations
            # self.tabulate_aux_energy(i) # Moved to post-simulation
            
        # Post-Simulation Metrics
        self.calculate_metrics()
        print(f"Time taken: {time.time() - start_time}")


    def calculate_ambient_heat_load_and_internal_air_temp(self, i):

        # Steel Wall Update
        heat_flux_to_outer_node_steel = (self.radiation_heat_load[i] +  # heat from radiation
                                    ((self.ambient_temp_profile[i] - self.steel_walls_temp[i-1, 6]) *
                                     self.steel_wall_specs.R[0]) +  # heat from ambient
                                    ((self.steel_walls_temp[i-1, 5] - self.steel_walls_temp[i-1, 6]) *
                                     self.steel_wall_specs.R[1]))  # heat from internal node

        heat_flux_to_inner_node_steel = (((self.internal_air_temp[i - 1] - self.steel_walls_temp[i - 1, 0]) *
                                     self.steel_wall_specs.R[2]) +  # heat from internal air
                                    (self.steel_walls_temp[i - 1, 1] - self.steel_walls_temp[i - 1, 0]) *
                                    self.steel_wall_specs.R[1]  # heat from internal node
                                    )

        # Flux from air to steel wall (positive means heat leaves air)
        flux_from_air_to_steel_wall = (self.internal_air_temp[i - 1] - self.steel_walls_temp[i - 1, 0]) * \
                                      self.steel_wall_specs.R[2]
        flux_to_inner_air_from_walls = -flux_from_air_to_steel_wall  # accumulators for air update

        self.steel_walls_temp[i, 0] = (self.steel_walls_temp[i - 1, 0] + heat_flux_to_inner_node_steel * self.dt /
                                       (self.steel_wall_specs.mass * self.steel_wall_specs.cp / 7))
        self.steel_walls_temp[i, 6] = (self.steel_walls_temp[i - 1, 6] + heat_flux_to_outer_node_steel * self.dt /
                                       (self.steel_wall_specs.mass * self.steel_wall_specs.cp / 7))

        # Vectorized Update for nodes 1-5
        # T[j] = T_prev[j] + ( (T_prev[j-1] - T_prev[j])*R + (T_prev[j+1] - T_prev[j])*R ) * dt / (mass * cp / 7)
        # Flux left: (T_prev[0:5] - T_prev[1:6])
        # Flux right: (T_prev[2:7] - T_prev[1:6])
        t_prev_steel = self.steel_walls_temp[i - 1]
        
        flux_left = (t_prev_steel[0:5] - t_prev_steel[1:6]) * self.steel_wall_specs.R[1]
        flux_right = (t_prev_steel[2:7] - t_prev_steel[1:6]) * self.steel_wall_specs.R[1]
        
        self.steel_walls_temp[i, 1:6] = t_prev_steel[1:6] + (flux_left + flux_right) * self.dt / \
                                        (self.steel_wall_specs.mass * self.steel_wall_specs.cp / 7)

        # Insulation Wall Update
        heat_flux_to_outer_node_insulation = (((self.ambient_temp_profile[i] - self.insulation_walls_temp[i-1, 6]) *
                                          self.insulation_wall_specs.R[0]) +
                                         ((self.insulation_walls_temp[i-1, 5] - self.insulation_walls_temp[i-1, 6]) *
                                          self.insulation_wall_specs.R[1]))

        heat_flux_to_inner_node_insulation = (((self.internal_air_temp[i - 1] - self.insulation_walls_temp[i - 1, 0]) *
                                          self.insulation_wall_specs.R[2]) +
                                         ((self.insulation_walls_temp[i - 1, 1] - self.insulation_walls_temp[
                                             i - 1, 0]) * self.insulation_wall_specs.R[1]))

        # Flux from air to insulation wall
        flux_from_air_to_insulation_wall = (self.internal_air_temp[i - 1] - self.insulation_walls_temp[i - 1, 0]) * \
                                           self.insulation_wall_specs.R[2]
        flux_to_inner_air_from_walls += -flux_from_air_to_insulation_wall

        self.insulation_walls_temp[i, 0] = (
                    self.insulation_walls_temp[i - 1, 0] + heat_flux_to_inner_node_insulation * self.dt /
                    (self.insulation_wall_specs.mass * self.insulation_wall_specs.cp / 7))
        self.insulation_walls_temp[i, 6] = (
                    self.insulation_walls_temp[i - 1, 6] + heat_flux_to_outer_node_insulation * self.dt /
                    (self.insulation_wall_specs.mass * self.insulation_wall_specs.cp / 7))

        # Vectorized Update for nodes 1-5
        t_prev_ins = self.insulation_walls_temp[i - 1]
        
        flux_left = (t_prev_ins[0:5] - t_prev_ins[1:6]) * self.insulation_wall_specs.R[1]
        flux_right = (t_prev_ins[2:7] - t_prev_ins[1:6]) * self.insulation_wall_specs.R[1]
        
        self.insulation_walls_temp[i, 1:6] = t_prev_ins[1:6] + (flux_left + flux_right) * self.dt / \
                                             (self.insulation_wall_specs.mass * self.insulation_wall_specs.cp / 7)

        # Internal Air Temperature Update
        # heatIntoAir = (prevT_internal - b->tempLast[6])*R[2]; (From C)
        # Positive if Air > Battery (Heat flows into Battery)
        # Air Update subtracts this heat.
        
        # Using previous battery temp (node 6 is top)
        # Note: In C code, b->heatIntoAir is calculated in updateBatteryTemperatures (end of loop) using TEMPLAST.
        # Here we are at start of loop (step i). battery_temp[i-1] corresponds to last step.
        b_specs = self.system_specs.battery_specs
        heat_into_air_from_battery = (self.internal_air_temp[i - 1] - self.battery_temp[i - 1, 6]) * b_specs.R[2]

        self.internal_air_temp[i] = self.internal_air_temp[i - 1] + (
                -heat_into_air_from_battery + flux_to_inner_air_from_walls) * self.dt / (20.0 * 1006.0)


    def update_battery_temp(self, i):

        # Calculate Heat Generation
        total_heat_gen = self.cell_heat_gen_profile[i] * self.system_specs.battery_specs.n_cells
        
        # Update Temperatures
        b_specs = self.system_specs.battery_specs
        
        # Connected to Chiller/Coolant state
        # Using values from control logic
        # 480 LPM max * pump percent
        volume_flow_rate_lpm = self.system_specs.chiller_specs['bat_volume_flow_rate_lpm'] * self.battery_pump_pcnt[i]
        
        if volume_flow_rate_lpm < 0.1:
            coolant_mass_flow = 0.001
        else:
            coolant_mass_flow = (volume_flow_rate_lpm / 60000.0) * 1050.0 # kg/s (~8.4 kg/s max)

        coolant_cp = 3400.0 # J/kgK
        
        # Temp leaving chiller (entering cold plate)
        tlc_last = self.battery_stream_temp_leaving_chiller[i-1]
        
        # Max Enthalpy Delta
        # maxEnthalpyDelta = c->batteryStream->massFlowRate*c->batteryStream->coolantCp*(b->tempLast[0] - c->batteryStream->tlcLast);
        max_possible_heat_transfer = coolant_mass_flow * coolant_cp * (self.battery_temp[i-1, 0] - tlc_last)
        
        # Heat Fluxes
        # bottomQ = -0.4*maxEnthalpyDelta + (b->tempLast[1] - b->tempLast[0])*R[1];
        bottom_q = -0.4 * max_possible_heat_transfer + (self.battery_temp[i-1, 1] - self.battery_temp[i-1, 0]) * b_specs.R[1]
        
        # topQ    = (simmain->internalAirTemp - b->tempLast[6])*R[2] + (b->tempLast[5] - b->tempLast[6])*R[1];
        top_q = (self.internal_air_temp[i] - self.battery_temp[i-1, 6]) * b_specs.R[2] + \
                (self.battery_temp[i-1, 5] - self.battery_temp[i-1, 6]) * b_specs.R[1]
                
        # Heat into Chiller (for next step calculation of chiller return temp)
        # b->heatIntoColdPlate = -0.4*maxEnthalpyDelta;
        heat_into_cold_plate = -0.4 * max_possible_heat_transfer
        self.heat_into_cold_plate[i] = heat_into_cold_plate
        
        # Calculate Temp Entering Chiller (for next step control logic)
        # c->batteryStream->tempEnteringChiller = c->batteryStream->tlcLast - b->heatIntoColdPlate/(c->batteryStream->massFlowRate*c->batteryStream->coolantCp);
        if coolant_mass_flow > 0.001:
            self.battery_stream_temp_entering_chiller[i] = tlc_last - heat_into_cold_plate / (coolant_mass_flow * coolant_cp)
        else:
            self.battery_stream_temp_entering_chiller[i] = tlc_last

        # Node 0 (Bottom)
        # b->temperature[0] += (bottomQ + (ONE/7.0)*batteryTotalHeatGeneration(simmain))*transientDt/(b->mass * b->cp / 7.0);
        self.battery_temp[i, 0] = self.battery_temp[i-1, 0] + \
                                  (bottom_q + (1.0/7.0) * total_heat_gen) * self.dt / \
                                  (b_specs.mass * b_specs.cp / 7.0)

        # Node 6 (Top)
        # b->temperature[6] += (topQ    + (ONE/7.0)*batteryTotalHeatGeneration(simmain) +  batteryTabHeat)*transientDt/(b->mass * b->cp / 7.0);
        
        # Tab heat implementation matching C code macro:
        # heat = 2.5 * 104.0 * 48.0 * (current / 150.0)
        # C code: ((currentCurrent > 0.0) ? (2.5*104.0*48.0*(currentCurrent/150.0)) : (-2.5*104.0*48.0*(currentCurrent/150.0)))
        # This simplifies to: 2.5 * 104.0 * 48.0 * abs(current) / 150.0
        current_amps = self.current_profile[i]
        battery_tab_heat = 2.5 * 104.0 * 48.0 * abs(current_amps) / 150.0

        self.battery_temp[i, 6] = self.battery_temp[i-1, 6] + \
                                  (top_q + (1.0/7.0) * total_heat_gen + battery_tab_heat) * self.dt / \
                                  (b_specs.mass * b_specs.cp / 7.0)

        # Middle Nodes (1-5) Vectorized
        t_prev_batt = self.battery_temp[i-1]
        
        flux_left = (t_prev_batt[0:5] - t_prev_batt[1:6]) * b_specs.R[1]
        flux_right = (t_prev_batt[2:7] - t_prev_batt[1:6]) * b_specs.R[1]
        
        self.battery_temp[i, 1:6] = t_prev_batt[1:6] + \
                                    ((1.0/7.0 * total_heat_gen) + flux_left + flux_right) * \
                                    self.dt / (b_specs.mass * b_specs.cp / 7.0)



    def get_ocv(self, soc):
        ocv_df = self.system_specs.battery_specs.ocv_df
        # Assuming index 0 is SOC and index 1 is Voltage
        return np.interp(soc, ocv_df.iloc[:, 0], ocv_df.iloc[:, 1])

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

    # --- Control Logic Methods ---

    def _check_circulate_mode_timer(self, i):
        """Equivalent to C's setPumpCirculation().
        Returns True if timer is still active (caller should return early).
        """
        if self.circ_run_timer < self.system_specs.chiller_specs['circulation_time_limit']:
            self.circ_run_timer += self.dt
            self.battery_pump_pcnt[i] = 0.40
            return True  # Early exit signal
        return False

    def update_control_state(self, i):
        if self._check_circulate_mode_timer(i):
            return

        bat_min_temp = np.min(self.battery_temp[i-1])
        bat_max_temp = np.max(self.battery_temp[i-1])
        # C uses tlcLast (temp Leaving chiller from prev step) for cooling entry/exit triggers
        tlc_last = self.battery_stream_temp_leaving_chiller[i-1]
        
        # Cooling Triggers
        if tlc_last > self.system_specs.chiller_specs['b_coolant_target']:
            print(f"Entering cooling mode at {time[i]} because tlc>b_coolant_target")
            # if last mode was standby, we set came_from_standby and circulation timer
            if self.chiller_mode == self.STANDBY_MODE:
                self.came_from_standby = True
                self.circ_run_timer = 0.0
            self.chiller_mode = self.COOL_MODE

        # cooling execution
        if self.chiller_mode == self.COOL_MODE:
            self.cooling_mode(i)

            # Check exit conditions
            # Only leave cooling mode if chiller_inlet_temp is 3 less than the coolant_target
            tec_last = self.battery_stream_temp_entering_chiller[i - 1]
            if tec_last < (self.system_specs.chiller_specs['b_coolant_target'] - 3.0):
                self.set_standby_or_circulate_mode(i)
            
        # Heating Triggers
        if bat_max_temp < self.system_specs.chiller_specs['battery_heat_min'] or \
           bat_min_temp < self.system_specs.chiller_specs['battery_heat_target']:
             self.chiller_mode = self.HEAT_MODE

        # heating execution
        if self.chiller_mode == self.HEAT_MODE:
            self.heating_mode(i)

            # Leave Heating Mode Check
            if bat_max_temp > self.system_specs.chiller_specs['battery_heat_max'] or \
                    bat_min_temp > self.system_specs.chiller_specs['battery_heat_exit']:
                self.set_standby_or_circulate_mode(i)

        # Circulation Mode
        if self.chiller_mode == self.CIRCULATE_MODE:
            self.circulate_mode(i)
            
        # Standby Mode
        if self.chiller_mode == self.STANDBY_MODE:
            self.standby_mode(i)

    def cooling_mode(self, i):
        if self._check_circulate_mode_timer(i):
            return

        # Determine Demand
        # Control Scheme 2: Envicool Base Control Scheme
        # bDemand = (b->temperature[6] - (BATTERY_COOL_MIN + ONE)) / bSensitivity;
        sensitivity = self.system_specs.chiller_specs.battery_sensitivity
        pump_aux_cap = self.system_specs.chiller_specs.pump_aux_cap
        cooling_power_coef = self.system_specs.chiller_specs.cooling_power_coef

        # Check top node temp (index 6)
        b_temp_top = self.battery_temp[i-1, 6]
        b_demand = (b_temp_top - (self.system_specs.chiller_specs['battery_cool_min'] + 1.0)) / sensitivity
        
        # Compressor Control
        if b_demand >= 0.30 and not self.b_turned_on:
             self.compressor_pcnt[i] = np.clip(b_demand, 0.30, 1.0) * cooling_power_coef
             self.compressor_on_off = self.ON
             self.battery_pump_pcnt[i] = pump_aux_cap
             self.b_turned_on = True
             
        elif b_demand >= 0.01 and self.b_turned_on:
             self.compressor_pcnt[i] = np.clip(b_demand, 0.30, 1.0) * cooling_power_coef
             self.compressor_on_off = self.ON
             self.battery_pump_pcnt[i] = pump_aux_cap
             
        elif b_demand < 0.01 and self.b_turned_on:
             self.compressor_pcnt[i] = 0.0
             self.compressor_on_off = self.OFF
             self.battery_pump_pcnt[i] = 0.01
             self.b_turned_on = False
             
        else:
             self.compressor_pcnt[i] = 0.0
             self.compressor_on_off = self.OFF
             self.battery_pump_pcnt[i] = 0.01

        # Fans
        if self.b_turned_on:
            self.fan_pcnt[i] = 0.80
            self.fans_on_off = self.ON
        else:
            self.fan_pcnt[i] = 0.0
            self.fans_on_off = self.OFF


    def heating_mode(self, i):
        self.heater_pcnt[i] = 0.80

    def circulate_mode(self, i):
        self.compressor_pcnt[i] = 0.0
        self.compressor_on_off = self.OFF
        self.battery_pump_pcnt[i] = 0.40
        self.b_turned_on = False
        self.fan_pcnt[i] = 0.0

        self.set_standby_or_circulate_mode(i)

    def standby_mode(self, i):
        self.compressor_pcnt[i] = 0.0
        self.compressor_on_off = self.OFF
        self.battery_pump_pcnt[i] = 0.01
        self.b_turned_on = False
        self.fan_pcnt[i] = 0.0
        
        self.set_standby_or_circulate_mode(i)

    def set_standby_or_circulate_mode(self, i):
        # C macros: BATTERY_MAX_TEMP = b->temperature[6], BATTERY_MIN_TEMP = b->temperature[6]
        # So abs(MAX - MIN) = 0, which is always < TEMP_STBL (3.0)
        # => standbyOrCirculate always goes to STANDBY_MODE in the C model
        bat_max_temp = self.battery_temp[i-1, 6]
        bat_min_temp = self.battery_temp[i-1, 0]  # Same node as max — always 0 diff
        
        if abs(bat_max_temp - bat_min_temp) > self.system_specs.chiller_specs['temp_stable']:
             self.chiller_mode = self.CIRCULATE_MODE
             self.circ_run_timer = 0.0
        else:
             self.circ_run_timer = self.system_specs.chiller_specs['circulation_time_limit'] + 1.0  # Expire timer
             self.chiller_mode = self.STANDBY_MODE

    def update_chiller_condition_and_cool(self, i):
        c_specs = self.system_specs.chiller_specs

        # Constants
        C_COEFF = 1.0

        if self.compressor_on_off == self.ON:
            ambient = self.ambient_temp_profile[i] - 273.15  # Convert K -> °C for chiller curve lookup
            
            c18 = C_COEFF * self.get_chiller_cooling_power(ambient, 18)
            c23 = C_COEFF * self.get_chiller_cooling_power(ambient, 23)
            
            # Heat into cold plate from previous step (negative value usually)
            hicp_last = self.heat_into_cold_plate[i-1]
            
            # Logic from C:
            # if(-b->hicpLast <= (C_COEFF*tableInterpolateCooling(ambientT,c->cooling18))) 
            #    c->batteryColdSideTemp += (BASE_COLD_SIDE_TEMPERATURE - c->batteryColdSideTemp)*transientDt/(1.0*910.0);
            # this logic only works if the chiller_setpoint is 19C. we are setting it 19C and keeping the logic same for validation
            if -hicp_last <= c18:
                 target = self.system_specs.chiller_specs['chiller_setpoint'] + 273.15
                 self.battery_cold_side_temp += (target - self.battery_cold_side_temp) * self.dt / (1.0 * 910.0)
            else:
                 # c->batteryColdSideTemp += ((BASE_COLD_SIDE_TEMPERATURE + (-b->hicpLast - c18)*5.0/(c23-c18)) - c->batteryColdSideTemp)*transientDt/(1.0*910.0);
                 if abs(c23 - c18) < 1e-6: # Avoid div by zero
                     denom = 1.0
                 else:
                     denom = c23 - c18
                     
                 target = self.system_specs.chiller_specs['chiller_setpoint'] + 273.15 + (-hicp_last - c18) * 5.0 / denom
                 self.battery_cold_side_temp += (target - self.battery_cold_side_temp) * self.dt / (1.0 * 910.0)
                 
        else:
            # If off, set to temp entering chiller (from C: c->batteryColdSideTemp = c->batteryStream->tempEnteringChiller;)
            # Or simplified drift? The C code explicitly sets it to entering temp when off.
            self.battery_cold_side_temp = self.battery_stream_temp_entering_chiller[i-1]
            
        # 2. Battery Coolant Stream Calculation
        # maxEnthalpyDelta = m * cp * (T_cold_side - T_entering_last)
        # T_leaving = T_entering_last + (Heater + Sharing + 0.7 * maxEnthalpyDelta) / (m * cp)
        
        tec_last = self.battery_stream_temp_entering_chiller[i-1]
        
        self.battery_stream_mass_flow = self.calculate_battery_stream_mass_flow_rate(i)

        coolant_cp = 3400.0 # J/kgK
        
        max_enthalpy_delta = self.battery_stream_mass_flow * coolant_cp * (self.battery_cold_side_temp - tec_last)
        
        heater_heat = self.heater_pcnt[i] * self.system_specs.chiller_specs['heater_heat']
        
        self.battery_stream_temp_leaving_chiller[i] = tec_last + \
            (heater_heat + 0.7 * max_enthalpy_delta) / (self.battery_stream_mass_flow * coolant_cp)


    def calculate_battery_stream_mass_flow_rate(self, i):
        # Clip pump percentage at 0.01 to match C model's floor speed
        pump_pcnt = np.clip(self.battery_pump_pcnt[i], 0.01, 1.0)

        volume_flow_rate_lpm = self.BAT_VOLUME_FLOW_RATE_LPM * pump_pcnt
        battery_stream_mass_flow = (volume_flow_rate_lpm / 60000.0) * 1050.0 # kg/s (~8.4 kg/s max)

        return battery_stream_mass_flow

    def update_hvac_condition_and_cool(self, i):
        # Update hvac_air_temp
        # h->airTemp += (((simmain->ambientTemperature - h->airTemp)*10.0 + componentHeatLoad)/(30.0*1500.0))*transientDt;
        
        if not self.system_specs.hvac_present:
            self.hvac_air_temp[i] = self.hvac_air_temp[i-1]
            self.hvac_aux_power[i] = 0.0
            self.hvac_cooling_power[i] = 0.0
            return

        h_air_temp = self.hvac_air_temp[i-1]
        ambient = self.ambient_temp_profile[i]
        
        # Component Heat Load (from current)
        # if(simmain->current >  0.1)  componentHeatLoad = 5000.0*(simmain->current/150.0);
        current = self.current_profile[i]
        component_heat_load = 0.0
        if current > 0.1:
            component_heat_load = 5000.0 * (current / 150.0)
        elif current < -0.1:
            component_heat_load = 5000.0 * (-current / 150.0)
            
        h_air_temp += (((ambient - h_air_temp) * 10.0 + component_heat_load) / (30.0 * 1500.0)) * self.dt
        
        # Hvac targets
        acc_target = 303.15 # 30C
        hysteresis = 2.0
        
        cooling_power = 0.0
        aux_power = 0.0
        
        if h_air_temp > (acc_target + hysteresis):
            aux_power = 1600.0
            cooling_power = 4000.0
        elif h_air_temp < acc_target:
            aux_power = 0.0
            cooling_power = 0.0
        else:
            # Maintain previous state? Simplified to OFF for now if dropped below target in check above
            pass
            
        h_air_temp -= (cooling_power / (40.0 * 1500.0)) * self.dt
        
        self.hvac_air_temp[i] = h_air_temp
        self.hvac_aux_power[i] = aux_power
        self.hvac_cooling_power[i] = cooling_power


    def update_dehumidifier_condition_and_dry_out(self, i):
        # void updateDehumidifierConditionAndDryOut(struct SimMain *simmain)
        # if((c->fansOnOff == OFF) && (d->cumulativeDehumidifierOnTime < 2.0*CONVERT_HOURS_TO_SECONDS))
        
        if self.fans_on_off == self.OFF and self.dehumidifier_on_time < (2.0 * 3600.0):
             self.dehumidifier_aux_power[i] = 500.0
             self.dehumidifier_on_time += self.dt
        else:
             self.dehumidifier_aux_power[i] = 0.0

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
                           
        heater_power = self.heater_pcnt * 6000.0
        
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
        # 1. OPERATING
        is_operating = current_sq > 0.001
        self.operating_aux_energy = np.sum(total_instant_power[is_operating]) * self.dt
        self.time_spent_operating = np.sum(is_operating) * self.dt
        # Note: batt_ave_temp logic was accumulating self.dt * temp. 
        # So average = sum(temp * dt) / total_time? Or just sum(temp * dt)?
        # Original: self.batt_ave_temp_operating += bat_temp_top * self.dt
        # So it is the time-integral of temperature.
        self.batt_ave_temp_operating = np.sum(self.battery_temp[is_operating, 6]) * self.dt
        
        # 2. RESTING (Not operating AND temp > cutoff)
        bat_temp_top = self.battery_temp[:, 6]
        is_resting = (~is_operating) & (bat_temp_top > self.idle_rest_cutoff_temp)
        
        self.resting_aux_energy = np.sum(total_instant_power[is_resting]) * self.dt
        self.time_spent_resting = np.sum(is_resting) * self.dt
        self.batt_ave_temp_not_operating += np.sum(bat_temp_top[is_resting]) * self.dt
        
        # 3. IDLING (Not operating AND temp <= cutoff)
        is_idling = (~is_operating) & (~is_resting) # Remaining
        
        self.idling_aux_energy = np.sum(total_instant_power[is_idling]) * self.dt
        self.time_spent_idling = np.sum(is_idling) * self.dt
        self.batt_ave_temp_not_operating += np.sum(bat_temp_top[is_idling]) * self.dt
        self.peak_aux_power = np.max(total_instant_power)


    def plot_results(self):
        time_hours = self.time_s / 3600.0
        
        fig, axs = plt.subplots(4, 1, figsize=(12, 16), sharex=True)
        
        # 1. Temperatures
        axs[0].plot(time_hours, self.battery_temp[:, 6] - 273.15, label='Battery Top Temp')
        axs[0].plot(time_hours, self.battery_temp[:, 0] - 273.15, label='Battery Bottom Temp', linestyle='--')
        axs[0].plot(time_hours, self.ambient_temp_profile - 273.15, label='Ambient Temp', alpha=0.6)
        axs[0].set_ylabel('Temperature (°C)')
        axs[0].set_title('System Temperatures')
        axs[0].legend()
        axs[0].grid(True)
        
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
        axs[2].plot(time_hours, self.total_aux_power, label='Total Aux Power', color='red')
        axs[2].set_ylabel('Power (W)')
        axs[2].set_title('Auxiliary Power Consumption')
        axs[2].legend()
        axs[2].grid(True)
        
        # 4. Chiller State
        axs[3].plot(time_hours, self.chiller_mode_history, label='Chiller Mode', drawstyle='steps-post')
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
            'battery_top_temp_c': self.battery_temp[:, 6] - 273.15,
            'battery_bottom_temp_c': self.battery_temp[:, 0] - 273.15,
            'ambient_temp_c': self.ambient_temp_profile - 273.15,
            'current_a': self.current_profile,
            'soc': self.soc,
            'total_aux_power_w': self.total_aux_power,
            'chiller_mode': self.chiller_mode_history,
            'compressor_pct': self.compressor_pcnt,
            'cell_heat': self.cell_heat_gen_profile,
            'batt_coolant_temp_leaving_chiller': self.battery_stream_temp_leaving_chiller,
            'batt_coolant_temp_entering_chiller': self.battery_stream_temp_entering_chiller,
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

