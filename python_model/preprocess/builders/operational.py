from python_model.preprocess.properties import OperationalSpecs
from python_model.preprocess.loaders import load_input_config, load_library_data
from python_model.preprocess.profiles import generate_current_profile_for_a_day, generate_ambient_temp_profile_for_a_day
from python_model.preprocess.profiles.radiation import generate_radiation_load_for_a_day

def load_operation_specs() -> OperationalSpecs:
    input_config = load_input_config()
    library_data = load_library_data()

    c_rate = input_config.c_rate
    n_cycles = input_config.n_cycles
    capacity_ah = library_data['batteries'][input_config.battery_type]['capacity_ah']
    time_s, current_profile = generate_current_profile_for_a_day(c_rate=c_rate,
                                                                 n_cycles=n_cycles,
                                                                 capacity_ah=capacity_ah,
                                                                 )

    ambient_temp_constant = input_config.ambient_temperature
    time_s, ambient_profile = generate_ambient_temp_profile_for_a_day(ambient_temp_constant)
    time_s, radiation_profile = generate_radiation_load_for_a_day()

    return OperationalSpecs(time_s=time_s,
                            current_profile=current_profile,
                            ambient_profile=ambient_profile,
                            radiation_profile=radiation_profile)
