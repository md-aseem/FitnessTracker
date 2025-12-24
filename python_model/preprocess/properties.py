from pydantic import BaseModel
import numpy as np
import pandas as pd
from dataclasses import dataclass

### input config
class InputConfig(BaseModel):

    ## high-level
    quantum: float

    ## operational
    c_rate: float
    n_cycles: int

    ambient_temperature: float
    initial_battery_temp: float
    max_charge_rate: float
    max_discharge_rate: float
    battery_type: str
    battery_life: str
    chiller_model: str
    chiller_noise_kit: bool
    initial_soc: float
    sunrise_time: int
    sunset_time: int
    control_scheme: str


### module specs
@dataclass
class ControlSpecs:
    control_scheme: str

@dataclass
class BatterySpecs:
    battery_type: str
    battery_life: str

    # OCV data
    ocv_df: pd.DataFrame

    # Thermal data
    heat_gen_df: pd.DataFrame

@dataclass
class ChillerSpecs:
    chiller_model: str
    chiller_noise_kit: bool
    chiller_curves_df: pd.DataFrame

    battery_sensitivity: float
    inverter_sensitivity: float

    # ambiguous
    battery_temp_target_C: int
    inverter_temp_target_C: int

    electronics_aux_power: float

    # these power values are multiplied by percent, from 0 to 1, to get power of each component in the code
    pcs_pump_power_per_pcnt: float
    bat_pump_power_per_prcnt: float
    fan_aux_power_per_pcnt: float

    # flow rate
    bat_volume_flow_rate_per_prcnt: float
    pcs_volume_flow_rate_per_prcnt: float


@dataclass
class EnvironmentSpecs:
    ambient_temperature: float
    sunrise_time: int
    sunset_time: int


@dataclass
class OperationalSpecs:
    time_s: np.ndarray
    current_profile: np.ndarray
    ambient_profile: np.ndarray


### combined system specs
@dataclass
class SystemSpecs:

    battery_specs: BatterySpecs
    chiller_specs: ChillerSpecs



### Solver specs

class SolverConfig(BaseModel):
    pass

