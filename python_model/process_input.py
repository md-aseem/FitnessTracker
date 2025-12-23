
import yaml
from pathlib import Path
from properties import SystemConfig, InputConfig, BatteryConfig


def load_input_config(path: str = None) -> InputConfig:
    if path is None:
        path = Path(__file__).parent / "input.yaml"
    
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {path} (Resolved path: {config_path.absolute()})")
        
    with open(config_path, "r") as f:
        raw_data = yaml.safe_load(f)

    return InputConfig.model_validate(raw_data)

def hydrate_battery_config(input_config: InputConfig) -> BatteryConfig:

    pass

def build_system_config(input_config: InputConfig) -> SystemConfig:
    return SystemConfig.model_validate(input_config)

if __name__ == "__main__":
    # Test loading the default config
    try:
        input_config = load_input_config()
        system_config = build_system_config(input_config)
        print("Successfully loaded config:")
        print(input_config.model_dump_json(indent=2))
    except Exception as e:
        print(f"Failed to load config: {e}")
