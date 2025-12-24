### This file contains the logic to run the simulation. This is the heart of the model. ###
from python_model.preprocess.builders import load_operation_specs
from python_model.preprocess.properties import SystemSpecs, OperationalSpecs
from python_model.preprocess.builders.system import build_system_specs
import numpy as np

class Simulation:
    def __init__(self, system_specs: SystemSpecs, operational_specs: OperationalSpecs):
        self.system_specs = system_specs
        self.operational_specs = operational_specs
        print(f"Simulation initialized with battery_type: {self.system_specs.battery_specs.battery_type}")

        self.time_s = self.operational_specs.time_s.copy()
        self.current_profile = self.operational_specs.current_profile.copy()
        self.ambient_temp_profile = self.operational_specs.ambient_profile.copy()


    def run(self):
        print(f"Running simulation...")



if __name__ == "__main__":
    system_specs = build_system_specs()
    operational_specs = load_operation_specs()
    sim = Simulation(system_specs, operational_specs)
    sim.run()
