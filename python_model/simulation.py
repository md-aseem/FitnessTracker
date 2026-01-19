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

        self.n = self.operational_specs.n
        self.dt = self.operational_specs.dt
        self.time_s = self.operational_specs.time_s.copy()
        self.current_profile = self.operational_specs.current_profile.copy()
        self.ambient_temp_profile = self.operational_specs.ambient_profile.copy()
        self.radiation_heat_load = self.calculate_radiation_load()

        ### dissecting system specs here for easy access
        self.steel_wall_specs = self.system_specs.steel_wall_specs
        self.insulation_wall_specs = self.system_specs.insulation_wall_specs

        # heat and temperature 2D vectors. First dim is time, Second is space/nodes
        # Initialize with initial ambient temperature
        initial_temp = self.ambient_temp_profile[0]
        self.steel_walls_temp = np.full([self.n, 7], initial_temp)
        self.insulation_walls_temp = np.full([self.n, 7], initial_temp)

        self.internal_air_temp = np.ones([self.n]) # no discretization -> no 2nd dim


    def run(self):
        print(f"Running simulation...")


        # Main time-stepping loop
        for i in range(1, self.time_s.size):

            ### Calculating internal air temp and walls temp
            # Steel Wall Update
            steel_flux_to_outer_node = (self.radiation_heat_load[i] +                                                                  # heat from radiation
                                         ((self.ambient_temp_profile[i] - self.steel_walls_temp[i, 6]) * self.steel_wall_specs.R[0]) + # heat from ambient
                                         ((self.steel_walls_temp[i, 5] - self.steel_walls_temp[i, 6]) * self.steel_wall_specs.R[1]))   # heat from internal node

            steel_flux_to_inner_node = (((self.internal_air_temp[i-1] - self.steel_walls_temp[i-1, 0]) * self.steel_wall_specs.R[2]) + # heat from internal air
                                         (self.steel_walls_temp[i-1, 1] - self.steel_walls_temp[i-1, 0]) * self.steel_wall_specs.R[1] # heat from internal node
                                         )

            # Flux from air to steel wall (positive means heat leaves air)
            flux_from_air_to_steel_wall = (self.internal_air_temp[i-1] - self.steel_walls_temp[i-1, 0]) * self.steel_wall_specs.R[2]
            flux_to_inner_air_from_walls = -flux_from_air_to_steel_wall # accumulators for air update

            self.steel_walls_temp[i, 0] = (self.steel_walls_temp[i-1, 0] + steel_flux_to_inner_node*self.dt /
                                           (self.steel_wall_specs.mass * self.steel_wall_specs.cp / 7))
            self.steel_walls_temp[i, 6] = (self.steel_walls_temp[i-1, 6] + steel_flux_to_outer_node*self.dt /
                                           (self.steel_wall_specs.mass * self.steel_wall_specs.cp / 7))

            for j in range(1, 6):
                self.steel_walls_temp[i, j] = (self.steel_walls_temp[i-1,j] + (
                        (self.steel_walls_temp[i-1, j-1] - self.steel_walls_temp[i-1, j]) * self.steel_wall_specs.R[1] +
                        (self.steel_walls_temp[i-1, j+1] - self.steel_walls_temp[i-1, j]) * self.steel_wall_specs.R[1]) *
                        (self.dt / (self.steel_wall_specs.mass * self.steel_wall_specs.cp / 7)))


            # Insulation Wall Update
            insulation_flux_to_outer_node = (((self.ambient_temp_profile[i] - self.insulation_walls_temp[i, 6]) * self.insulation_wall_specs.R[0]) +
                                             ((self.insulation_walls_temp[i, 5] - self.insulation_walls_temp[i, 6]) * self.insulation_wall_specs.R[1]))

            insulation_flux_to_inner_node = (((self.internal_air_temp[i-1] - self.insulation_walls_temp[i-1, 0]) * self.insulation_wall_specs.R[2]) +
                                             ((self.insulation_walls_temp[i-1, 1] - self.insulation_walls_temp[i-1, 0]) * self.insulation_wall_specs.R[1]))

            # Flux from air to insulation wall
            flux_from_air_to_insulation_wall = (self.internal_air_temp[i-1] - self.insulation_walls_temp[i-1, 0]) * self.insulation_wall_specs.R[2]
            flux_to_inner_air_from_walls += -flux_from_air_to_insulation_wall

            self.insulation_walls_temp[i, 0] = (self.insulation_walls_temp[i-1, 0] + insulation_flux_to_inner_node * self.dt /
                                                (self.insulation_wall_specs.mass * self.insulation_wall_specs.cp / 7))
            self.insulation_walls_temp[i, 6] = (self.insulation_walls_temp[i-1, 6] + insulation_flux_to_outer_node * self.dt /
                                                (self.insulation_wall_specs.mass * self.insulation_wall_specs.cp / 7))

            for j in range(1, 6):
                self.insulation_walls_temp[i, j] = (self.insulation_walls_temp[i-1, j] + (
                        (self.insulation_walls_temp[i-1, j-1] - self.insulation_walls_temp[i-1, j]) * self.insulation_wall_specs.R[1] +
                        (self.insulation_walls_temp[i-1, j+1] - self.insulation_walls_temp[i-1, j]) * self.insulation_wall_specs.R[1]) *
                                                    (self.dt / (self.insulation_wall_specs.mass * self.insulation_wall_specs.cp / 7)))

            # Internal Air Temperature Update
            heat_into_air_from_battery = 0.0 # Placeholder as battery model is not connected yet
            
            self.internal_air_temp[i] = self.internal_air_temp[i-1] + (
                -heat_into_air_from_battery + flux_to_inner_air_from_walls) * self.dt / (20.0 * 1006.0)



    def calculate_ambient_heat_load_and_internal_air_temp(self):



        pass


    def calculate_radiation_load(self):

        container_wall_area = self.system_specs.container_specs.container_wall_area
        radiation_surface_prcnt = self.system_specs.container_specs.radiation_surface_prcnt

        radiation_surface_area = container_wall_area * radiation_surface_prcnt
        radiation_profile = self.operational_specs.radiation_profile

        radiation_load = radiation_profile * radiation_surface_area

        return radiation_load

if __name__ == "__main__":
    system_specs = build_system_specs()
    operational_specs = load_operation_specs()
    sim = Simulation(system_specs, operational_specs)
    sim.run()
