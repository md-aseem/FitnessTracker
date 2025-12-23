import pandas as pd
import yaml
from pathlib import Path
from properties import SystemConfig, InputConfig, BatteryConfig
import os

def load_input_config(path: str = None) -> InputConfig:
    if path is None:
        path = Path(__file__).parent / "input.yaml"
    
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {path} (Resolved path: {config_path.absolute()})")
        
    with open(config_path, "r") as f:
        raw_data = yaml.safe_load(f)

    return InputConfig.model_validate(raw_data)

def load_library_data() -> dict:

    path = Path(__file__).parent / "data" / "library.yaml"
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"Library file not found: {path} (Resolved path: {config_path.absolute()})")

    with open(config_path, "r") as f:
        library_data = yaml.safe_load(f)

    return library_data

def build_battery_config(input_config: InputConfig,
                         library_data) -> BatteryConfig:

    battery_type = input_config.battery_type
    battery_life = input_config.battery_life

    # load ocv
    ocv_path = library_data['batteries'][battery_type]["ocv_path"]
    ocv_df = pd.read_csv(ocv_path)
    ocv_df.sort_values(by=["soc"], inplace=True)

    # load heat gen data
    heat_gen_data_path = os.path.join(library_data['batteries'][battery_type]["heat_gen_dir"],
                                      f"{battery_type}_{battery_life}.csv")

    heat_gen_df = pd.read_csv(heat_gen_data_path)

    # bringing everything together for battery config
    battery_config = BatteryConfig(
        battery_type=battery_type,
        battery_life=battery_life,
        ocv_df=ocv_df,
        heat_gen_df=heat_gen_df
    )

    return battery_config


if __name__ == "__main__":
    # Test loading the default config
    try:
        input_config = load_input_config()
        library_data = load_library_data()
        battery_config = build_battery_config(input_config, library_data)

        print("Successfully loaded config:")
        print(battery_config)
    except Exception as e:
        print(f"Failed to load config: {e}")
