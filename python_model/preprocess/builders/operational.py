from python_model.preprocess.properties import OperationalSpecs
from python_model.preprocess.loaders import load_input_config, load_library_data
from python_model.preprocess.profiles import generate_power_profile_for_a_day, generate_ambient_temp_profile_for_a_day
from python_model.preprocess.profiles.radiation import generate_radiation_load_for_a_day

def load_operation_specs() -> OperationalSpecs:
    input_config = load_input_config()
    library_data = load_library_data()

    cp_rate = input_config.cp_rate
    n_cycles = input_config.n_cycles
    dt = 0.2

    time_s, power_profile = generate_power_profile_for_a_day(cp_rate=cp_rate,
                                                                 n_cycles=n_cycles,
                                                                 dt=dt
                                                                 )

    ambient_temp_constant = input_config.ambient_temperature + 273.15
    time_s, ambient_profile = generate_ambient_temp_profile_for_a_day(ambient_temp_constant, dt=dt)
    time_s, radiation_profile = generate_radiation_load_for_a_day(dt=dt)

    return OperationalSpecs(time_s=time_s,
                            power_profile=power_profile,
                            ambient_profile=ambient_profile,
                            radiation_profile=radiation_profile)
