import pandas as pd
from pathlib import Path
from python_model.preprocess.properties import OperationalSpecs
from python_model.preprocess.loaders import load_input_config, load_library_data
from python_model.preprocess.profiles import generate_power_profiles_for_a_day, generate_ambient_temp_profile_for_a_day, process_custom_power_profile
from python_model.preprocess.profiles.power import generate_power_profiles_from_cycles
from python_model.preprocess.profiles.radiation import generate_radiation_load_for_a_day
from python_model.preprocess.builders.battery import build_battery_specs

def load_operation_specs() -> OperationalSpecs:
    input_config = load_input_config()
    library_data = load_library_data()

    # Load Battery Specs to access OCV Curve and other properties
    batt_specs = build_battery_specs(input_config, library_data)

    charge_rate = input_config.max_charge_rate
    discharge_rate = input_config.max_discharge_rate
    n_cycles = input_config.n_cycles
    
    battery_capacity_ah = batt_specs.cell_capacity_ah
    battery_energy = batt_specs.total_energy / batt_specs.n_cells
    dt = 0.25

    # User requested to always start with charge (StateMachine handles full battery case)
    start_with_charge = True

    if input_config.custom_power_profile_path:
        # Load Custom Profile
        profile_path = Path(input_config.custom_power_profile_path)
        if not profile_path.exists():
            # Try finding it relative to project root? Or assume absolute/cwd?
            # Raise error for now if not found
             raise FileNotFoundError(f"Custom profile not found: {profile_path}")
             
        df = pd.read_csv(profile_path)
        # Expected columns: 'time' (s), 'power' (W)
        if 'time' not in df.columns or 'power' not in df.columns:
             raise ValueError(f"Custom profile must have 'time' and 'power' columns. Found: {df.columns}")
             
        time_s, soc, current, power_watts = process_custom_power_profile(
            custom_time=df['time'].values,
            custom_power=df['power'].values,
            ocv_curve=batt_specs.ocv_df,
            battery_capacity_ah=battery_capacity_ah,
            soc_init=input_config.soc_init,
            dt=dt
        )
    elif input_config.cycles:
        time_s, soc, current, power_watts = generate_power_profiles_from_cycles(
            cycles=input_config.cycles,
            charge_rate=charge_rate,
            discharge_rate=discharge_rate,
            total_energy=battery_energy,
            ocv_curve=batt_specs.ocv_df,
            battery_capacity_ah=battery_capacity_ah,
            soc_init=input_config.soc_init,
            dt=dt
        )
    else:
        time_s, soc, current, power_watts = generate_power_profiles_for_a_day(charge_rate=charge_rate,
                                                                  discharge_rate=discharge_rate,
                                                                  n_cycles=n_cycles,
                                                                  total_energy=battery_energy,
                                                                  ocv_curve=batt_specs.ocv_df,
                                                                  battery_capacity_ah=battery_capacity_ah,
                                                                  soc_init=input_config.soc_init,
                                                                  dt=dt
                                                                  )

    ambient_temp_constant = input_config.ambient_temperature + 273.15
    time_s, ambient_profile = generate_ambient_temp_profile_for_a_day(ambient_temp_constant, dt=dt)
    
    # Radiation
    sr = input_config.sunrise_time
    ss = input_config.sunset_time
    # If sunrise == sunset or values are invalid, disable radiation
    if sr == ss:
         max_rad = 0
    else:
         max_rad = 170 # Default

    time_s, radiation_profile = generate_radiation_load_for_a_day(max_radiation=max_rad, sunrise_time=sr, sunset_time=ss, dt=dt)

    return OperationalSpecs(time_s=time_s,
                            soc_profile=soc,
                            current_profile=current,
                            power_profile=power_watts,
                            ambient_profile=ambient_profile,
                            radiation_profile=radiation_profile)

if __name__ == '__main__':
    opec_specs = load_operation_specs()