from typing import Literal
from pydantic import BaseModel, Field
import numpy as np
import pandas as pd
from dataclasses import dataclass, field

### input config
class InputConfig(BaseModel):

    ## high-level
    quantum: Literal["2p0", "3p0", "2p1"]

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

    # Thermal Properties
    mass: float
    cp: float
    k: float
    area: float
    thickness: float
    topUA: float
    coldPlateUA: float
    initial_temperature: float
    initial_soc: float
    total_energy: float
    n_cells_in_a_module: int
    n_modules_in_a_string: int
    n_strings: int
    cell_capacity: float

    dx: float = field(init=False)
    R: np.ndarray = field(init=False)

    def __post_init__(self):
        self.dx = self.thickness / 7
        self.R = np.array([
            self.area * (1 / ((1 / self.coldPlateUA) + ((self.dx / 2) / self.k))),
            self.area * self.k / self.dx,
            self.area * (1 / ((1 / self.topUA) + ((self.dx / 2) / self.k)))
        ])
        self.n_cells = self.n_cells_in_a_module * self.n_modules_in_a_string * self.n_strings

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

    # caps/limits
    pump_aux_cap: float
    comp_aux_cap: float
    cooling_power_coef: float

    def __post_init__(self):
        self.combined_cap = 0.7 * self.comp_aux_cap + 0.15 * self.pump_aux_cap + 0.15 # ac in c-code

@dataclass
class WallSpecs:
    rho: float
    area: float
    mass: float
    cp: float
    k: float
    thickness: float
    innerUA: float = 8.0
    outerUA: float = 8.0

    def __post_init__(self):
        self.dx = self.thickness / 7 # 7 nodes hardcoded into the code for now
        self.R =  np.array([self.area * (1 / ((1 / self.outerUA) + ((self.dx / 2) / self.k))),  # wall-to-ambient thermal conductance
                            self.area * self.k / self.dx,                                       # node-to-node thermal conductance
                            self.area * (1 / ((1 / self.innerUA) + ((self.dx / 2) / self.k)))]) # # inner-to-wall thermal conductance

@dataclass
class EnvironmentSpecs:
    ambient_temperature: float
    sunrise_time: int
    sunset_time: int
    is_radiation: bool = True
    radiation_intensity: float = 350 # W/m2  radiation_intensity(1000) * absorptivity(0.35)
    percent_surface_in_radiation: float = 1

@dataclass
class ContainerSpecs:
    container_wall_area: float
    radiation_surface_prcnt: float
    container_wall_UA: float
    container_wall_prcnt_steel: float

@dataclass
class OperationalSpecs:
    time_s: np.ndarray
    current_profile: np.ndarray
    ambient_profile: np.ndarray
    radiation_profile: np.ndarray

    def __post_init__(self):
        self.n = self.current_profile.shape[0]
        self.dt = np.diff(self.time_s)[0]


### combined system specs
@dataclass
class SystemSpecs:

    battery_specs: BatterySpecs
    chiller_specs: ChillerSpecs
    container_specs: ContainerSpecs
    steel_wall_specs: WallSpecs # wall 1
    insulation_wall_specs: WallSpecs # wall 2


### Solver specs

class SolverConfig(BaseModel):
    pass

