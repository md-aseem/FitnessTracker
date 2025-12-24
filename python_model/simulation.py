### This file contains the logic to run the simulation. This is the heart of the model. ###
from python_model.preprocess.properties import SystemSpecs


class Simulation:
    def __init__(self, config: SystemSpecs):
        self.config = config
        print(f"Simulation initialized with battery type: {self.config.battery_type}")


