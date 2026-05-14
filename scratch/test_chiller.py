
import numpy as np
from quantum_thermal_model.core import ThermalSolver, BatterySpecs, WallSpecs, ChillerSpecs, SetpointSpecs, ProfileSpecs, ThermalState, ControlState, PowerState, FluxState

def test_case(sp, load_val, p18_val, p23_val, label):
    dt = 1.0
    hvac_present = False
    
    battery = BatterySpecs(R=np.array([0.01, 0.01, 0.01]), inv_cap=1e-5, n_cells=10, cell_cap_ah=100.0)
    wall = WallSpecs(R=np.array([0.01, 0.01, 0.01]), inv_cap=1e-5)
    chiller = ChillerSpecs(
        circulation_time_limit=300.0, temp_stable=0.5, battery_sensitivity=1.0, 
        pump_aux_cap=1.0, cooling_power_coef=1.0, heater_heat=2000.0, bat_volume_flow_rate_lpm=20.0
    )
    
    setpoints = SetpointSpecs(
        batt_coolant_target=25.0, battery_cool_min=20.0, battery_heat_min=10.0, 
        battery_heat_target=15.0, battery_heat_max=35.0, battery_heat_exit=30.0, chiller_setpoint=sp
    )
    
    profiles = ProfileSpecs(
        current=np.zeros(10), ambient=np.full(10, 30.0), heat_gen=np.zeros(10), radiation=np.zeros(10),
        chiller_pwr_18c_profile=np.full(10, p18_val),
        chiller_pwr_23c_profile=np.full(10, p23_val)
    )
    
    thermal = ThermalState(
        internal_air=np.full(10, 25.0), steel_walls=np.full((10, 7), 25.0), insulation_walls=np.full((10, 7), 25.0),
        battery=np.full((10, 7), 25.0), chiller_outlet=np.full(10, sp), chiller_inlet=np.full(10, 25.0),
        refrigerant=np.full(10, sp), hvac_air=np.full(10, 25.0)
    )
    
    control = ControlState(
        chiller_mode=np.full(10, 1.0), came_from_standby=np.zeros(10, dtype=bool), circ_run_timer=np.full(10, 400.0),
        b_turned_on=np.full(10, True), p_turned_on=np.full(10, True), fans_on_off=np.full(10, 1, dtype=np.int32),
        compressor_on_off=np.full(10, 1, dtype=np.int32), dehumidifier_on_time=np.zeros(10)
    )
    
    power = PowerState(
        compressor_pcnt=np.zeros(10), heater_pcnt=np.zeros(10), fan_pcnt=np.zeros(10),
        battery_pump_pcnt=np.full(10, 1.0), inverter_pump_pcnt=np.zeros(10),
        hvac_cooling_power=np.zeros(10), hvac_aux_power=np.zeros(10), dehumidifier_aux_power=np.zeros(10)
    )
    
    flux = FluxState(
        heat_into_cold_plate=np.full(10, -load_val),
        heat_from_walls_to_air=np.zeros(10), heat_from_battery_to_air=np.zeros(10)
    )
    
    solver = ThermalSolver(dt, hvac_present, battery, wall, wall, chiller, setpoints, profiles, thermal, control, power, flux)
    
    # We want to see what 'target' is. refrigerant_temp[1] = sp + (target - sp) * 1/910
    # So (refrigerant_temp[1] - sp) * 910 + sp = target
    solver.update_chiller_condition(1)
    target = (solver.refrigerant_temp[1] - sp) * 910.0 + sp
    
    print(f"--- {label} ---")
    print(f"Setpoint: {sp}, Load: {load_val}, P18: {p18_val}, P23: {p23_val}")
    print(f"Calculated Target: {target:.2f}")
    
def test_chiller_logic():
    # Capacity at 18: 2000, Capacity at 23: 3000
    # Capacity at 20: 2000 + (3000-2000)*(20-18)/5 = 2000 + 1000*0.4 = 2400
    
    test_case(23.0, 2500.0, 2000.0, 3000.0, "SP 23, Load 2500 (Inside)") # Target 23
    test_case(23.0, 3500.0, 2000.0, 3000.0, "SP 23, Load 3500 (Outside)") # Target 18 + (3500-2000)*5/1000 = 18 + 7.5 = 25.5
    test_case(20.0, 2200.0, 2000.0, 3000.0, "SP 20, Load 2200 (Inside)") # Target 20
    test_case(20.0, 2600.0, 2000.0, 3000.0, "SP 20, Load 2600 (Outside)") # Target 18 + (2600-2000)*5/1000 = 18 + 3 = 21.0
    test_case(18.0, 1500.0, 2000.0, 3000.0, "SP 18, Load 1500 (Inside)") # Target 18
    test_case(18.0, 2500.0, 2000.0, 3000.0, "SP 18, Load 2500 (Outside)") # Target 18 + (2500-2000)*5/1000 = 20.5

    
    # Expected: since 2500W < 3000W (capacity at 23C), target should be 23.0
    # Current code: since 2500W > 2000W (capacity at 18C), target will be 23.0 + (2500-2000)*5/1000 = 25.5

if __name__ == "__main__":
    test_chiller_logic()
