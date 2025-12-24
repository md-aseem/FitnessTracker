from pydantic import BaseModel
import numpy as np
import pandas as pd
from dataclasses import dataclass

### input config
class InputConfig(BaseModel):
    quantum: float
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

@dataclass
class EnvironmentSpecs:
    ambient_temperature: float
    sunrise_time: int
    sunset_time: int


### combined system specs
@dataclass
class SystemSpecs:

    control_specs: ControlSpecs
    battery_specs: BatterySpecs
    chiller_specs: ChillerSpecs
    environment_specs: EnvironmentSpecs



### Solver specs

class SolverConfig(BaseModel):
    pass

