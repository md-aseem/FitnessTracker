from pydantic import BaseModel
import numpy as np
from typing import Optional, List
from dataclasses import dataclass

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
@dataclass
class ControlConfig:
    control_scheme: str

@dataclass
class BatteryConfig:
    battery_type: str
    battery_life: str

    # OCV data
    ocv_soc_bp: List[float]
    ocv_values_bp: List[float]

    # Thermal data

@dataclass
class ChillerConfig:
    chiller_model: str
    chiller_noise_kit: bool

@dataclass
class EnvironmentConfig:
    ambient_temperature: float
    sunrise_time: int
    sunset_time: int


### combined system config
@dataclass
class SystemConfig:

    control_config: ControlConfig
    battery_config: BatteryConfig
    chiller_config: ChillerConfig
    environment_config: EnvironmentConfig



### Solver Config

class SolverConfig(BaseModel):
    pass

