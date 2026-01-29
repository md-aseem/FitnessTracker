from python_model.preprocess.properties import OperationalSpecs
from python_model.preprocess.loaders import load_input_config, load_library_data
from python_model.preprocess.profiles import generate_power_profiles_for_a_day, generate_ambient_temp_profile_for_a_day
from python_model.preprocess.profiles.radiation import generate_radiation_load_for_a_day

def load_operation_specs() -> OperationalSpecs:
    input_config = load_input_config()
    library_data = load_library_data()

    cp_rate = input_config.cp_rate
    n_cycles = input_config.n_cycles
    battery_capacity_ah = library_data['batteries'][input_config.battery_type]['capacity_ah']
    battery_energy = battery_capacity_ah * 3.2 # 3.2 is nominal voltage
    dt = 0.2

    time_s, soc, current, power_watts = generate_power_profiles_for_a_day(cp_rate=cp_rate,
                                                              n_cycles=n_cycles,
                                                              dt=dt,
                                                              total_energy=battery_energy
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