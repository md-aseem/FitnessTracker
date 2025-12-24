import yaml
from pathlib import Path
from python_model.preprocess.properties import InputConfig

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
