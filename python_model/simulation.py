### This file contains the logic to run the simulation. This is the heart of the model. ###
import numpy as np
import pandas as pd
from properties import SystemConfig


class Simulation:
    def __init__(self, config: SystemConfig):
        self.config = config
        print(f"Simulation initialized with battery type: {self.config.battery_type}")


