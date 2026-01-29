from python_model.preprocess.properties import OperationalSpecs
from python_model.preprocess.loaders import load_input_config, load_library_data
from python_model.preprocess.profiles import generate_power_profiles_for_a_day, generate_ambient_temp_profile_for_a_day
from python_model.preprocess.profiles.radiation import generate_radiation_load_for_a_day
from python_model.preprocess.builders.battery import build_battery_specs

def load_operation_specs() -> OperationalSpecs:
    input_config = load_input_config()
    library_data = load_library_data()

    # Load Battery Specs to access OCV Curve and other properties
    batt_specs = build_battery_specs(input_config, library_data)

    cp_rate = input_config.cp_rate
    n_cycles = input_config.n_cycles
    
    battery_capacity_ah = batt_specs.cell_capacity_ah
    battery_energy = battery_capacity_ah * 3.2 # 3.2 is nominal voltage (Cell Energy)
    dt = 0.2

    # User requested to always start with charge (StateMachine handles full battery case)
    start_with_charge = True

    time_s, soc, current, power_watts = generate_power_profiles_for_a_day(cp_rate=cp_rate,
                                                              n_cycles=n_cycles,
                                                              total_energy=battery_energy,
                                                              ocv_curve=batt_specs.ocv_df,
                                                              battery_capacity_ah=battery_capacity_ah,
                                                              soc_init=input_config.soc_init,
                                                              dt=dt
                                                              )

    ambient_temp_constant = input_config.ambient_temperature + 273.15
    time_s, ambient_profile = generate_ambient_temp_profile_for_a_day(ambient_temp_constant, dt=dt)
    time_s, radiation_profile = generate_radiation_load_for_a_day(dt=dt)

    return OperationalSpecs(time_s=time_s,
                            soc_profile=soc,
                            current_profile=current,
                            power_profile=power_watts,
                            ambient_profile=ambient_profile,
                            radiation_profile=radiation_profile)

if __name__ == '__main__':
    opec_specs = load_operation_specs()