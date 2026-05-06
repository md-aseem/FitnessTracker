from python_model.preprocess.properties import SystemSpecs
from python_model.preprocess.loaders import load_input_config, load_library_data
from .battery import build_battery_specs
from .chiller import build_chiller_specs
from .walls import build_wall_specs
from .container import build_container_specs

def build_system_specs() -> SystemSpecs:

    input_config = load_input_config()
    library_data = load_library_data()

    battery_specs = build_battery_specs(input_config, library_data)
    chiller_specs = build_chiller_specs(input_config, library_data)
    steel_wall_specs, insulation_wall_specs = build_wall_specs(input_config, library_data)
    container_specs = build_container_specs(input_config, library_data)
    system_specs = SystemSpecs(battery_specs=battery_specs,
                               chiller_specs=chiller_specs,
                               container_specs=container_specs,
                               steel_wall_specs=steel_wall_specs,
                               insulation_wall_specs=insulation_wall_specs,
                               hvac_present=input_config.hvac_present)

    return system_specs
