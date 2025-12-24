import pandas as pd
import yaml
from pathlib import Path
from python_model.preprocess.properties import SystemSpecs, InputConfig, BatterySpecs, ChillerSpecs, OperationalSpecs
import os
from python_model.preprocess.generate_operational_profiles import generate_current_profile_for_a_day, generate_ambient_temp_profile_for_a_day
def load_input_config(path: str = None) -> InputConfig:
    if path is None:
        path = Path(__file__).parent.parent / "input.yaml"
    
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {path} (Resolved path: {config_path.absolute()})")
        
    with open(config_path, "r") as f:
        raw_data = yaml.safe_load(f)

    return InputConfig.model_validate(raw_data)

def load_library_data() -> dict:

    path = Path(__file__).parent.parent / "data" / "library.yaml"
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"Library file not found: {path} (Resolved path: {config_path.absolute()})")

    with open(config_path, "r") as f:
        library_data = yaml.safe_load(f)

    return library_data

def build_battery_specs(input_config: InputConfig,
                        library_data) -> BatterySpecs:

    battery_type = input_config.battery_type
    battery_life = input_config.battery_life

    # load ocv
    ocv_path = library_data['batteries'][battery_type]["ocv_path"]
    ocv_df = pd.read_csv(Path(__file__).parent.parent / ocv_path)
    ocv_df.sort_values(by=["soc"], inplace=True)

    # load heat gen data
    heat_gen_data_path = os.path.join(library_data['batteries'][battery_type]["heat_gen_dir"],
                                      f"{battery_type}_{battery_life}.csv")

    heat_gen_df = pd.read_csv(Path(__file__).parent.parent / heat_gen_data_path)

    # bringing everything together for battery config
    battery_specs = BatterySpecs(
        battery_type=battery_type,
        battery_life=battery_life,
        ocv_df=ocv_df,
        heat_gen_df=heat_gen_df
    )

    return battery_specs

def build_chiller_specs(input_config: InputConfig, library_data) -> ChillerSpecs:
    """
    The code to build chiller config.
    The code needs improvement. There is a lot of hardcoding right now.
    """
    chiller_model = input_config.chiller_model
    quantum = input_config.quantum

    is_envicool = 'envicool_55kW' in chiller_model

    if is_envicool and int(quantum) == 2:
        chiller_curves_dir = library_data['chillers']['envicool_q2_55kw']['chiller_curves_dir']

        low_temp = pd.read_csv(Path(__file__).parent.parent / chiller_curves_dir / "envicool_55kw_18c.csv")
        low_temp['temp'] = 18

        high_temp = pd.read_csv(Path(__file__).parent.parent / chiller_curves_dir / "envicool_55kw_23c.csv")
        high_temp['temp'] = 23

        chiller_curves_df = pd.concat([low_temp, high_temp], ignore_index=True)

    else:
        chiller_curves_df = pd.DataFrame()

    return ChillerSpecs(
        chiller_model=chiller_model,
        chiller_noise_kit=input_config.chiller_noise_kit,
        chiller_curves_df=chiller_curves_df
    )

def build_system_specs() -> SystemSpecs:

    input_config = load_input_config()
    library_data = load_library_data()

    battery_specs = build_battery_specs(input_config, library_data)
    chiller_specs = build_chiller_specs(input_config, library_data)
    system_specs = SystemSpecs(battery_specs=battery_specs, chiller_specs=chiller_specs)

    return system_specs


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

    return OperationalSpecs(time_s=time_s, current_profile=current_profile, ambient_profile=ambient_profile)

if __name__ == "__main__":
    # Test loading the default config
    try:
        system_specs = build_system_specs()
        operational_specs = load_operation_specs()
        print("Successfully loaded config:")
        print(system_specs)
    except Exception as e:
        print(f"Failed to load config: {e}")
