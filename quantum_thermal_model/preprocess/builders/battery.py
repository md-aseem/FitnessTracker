import os
import pandas as pd
from pathlib import Path
from quantum_thermal_model.preprocess.properties import InputConfig, BatterySpecs

def build_battery_specs(input_config: InputConfig,
                        library_data,
                        soh: float = None) -> BatterySpecs:
    """
    Builds the battery specifications including SOH-based capacity scaling 
    and heat generation interpolation.
    """
    battery_type = input_config.battery_type
    
    # 1. Resolve SOH (State of Health)
    soh = _resolve_soh(input_config, soh)
    
    # 2. Load OCV Data
    ocv_df = _load_ocv_data(battery_type, library_data)

    # 3. Load and Interpolate Heat Generation Data (BOL vs EOL)
    heat_gen_df = _load_and_interpolate_heat_gen(battery_type, library_data, soh)

    # 4. Scale Capacity and Energy
    base_capacity = library_data['batteries'][battery_type]['capacity_ah']
    current_capacity = base_capacity * soh
    
    # Assuming BOL Energy is base for scaling
    bol_energy = (3.47 * 52.0) * (304.0 * 80.0) 
    current_energy = bol_energy * soh

    # 5. Assemble BatterySpecs
    return BatterySpecs(
        battery_type=battery_type,
        battery_life=input_config.battery_life,
        soh=soh,
        ocv_df=ocv_df,
        heat_gen_df=heat_gen_df,
        mass=10*8*52*6.15, # 10 strings * 8 modules * 52 cells in a module * 6.15 kg per cell
        cp=990.0,
        k=9.0, # top to bottom conductivity?
        area=80.0, # 10 strings * 8 modules * 1 m^2 area of the top of each module?
        thickness=0.204,
        topUA=15.0, # todo: how?
        coldPlateUA=666.67, # todo: 20000.0 / 30.0 how?
        initial_temperature=input_config.initial_battery_temp,
        soc_init=input_config.soc_init,
        total_energy=current_energy,
        n_cells_in_a_module=52,
        n_modules_in_a_string=8,
        n_strings=10,
        cell_capacity_ah=current_capacity
    )

def _resolve_soh(input_config: InputConfig, soh_override: float = None) -> float:
    """Determines SOH based on explicit override or config battery_life."""
    if soh_override is not None:
        return float(soh_override)
        
    if input_config.battery_life.lower() == 'eol':
        return 0.8
    return 1.0

def _load_ocv_data(battery_type: str, library_data: dict) -> pd.DataFrame:
    """Loads and prepares OCV curve from library data."""
    ocv_path = library_data['batteries'][battery_type]["ocv_path"]
    full_path = Path(__file__).parent.parent.parent / ocv_path
    df = pd.read_csv(full_path)
    return df.sort_values(by=["soc"])

def _load_and_interpolate_heat_gen(battery_type: str, library_data: dict, soh: float) -> pd.DataFrame:
    """
    Loads heat generation data. Interpolates between BOL and EOL if SOH 
    is between 0.8 and 1.0.
    """
    heat_gen_dir = library_data['batteries'][battery_type]["heat_gen_dir"]
    base_dir = Path(__file__).parent.parent.parent
    
    # Load BOL (Beginning of Life)
    bol_path = base_dir / heat_gen_dir / f"{battery_type}_bol.csv"
    bol_df = pd.read_csv(bol_path)

    if soh >= 1.0:
        return bol_df
    
    # Load EOL (End of Life)
    eol_path = base_dir / heat_gen_dir / f"{battery_type}_eol.csv"
    eol_df = pd.read_csv(eol_path)

    if soh <= 0.8:
        return eol_df

    # Interpolate
    # Alpha represents "how close to EOL are we?"
    # soh=1.0 -> alpha=0.0 (BOL), soh=0.8 -> alpha=1.0 (EOL)
    alpha = (1.0 - soh) / 0.2
    
    heat_gen_df = bol_df.copy()
    numeric_cols = bol_df.columns[1:]
    heat_gen_df[numeric_cols] = bol_df[numeric_cols] * (1 - alpha) + eol_df[numeric_cols] * alpha
    
    return heat_gen_df
