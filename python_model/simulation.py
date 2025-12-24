### This file contains the logic to run the simulation. This is the heart of the model. ###
from python_model.preprocess.properties import SystemSpecs
from python_model.preprocess.builders.system import build_system_specs


class Simulation:
    def __init__(self, system_specs: SystemSpecs):
        self.system_specs = system_specs
        print(f"Simulation initialized with battery_type: {self.system_specs.battery_specs.battery_type}")

    def run(self):
        print(f"Running simulation...")

if __name__ == "__main__":
    system_specs = build_system_specs()
    sim = Simulation(system_specs)
    sim.run()
