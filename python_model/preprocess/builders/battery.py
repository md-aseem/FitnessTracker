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
        heat_gen_df=heat_gen_df
    )

    return battery_specs
