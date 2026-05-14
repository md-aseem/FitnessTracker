
import numpy as np
from quantum_thermal_model.core import (
    ThermalSolver, BatterySpecs, WallSpecs, ChillerSpecs, SetpointSpecs, 
    ProfileSpecs, ThermalState, ControlState, PowerState, FluxState
)

# Constants from core.py (re-defined here for testing)
COOLANT_BASED = 0
BATTERY_BASED = 1

def run_test(strategy):
    dt = 1.0
    hvac_present = False
    
    battery = BatterySpecs(R=np.array([0.01, 0.01, 0.01]), inv_cap=1e-5, n_cells=10, cell_cap_ah=100.0)
    wall = WallSpecs(R=np.array([0.01, 0.01, 0.01]), inv_cap=1e-5)
    chiller = ChillerSpecs(
        circulation_time_limit=300.0, temp_stable=0.5, battery_sensitivity=1.0, 
        pump_aux_cap=1.0, cooling_power_coef=1.0, heater_heat=2000.0, bat_volume_flow_rate_lpm=20.0
    )
    
    # battery_cool_target = 25
    # battery_cool_exit = 22
    setpoints = SetpointSpecs(
        batt_coolant_target=23.0, battery_cool_min=19.5, battery_heat_min=10.0, 
        battery_heat_target=15.0, battery_heat_max=35.0, battery_heat_exit=30.0, 
        chiller_setpoint=19.0, battery_cool_target=25.0, battery_cool_exit=22.0, 
        cooling_strategy=strategy
    )
    
    profiles = ProfileSpecs(
        current=np.zeros(10), ambient=np.full(10, 30.0), heat_gen=np.zeros(10), radiation=np.zeros(10),
        chiller_pwr_18c_profile=np.full(10, 2000.0),
        chiller_pwr_23c_profile=np.full(10, 3000.0)
    )
    
    # Initial state: Battery 24.5 (less than 25), Coolant 24.0 (greater than 23)
    thermal = ThermalState(
        internal_air=np.full(10, 24.0), steel_walls=np.full((10, 7), 24.0), insulation_walls=np.full((10, 7), 24.0),
        battery=np.full((10, 7), 24.5), chiller_outlet=np.full(10, 24.0), chiller_inlet=np.full(10, 24.0),
        refrigerant=np.full(10, 24.0), hvac_air=np.full(10, 24.0)
    )
    
    control = ControlState(
        chiller_mode=np.full(10, 0.0), came_from_standby=np.zeros(10, dtype=bool), circ_run_timer=np.full(10, 400.0),
        b_turned_on=np.zeros(10, dtype=bool), p_turned_on=np.zeros(10, dtype=bool), fans_on_off=np.zeros(10, dtype=np.int32),
        compressor_on_off=np.zeros(10, dtype=np.int32), dehumidifier_on_time=np.zeros(10)
    )
    
    power = PowerState(
        compressor_pcnt=np.zeros(10), heater_pcnt=np.zeros(10), fan_pcnt=np.zeros(10),
        battery_pump_pcnt=np.zeros(10), inverter_pump_pcnt=np.zeros(10),
        hvac_cooling_power=np.zeros(10), hvac_aux_power=np.zeros(10), dehumidifier_aux_power=np.zeros(10)
    )
    
    flux = FluxState(
        heat_into_cold_plate=np.zeros(10),
        heat_from_walls_to_air=np.zeros(10), heat_from_battery_to_air=np.zeros(10)
    )
    
    solver = ThermalSolver(dt, hvac_present, battery, wall, wall, chiller, setpoints, profiles, thermal, control, power, flux)
    
    # Step 1: Check transition to COOL_MODE
    solver.update_control_state(1)
    mode = solver.chiller_mode[1]
    
    strat_name = "COOLANT_BASED" if strategy == COOLANT_BASED else "BATTERY_BASED"
    print(f"Strategy: {strat_name}")
    print(f"Initial: Battery 24.5, Coolant 24.0 (Target Coolant 23.0, Target Battery 25.0)")
    print(f"Mode at Step 1: {'COOL_MODE' if mode == 1 else 'STANDBY/OTHER'}")

    # Now simulate a high battery temp (26.0) for both
    solver.battery_temp[1, :] = 26.0
    solver.chiller_outlet_temp[1] = 22.0 # Coolant is OK (Target 23)
    
    solver.update_control_state(2)
    mode = solver.chiller_mode[2]
    print(f"State 2: Battery 26.0, Coolant 22.0")
    print(f"Mode at Step 2: {'COOL_MODE' if mode == 1 else 'STANDBY/OTHER'}")
    print("-" * 30)

if __name__ == "__main__":
    run_test(COOLANT_BASED)
    run_test(BATTERY_BASED)
