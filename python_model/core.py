import numpy as np
from numba import float64, int32, boolean, int64, njit
from numba.experimental import jitclass
from collections import namedtuple

# --- Constants for Modes ---
STANDBY_MODE = 0
COOL_MODE = 1
HEAT_MODE = 2
CIRCULATE_MODE = 3
OFF = 0
ON = 1

# --- Physics Specs (NamedTuples) ---
BatterySpecs = namedtuple('BatterySpecs', ['R', 'inv_cap', 'n_cells', 'cell_cap_ah'])
WallSpecs = namedtuple('WallSpecs', ['R', 'inv_cap'])
ChillerSpecs = namedtuple('ChillerSpecs', [
    'circulation_time_limit', 'temp_stable', 'battery_sensitivity', 
    'pump_aux_cap', 'cooling_power_coef', 'heater_heat', 'bat_volume_flow_rate_lpm'
])
SetpointSpecs = namedtuple('SetpointSpecs', [
    'batt_coolant_target', 'battery_cool_min', 'battery_heat_min', 
    'battery_heat_target', 'battery_heat_max', 'battery_heat_exit', 'chiller_setpoint'
])
ProfileSpecs = namedtuple('ProfileSpecs', [
    'current', 'ambient', 'heat_gen', 'radiation', 
    'chiller_pwr_18c_profile', 'chiller_pwr_23c_profile'
])
ThermalState = namedtuple('ThermalState', [
    'internal_air', 'steel_walls', 'insulation_walls', 'battery', 
    'chiller_outlet', 'chiller_inlet', 'refrigerant', 'hvac_air'
])
ControlState = namedtuple('ControlState', [
    'chiller_mode', 'came_from_standby', 'circ_run_timer', 'b_turned_on', 'p_turned_on', 
    'fans_on_off', 'compressor_on_off', 'dehumidifier_on_time'
])
PowerState = namedtuple('PowerState', [
    'compressor_pcnt', 'heater_pcnt', 'fan_pcnt', 'battery_pump_pcnt', 'inverter_pump_pcnt', 
    'hvac_cooling_power', 'hvac_aux_power', 'dehumidifier_aux_power'
])
FluxState = namedtuple('FluxState', [
    'heat_into_cold_plate', 'heat_from_walls_to_air', 'heat_from_battery_to_air'
])

# --- Define the JITClass Spec ---
spec = [
    # Constants
    ('dt', float64),
    ('hvac_present', boolean),
    
    # Battery
    ('batt_R', float64[:]),
    ('batt_inv_cap', float64),
    ('n_cells', float64),
    ('cell_cap_ah', float64),

    # Walls
    ('steel_R', float64[:]),
    ('steel_inv_cap', float64),
    ('insul_R', float64[:]),
    ('insul_inv_cap', float64),

    # Chiller & Control
    ('circulation_time_limit', float64),
    ('temp_stable', float64),
    ('battery_sensitivity', float64),
    ('pump_aux_cap', float64),
    ('cooling_power_coef', float64),
    ('heater_heat', float64),
    ('bat_volume_flow_rate_lpm', float64),
    ('batt_coolant_target', float64),
    ('battery_cool_min', float64),
    ('battery_heat_min', float64),
    ('battery_heat_target', float64),
    ('battery_heat_max', float64),
    ('battery_heat_exit', float64),
    ('chiller_setpoint', float64),

    # Profiles
    ('current_profile', float64[:]),
    ('amb_temp_profile', float64[:]),
    ('cell_heat_gen_profile', float64[:]),
    ('radiation_heat_load', float64[:]),
    ('chiller_pwr_18c_profile', float64[:]),
    ('chiller_pwr_23c_profile', float64[:]),

    # State Arrays
    ('internal_air_temp', float64[:]),
    ('steel_walls_temp', float64[:, :]),
    ('insulation_walls_temp', float64[:, :]),
    ('battery_temp', float64[:, :]),
    ('chiller_mode', float64[:]),
    ('came_from_standby', boolean[:]),
    ('circ_run_timer', float64[:]),
    ('b_turned_on', boolean[:]),
    ('p_turned_on', boolean[:]),
    ('fans_on_off', int32[:]),
    ('compressor_on_off', int32[:]),
    ('dehumidifier_on_time', float64[:]),
    ('compressor_pcnt', float64[:]),
    ('heater_pcnt', float64[:]),
    ('fan_pcnt', float64[:]),
    ('battery_pump_pcnt', float64[:]),
    ('inverter_pump_pcnt', float64[:]),
    ('chiller_outlet_temp', float64[:]),
    ('chiller_inlet_temp', float64[:]),
    ('refrigerant_temp', float64[:]),
    ('hvac_air_temp', float64[:]),
    ('hvac_cooling_power', float64[:]),
    ('hvac_aux_power', float64[:]),
    ('dehumidifier_aux_power', float64[:]),
    ('heat_into_cold_plate', float64[:]),
    ('heat_from_walls_to_air', float64[:]),
    ('heat_from_battery_to_air', float64[:]),
]

@jitclass(spec)
class ThermalSolver:
    def __init__(
        self, dt, hvac_present,
        battery, steel_wall, insul_wall, chiller, setpoints, 
        profiles, thermal, control, power, flux
    ):
        self.dt = dt
        self.hvac_present = hvac_present

        # Unbundle Battery
        self.batt_R = battery.R
        self.batt_inv_cap = battery.inv_cap
        self.n_cells = battery.n_cells
        self.cell_cap_ah = battery.cell_cap_ah

        # Unbundle Walls
        self.steel_R = steel_wall.R
        self.steel_inv_cap = steel_wall.inv_cap
        self.insul_R = insul_wall.R
        self.insul_inv_cap = insul_wall.inv_cap

        # Unbundle Chiller & Setpoints
        self.circulation_time_limit = chiller.circulation_time_limit
        self.temp_stable = chiller.temp_stable
        self.battery_sensitivity = chiller.battery_sensitivity
        self.pump_aux_cap = chiller.pump_aux_cap
        self.cooling_power_coef = chiller.cooling_power_coef
        self.heater_heat = chiller.heater_heat
        self.bat_volume_flow_rate_lpm = chiller.bat_volume_flow_rate_lpm
        
        self.batt_coolant_target = setpoints.batt_coolant_target
        self.battery_cool_min = setpoints.battery_cool_min
        self.battery_heat_min = setpoints.battery_heat_min
        self.battery_heat_target = setpoints.battery_heat_target
        self.battery_heat_max = setpoints.battery_heat_max
        self.battery_heat_exit = setpoints.battery_heat_exit
        self.chiller_setpoint = setpoints.chiller_setpoint

        # Unbundle Profiles
        self.current_profile = profiles.current
        self.amb_temp_profile = profiles.ambient
        self.cell_heat_gen_profile = profiles.heat_gen
        self.radiation_heat_load = profiles.radiation
        self.chiller_pwr_18c_profile = profiles.chiller_pwr_18c_profile
        self.chiller_pwr_23c_profile = profiles.chiller_pwr_23c_profile

        # Unbundle Thermal State
        self.internal_air_temp = thermal.internal_air
        self.steel_walls_temp = thermal.steel_walls
        self.insulation_walls_temp = thermal.insulation_walls
        self.battery_temp = thermal.battery
        self.chiller_outlet_temp = thermal.chiller_outlet
        self.chiller_inlet_temp = thermal.chiller_inlet
        self.refrigerant_temp = thermal.refrigerant
        self.hvac_air_temp = thermal.hvac_air

        # Unbundle Control State
        self.chiller_mode = control.chiller_mode
        self.came_from_standby = control.came_from_standby
        self.circ_run_timer = control.circ_run_timer
        self.b_turned_on = control.b_turned_on
        self.p_turned_on = control.p_turned_on
        self.fans_on_off = control.fans_on_off
        self.compressor_on_off = control.compressor_on_off
        self.dehumidifier_on_time = control.dehumidifier_on_time
        
        # Unbundle Power State
        self.compressor_pcnt = power.compressor_pcnt
        self.heater_pcnt = power.heater_pcnt
        self.fan_pcnt = power.fan_pcnt
        self.battery_pump_pcnt = power.battery_pump_pcnt
        self.inverter_pump_pcnt = power.inverter_pump_pcnt
        self.hvac_cooling_power = power.hvac_cooling_power
        self.hvac_aux_power = power.hvac_aux_power
        self.dehumidifier_aux_power = power.dehumidifier_aux_power

        # Unbundle Flux State
        self.heat_into_cold_plate = flux.heat_into_cold_plate
        self.heat_from_walls_to_air = flux.heat_from_walls_to_air
        self.heat_from_battery_to_air = flux.heat_from_battery_to_air

    def update_ambient_and_air(self, i):
        # Steel Wall Update
        flux_air_to_steel_wall = self._update_wall_temperatures(
            i, self.steel_walls_temp, self.steel_R, self.steel_inv_cap, self.radiation_heat_load[i]
        )
        total_flux_to_air = -flux_air_to_steel_wall

        # Insulation Wall Update
        flux_air_to_insulation_wall = self._update_wall_temperatures(
            i, self.insulation_walls_temp, self.insul_R, self.insul_inv_cap, 0.0
        )
        total_flux_to_air += -flux_air_to_insulation_wall

        # Air Temperature Update
        heat_flux_battery_to_air = (self.internal_air_temp[i-1] - self.battery_temp[i-1, 6]) * self.batt_R[2]
        self.heat_from_walls_to_air[i] = total_flux_to_air
        self.heat_from_battery_to_air[i] = -heat_flux_battery_to_air
        
        self.internal_air_temp[i] = self.internal_air_temp[i-1] + (-heat_flux_battery_to_air + total_flux_to_air) * self.dt / (20.0 * 1006.0)

        # Air Temperature Update
        heat_flux_battery_to_air = (self.internal_air_temp[i-1] - self.battery_temp[i-1, 6]) * self.batt_R[2]
        self.heat_from_walls_to_air[i] = total_flux_to_air
        self.heat_from_battery_to_air[i] = -heat_flux_battery_to_air
        
        self.internal_air_temp[i] = self.internal_air_temp[i-1] + (-heat_flux_battery_to_air + total_flux_to_air) * self.dt / (20.0 * 1006.0)

    def update_control_state(self, i):
        # 1. Load current state from previous step
        current_chiller_mode = self.chiller_mode[i-1]
        circulation_run_timer = self.circ_run_timer[i-1]
        came_from_standby = self.came_from_standby[i-1]
        b_turned_on = self.b_turned_on[i-1]
        fans_status = self.fans_on_off[i-1]
        compressor_status = self.compressor_on_off[i-1]

        # 1. Circulation Timer Check
        if circulation_run_timer < self.circulation_time_limit:
            circulation_run_timer += self.dt
            self.battery_pump_pcnt[i] = 0.40
            self._store_control_state(
                i, current_chiller_mode, circulation_run_timer, came_from_standby, 
                b_turned_on, fans_status, compressor_status
            )
            return

        # 2. Temperature Triggers
        battery_temp_min = np.min(self.battery_temp[i-1])
        battery_temp_max = np.max(self.battery_temp[i-1])
        temp_liquid_coolant_leaving_chiller_prev = self.chiller_outlet_temp[i-1]

        if temp_liquid_coolant_leaving_chiller_prev > self.batt_coolant_target:
            if current_chiller_mode != COOL_MODE:
                if current_chiller_mode == STANDBY_MODE:
                    came_from_standby = True
                    circulation_run_timer = 0.0
            current_chiller_mode = COOL_MODE

        # Cooling Execution
        if current_chiller_mode == COOL_MODE:
            battery_temp_top_node = self.battery_temp[i-1, 6]
            battery_cooling_demand = (battery_temp_top_node - (self.battery_cool_min + 1.0)) / self.battery_sensitivity
            
            if battery_cooling_demand >= 0.30 and not b_turned_on:
                self.compressor_pcnt[i] = min(max(battery_cooling_demand, 0.30), 1.0) * self.cooling_power_coef
                compressor_status, b_turned_on = ON, True
                self.battery_pump_pcnt[i] = self.pump_aux_cap
            elif battery_cooling_demand >= 0.01 and b_turned_on:
                self.compressor_pcnt[i] = min(max(battery_cooling_demand, 0.30), 1.0) * self.cooling_power_coef
                compressor_status = ON
                self.battery_pump_pcnt[i] = self.pump_aux_cap
            elif battery_cooling_demand < 0.01 and b_turned_on:
                self.compressor_pcnt[i], compressor_status = 0.0, OFF
                self.battery_pump_pcnt[i], b_turned_on = 0.01, False
            else:
                self.compressor_pcnt[i], compressor_status = 0.0, OFF
                self.battery_pump_pcnt[i] = 0.01

            self.fan_pcnt[i] = 0.80 if b_turned_on else 0.0
            fans_status = ON if b_turned_on else OFF

            temp_liquid_coolant_entering_chiller_prev = self.chiller_inlet_temp[i-1]
            if temp_liquid_coolant_entering_chiller_prev < (self.batt_coolant_target - 3.0):
                if abs(self.battery_temp[i-1, 6] - self.battery_temp[i-1, 0]) > self.temp_stable:
                    current_chiller_mode, circulation_run_timer = CIRCULATE_MODE, 0.0
                else:
                    current_chiller_mode, circulation_run_timer = STANDBY_MODE, self.circulation_time_limit + 1.0

        # Heating Triggers
        if battery_temp_max < self.battery_heat_min or battery_temp_min < self.battery_heat_target:
            current_chiller_mode = HEAT_MODE

        if current_chiller_mode == HEAT_MODE:
            self.heater_pcnt[i] = 0.80
            if battery_temp_max > self.battery_heat_max or battery_temp_min > self.battery_heat_exit:
                if abs(self.battery_temp[i-1, 6] - self.battery_temp[i-1, 0]) > self.temp_stable:
                    current_chiller_mode, circulation_run_timer = CIRCULATE_MODE, 0.0
                else:
                    current_chiller_mode, circulation_run_timer = STANDBY_MODE, self.circulation_time_limit + 1.0

        # Circulate/Standby Modes
        if current_chiller_mode == CIRCULATE_MODE or current_chiller_mode == STANDBY_MODE:
            self.compressor_pcnt[i], compressor_status = 0.0, OFF
            self.fan_pcnt[i], fans_status, b_turned_on = 0.0, OFF, False
            self.battery_pump_pcnt[i] = 0.40 if current_chiller_mode == CIRCULATE_MODE else 0.01
            
            if abs(self.battery_temp[i-1, 6] - self.battery_temp[i-1, 0]) > self.temp_stable:
                current_chiller_mode, circulation_run_timer = CIRCULATE_MODE, 0.0
            else:
                current_chiller_mode, circulation_run_timer = STANDBY_MODE, self.circulation_time_limit + 1.0

        # Store updated state to history
        self._store_control_state(
            i, current_chiller_mode, circulation_run_timer, came_from_standby, 
            b_turned_on, fans_status, compressor_status
        )

    def update_chiller_condition(self, i):
        if self.compressor_on_off[i] == ON:
            chiller_cooling_power_18c = self.chiller_pwr_18c_profile[i] * self.cooling_power_coef
            chiller_cooling_power_23c = self.chiller_pwr_23c_profile[i] * self.cooling_power_coef
            
            heat_into_cold_plate_prev = self.heat_into_cold_plate[i-1]
            target = self.chiller_setpoint if -heat_into_cold_plate_prev <= chiller_cooling_power_18c else \
                     self.chiller_setpoint + (-heat_into_cold_plate_prev - chiller_cooling_power_18c) * 5.0 / (chiller_cooling_power_23c - chiller_cooling_power_18c + 1e-6)
            self.refrigerant_temp[i] = self.refrigerant_temp[i-1] + (target - self.refrigerant_temp[i-1]) * self.dt / 910.0
        else:
            self.refrigerant_temp[i] = self.chiller_inlet_temp[i-1]

        pump_percentage = min(max(self.battery_pump_pcnt[i], 0.01), 1.0)
        mass_flow_rate = (self.bat_volume_flow_rate_lpm * pump_percentage / 60000.0) * 1050.0

        max_cooling_enthalpy = mass_flow_rate * 3400.0 * (self.refrigerant_temp[i] - self.chiller_inlet_temp[i-1])
        heater_heat_gain = self.heater_pcnt[i] * self.heater_heat
        
        if mass_flow_rate > 1e-5:
            self.chiller_outlet_temp[i] = self.chiller_inlet_temp[i-1] + (heater_heat_gain + 0.7 * max_cooling_enthalpy) / (mass_flow_rate * 3400.0)
        else:
            self.chiller_outlet_temp[i] = self.chiller_inlet_temp[i-1]

    def update_hvac_and_dehumidifier(self, i):
        if not self.hvac_present:
            self.hvac_air_temp[i] = self.hvac_air_temp[i-1]
        else:
            hvac_air_temp_internal = self.hvac_air_temp[i-1]
            compressor_heat_gain = 5000.0 * (abs(self.current_profile[i]) / 150.0)
            cooling_power_draw, auxiliary_power_draw = (4000.0, 1600.0) if hvac_air_temp_internal > 32.0 else (0.0, 0.0)
            
            hvac_air_temp_internal += (((self.amb_temp_profile[i] - hvac_air_temp_internal) * 10.0 + compressor_heat_gain) / 45000.0) * self.dt - (cooling_power_draw / 60000.0) * self.dt
            self.hvac_air_temp[i], self.hvac_cooling_power[i], self.hvac_aux_power[i] = hvac_air_temp_internal, cooling_power_draw, auxiliary_power_draw

        dehumidifier_timer = self.dehumidifier_on_time[i-1]
        if self.fans_on_off[i] == OFF and dehumidifier_timer < 7200.0:
            self.dehumidifier_aux_power[i] = 500.0
            dehumidifier_timer += self.dt
        else:
            self.dehumidifier_aux_power[i] = 0.0
        
        self.dehumidifier_on_time[i] = dehumidifier_timer

    def update_battery_temp(self, i):
        total_heat_generation = self.cell_heat_gen_profile[i] * self.n_cells
        pump_percentage = self.battery_pump_pcnt[i]
        mass_flow_rate = (self.bat_volume_flow_rate_lpm * pump_percentage / 60000.0) * 1050.0 if pump_percentage >= 0.1/self.bat_volume_flow_rate_lpm else 0.001
                
        temp_liquid_coolant_leaving_chiller_prev = self.chiller_outlet_temp[i-1]
        max_heat_transfer_capacity = mass_flow_rate * 3400.0 * (self.battery_temp[i-1, 0] - temp_liquid_coolant_leaving_chiller_prev)
        
        heat_flux_at_bottom = -0.4 * max_heat_transfer_capacity + (self.battery_temp[i-1, 1] - self.battery_temp[i-1, 0]) * self.batt_R[1]
        heat_flux_at_top = (self.internal_air_temp[i] - self.battery_temp[i-1, 6]) * self.batt_R[2] + (self.battery_temp[i-1, 5] - self.battery_temp[i-1, 6]) * self.batt_R[1]
        
        self.heat_into_cold_plate[i] = -0.4 * max_heat_transfer_capacity
        self.chiller_inlet_temp[i] = temp_liquid_coolant_leaving_chiller_prev - self.heat_into_cold_plate[i] / (mass_flow_rate * 3400.0) if mass_flow_rate > 0.001 else temp_liquid_coolant_leaving_chiller_prev
                
        self.battery_temp[i, 0] = self.battery_temp[i-1, 0] + (heat_flux_at_bottom + (1.0/7.0) * total_heat_generation) * self.batt_inv_cap
        
        heat_generated_at_tabs = 2.5 * 104.0 * 48.0 * abs(self.current_profile[i]) / (self.cell_cap_ah * 0.5)
        self.battery_temp[i, 6] = self.battery_temp[i-1, 6] + (heat_flux_at_top + (1.0/7.0) * total_heat_generation + heat_generated_at_tabs) * self.batt_inv_cap
        
        temp_prev_nodes = self.battery_temp[i-1]
        flux_left_nodes = (temp_prev_nodes[0:5] - temp_prev_nodes[1:6]) * self.batt_R[1]
        flux_right_nodes = (temp_prev_nodes[2:7] - temp_prev_nodes[1:6]) * self.batt_R[1]
        self.battery_temp[i, 1:6] = temp_prev_nodes[1:6] + ((1.0/7.0 * total_heat_generation) + flux_left_nodes + flux_right_nodes) * self.batt_inv_cap

    def _update_wall_temperatures(self, i, wall_temp, R, inv_cap, outer_load):
        # Outer Node Update
        heat_flux_outer = (outer_load + 
                          (self.amb_temp_profile[i] - wall_temp[i-1, 6]) * R[0] + 
                          (wall_temp[i-1, 5] - wall_temp[i-1, 6]) * R[1])
        
        # Inner Node Update
        flux_air_to_wall = (self.internal_air_temp[i-1] - wall_temp[i-1, 0]) * R[2]
        heat_flux_inner = (flux_air_to_wall + 
                          (wall_temp[i-1, 1] - wall_temp[i-1, 0]) * R[1])
        
        wall_temp[i, 0] = wall_temp[i-1, 0] + heat_flux_inner * inv_cap
        wall_temp[i, 6] = wall_temp[i-1, 6] + heat_flux_outer * inv_cap
        
        # Intermediate Nodes Update (Nodes 1-5)
        t_prev = wall_temp[i-1]
        flux_left = (t_prev[0:5] - t_prev[1:6]) * R[1]
        flux_right = (t_prev[2:7] - t_prev[1:6]) * R[1]
        wall_temp[i, 1:6] = t_prev[1:6] + (flux_left + flux_right) * inv_cap
        
        return flux_air_to_wall

    def _store_control_state(self, i, mode, timer, from_sb, b_on, fans, comp):
        self.chiller_mode[i] = mode
        self.circ_run_timer[i] = timer
        self.came_from_standby[i] = from_sb
        self.b_turned_on[i] = b_on
        self.fans_on_off[i] = fans
        self.compressor_on_off[i] = comp
        self.p_turned_on[i] = self.p_turned_on[i-1]

# --- Main Entry Point Wrapper ---
@njit(cache=True)
def run_physics_engine(
    limit, dt, hvac_present,
    battery, steel_wall, insul_wall, chiller, setpoints, 
    profiles, thermal, control, power, flux
):
    # 1. Initialize the Solver Object
    solver = ThermalSolver(
        dt, hvac_present,
        battery, steel_wall, insul_wall, chiller, setpoints, 
        profiles, thermal, control, power, flux
    )

    # 2. Run the Loop
    for i in range(1, limit):
        solver.update_ambient_and_air(i)
        solver.update_control_state(i)
        solver.update_chiller_condition(i)
        solver.update_hvac_and_dehumidifier(i)
        solver.update_battery_temp(i)
