import pandas as pd
from pathlib import Path
import os
from python_model.preprocess.properties import InputConfig, BatterySpecs

def build_battery_specs(input_config: InputConfig,
                        library_data) -> BatterySpecs:

    battery_type = input_config.battery_type
    battery_life = input_config.battery_life

    # load ocv
    ocv_path = library_data['batteries'][battery_type]["ocv_path"]
    ocv_df = pd.read_csv(Path(__file__).parent.parent.parent / ocv_path)
    ocv_df.sort_values(by=["soc"], inplace=True)

    # load heat gen data
    heat_gen_data_path = os.path.join(library_data['batteries'][battery_type]["heat_gen_dir"],
                                      f"{battery_type}_{battery_life}.csv")

    heat_gen_df = pd.read_csv(Path(__file__).parent.parent.parent / heat_gen_data_path)

    # bringing everything together for battery config
    battery_specs = BatterySpecs(
        battery_type=battery_type,
        battery_life=battery_life,
        ocv_df=ocv_df,
        heat_gen_df=heat_gen_df,
        mass=25600.0, # 80.0 modules * 320.0 mass per module?
        cp=990.0,
        k=9.0, # top to bottom conductivity?
        area=80.0,
        thickness=0.204,
        topUA=15.0, # how?
        coldPlateUA=666.67, # 20000.0 / 30.0 how?
        initial_temperature=input_config.initial_battery_temp + 273.15,
        initial_soc=input_config.initial_soc,
        total_energy=(3.47*52.0)*(304.0*80.0), # from C model
        n_cells_in_a_module=52,
        n_modules_in_a_string=8,
        n_strings=10,
        cell_capacity=304.0
    )

    return battery_specs
