from pydantic import BaseModel
import numpy as np
from typing import Optional, List
### input config
class InputConfig(BaseModel):
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


### module configs
class ControlConfig(BaseModel):
    control_scheme: str

class BatteryConfig(BaseModel):
    battery_type: str
    battery_life: str

    # OCV data
    ocv_soc_bp: List[float] | np.ndarray
    ocv_values_bp: List[float] | np.ndarray

    # Thermal data


class ChillerConfig(BaseModel):
    chiller_model: str
    chiller_noise_kit: bool

class EnvironmentConfig(BaseModel):
    ambient_temperature: float | np.ndarray
    sunrise_time: int
    sunset_time: int


### combined system config
class SystemConfig(BaseModel):

    control_config: ControlConfig
    battery_config: BatteryConfig
    chiller_config: ChillerConfig
    environment_config: EnvironmentConfig



### Solver Config

class SolverConfig(BaseModel):
    pass

