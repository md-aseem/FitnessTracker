import pandas as pd
import numpy as np
from pathlib import Path
from python_model.preprocess.properties import OperationalSpecs
from python_model.preprocess.loaders import load_input_config, load_library_data
from python_model.preprocess.profiles import generate_power_profiles_for_a_day, process_custom_power_profile
from python_model.preprocess.profiles.power import generate_power_profiles_from_cycles
from python_model.preprocess.profiles.weather import fetch_historical_weather
from python_model.preprocess.builders.battery import build_battery_specs

def load_operation_specs(month_override: int = None, input_config=None, library_data=None) -> OperationalSpecs:
    if input_config is None:
        input_config = load_input_config()
    if library_data is None:
        library_data = load_library_data()

    # Use override if provided, else use config
    sim_month = month_override if month_override is not None else input_config.month

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
        df = pd.read_csv(profile_path)
        # Expected columns: 'time' (s), 'power' (W)
        if 'time' not in df.columns or 'power' not in df.columns:
             raise ValueError(f"Custom profile must have 'time' and 'power' columns. Found: {df.columns}")

        time_s, soc, current, power_watts = process_custom_power_profile(
            custom_time=df['time'].values,
            custom_power=df['power'].values,
            ocv_df=batt_specs.ocv_df,
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

    # Ambient Temperature & Radiation — single combined fetch
    SECONDS_IN_DAY = 86400
    total_steps = int(SECONDS_IN_DAY / dt) + 1
    time_s = np.arange(total_steps) * dt

    if input_config.location and sim_month:
         weather = fetch_historical_weather(input_config.location, sim_month)
         if weather is not None:
              # Interpolate hourly data (24 values) to simulation timestep
              hourly_times = np.arange(24) * 3600  # 0, 3600, 7200, ... 82800
              ambient_profile = np.interp(time_s, hourly_times, weather.hourly_temperature)
              radiation_profile = np.interp(time_s, hourly_times, weather.hourly_radiation)
         else:
              print("Warning: Historical weather fetch failed. Using defaults.")
              print(f"  Using constant ambient temperature: {input_config.ambient_temperature}°C")
              print("  Using NO radiation (0 W/m2)")
              ambient_profile = np.full(total_steps, input_config.ambient_temperature)
              radiation_profile = np.zeros(total_steps)
    else:
         print("No location/month provided.")
         print(f"  Using constant ambient temperature: {input_config.ambient_temperature}°C")
         print("  Using NO radiation (0 W/m2)")
         ambient_profile = np.full(total_steps, input_config.ambient_temperature)
         radiation_profile = np.zeros(total_steps)

    return OperationalSpecs(time_s=time_s,
                            soc_profile=soc,
                            current_profile=current,
                            power_profile=power_watts,
                            ambient_profile=ambient_profile,
                            radiation_profile=radiation_profile)

if __name__ == '__main__':
    opec_specs = load_operation_specs()