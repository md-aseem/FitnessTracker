### This file contains the logic to run the simulation. This is the heart of the model. ###
from python_model.preprocess.builders import load_operation_specs
from python_model.preprocess.properties import SystemSpecs, OperationalSpecs
from python_model.preprocess.builders.system import build_system_specs
import numpy as np
from scipy.interpolate import RegularGridInterpolator

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

        # Battery Temp
        # Initialize with initial battery temperature
        initial_batt_temp = self.system_specs.battery_specs.initial_temperature
        self.battery_temp = np.full([self.n, 7], initial_batt_temp)

        # SOC
        self.soc = np.zeros([self.n])
        self.soc[0] = self.system_specs.battery_specs.initial_soc

        # Setup Heat Generation Interpolator
        self.heat_gen_interpolator = self.generate_heat_gen_interpolator()


    def generate_heat_gen_interpolator(self):
        df = self.system_specs.battery_specs.heat_gen_df
        # heat_gen_df format: cols 1..N are C-rates, col 0 is SOC
        c_rate_cols = df.columns[1:].astype(float).values
        soc_col = df.iloc[:, 0].values
        heat_data = df.iloc[:, 1:].values

        # Initialize interpolator
        # Points must be strictly ascending/descending. Assuming input df follows this.
        return RegularGridInterpolator(
            (soc_col, c_rate_cols),
            heat_data,
            bounds_error=False,
            fill_value=None
        )

    def run(self):
        print(f"Running simulation...")


        # Main time-stepping loop
        for i in range(1, self.time_s.size):

            ### Calculating internal air temp and walls temp
            self.calculate_ambient_heat_load_and_internal_air_temp(i)
            self.update_soc(i)
            self.update_battery_temp(i)


    def calculate_ambient_heat_load_and_internal_air_temp(self, i):

        # Steel Wall Update
        steel_flux_to_outer_node = (self.radiation_heat_load[i] +  # heat from radiation
                                    ((self.ambient_temp_profile[i] - self.steel_walls_temp[i, 6]) *
                                     self.steel_wall_specs.R[0]) +  # heat from ambient
                                    ((self.steel_walls_temp[i, 5] - self.steel_walls_temp[i, 6]) *
                                     self.steel_wall_specs.R[1]))  # heat from internal node

        steel_flux_to_inner_node = (((self.internal_air_temp[i - 1] - self.steel_walls_temp[i - 1, 0]) *
                                     self.steel_wall_specs.R[2]) +  # heat from internal air
                                    (self.steel_walls_temp[i - 1, 1] - self.steel_walls_temp[i - 1, 0]) *
                                    self.steel_wall_specs.R[1]  # heat from internal node
                                    )

        # Flux from air to steel wall (positive means heat leaves air)
        flux_from_air_to_steel_wall = (self.internal_air_temp[i - 1] - self.steel_walls_temp[i - 1, 0]) * \
                                      self.steel_wall_specs.R[2]
        flux_to_inner_air_from_walls = -flux_from_air_to_steel_wall  # accumulators for air update

        self.steel_walls_temp[i, 0] = (self.steel_walls_temp[i - 1, 0] + steel_flux_to_inner_node * self.dt /
                                       (self.steel_wall_specs.mass * self.steel_wall_specs.cp / 7))
        self.steel_walls_temp[i, 6] = (self.steel_walls_temp[i - 1, 6] + steel_flux_to_outer_node * self.dt /
                                       (self.steel_wall_specs.mass * self.steel_wall_specs.cp / 7))

        for j in range(1, 6):
            self.steel_walls_temp[i, j] = (self.steel_walls_temp[i - 1, j] + (
                    (self.steel_walls_temp[i - 1, j - 1] - self.steel_walls_temp[i - 1, j]) * self.steel_wall_specs.R[
                1] +
                    (self.steel_walls_temp[i - 1, j + 1] - self.steel_walls_temp[i - 1, j]) * self.steel_wall_specs.R[
                        1]) *
                                           (self.dt / (self.steel_wall_specs.mass * self.steel_wall_specs.cp / 7)))

        # Insulation Wall Update
        insulation_flux_to_outer_node = (((self.ambient_temp_profile[i] - self.insulation_walls_temp[i, 6]) *
                                          self.insulation_wall_specs.R[0]) +
                                         ((self.insulation_walls_temp[i, 5] - self.insulation_walls_temp[i, 6]) *
                                          self.insulation_wall_specs.R[1]))

        insulation_flux_to_inner_node = (((self.internal_air_temp[i - 1] - self.insulation_walls_temp[i - 1, 0]) *
                                          self.insulation_wall_specs.R[2]) +
                                         ((self.insulation_walls_temp[i - 1, 1] - self.insulation_walls_temp[
                                             i - 1, 0]) * self.insulation_wall_specs.R[1]))

        # Flux from air to insulation wall
        flux_from_air_to_insulation_wall = (self.internal_air_temp[i - 1] - self.insulation_walls_temp[i - 1, 0]) * \
                                           self.insulation_wall_specs.R[2]
        flux_to_inner_air_from_walls += -flux_from_air_to_insulation_wall

        self.insulation_walls_temp[i, 0] = (
                    self.insulation_walls_temp[i - 1, 0] + insulation_flux_to_inner_node * self.dt /
                    (self.insulation_wall_specs.mass * self.insulation_wall_specs.cp / 7))
        self.insulation_walls_temp[i, 6] = (
                    self.insulation_walls_temp[i - 1, 6] + insulation_flux_to_outer_node * self.dt /
                    (self.insulation_wall_specs.mass * self.insulation_wall_specs.cp / 7))

        for j in range(1, 6):
            self.insulation_walls_temp[i, j] = (self.insulation_walls_temp[i - 1, j] + (
                    (self.insulation_walls_temp[i - 1, j - 1] - self.insulation_walls_temp[i - 1, j]) *
                    self.insulation_wall_specs.R[1] +
                    (self.insulation_walls_temp[i - 1, j + 1] - self.insulation_walls_temp[i - 1, j]) *
                    self.insulation_wall_specs.R[1]) *
                    (self.dt / (self.insulation_wall_specs.mass * self.insulation_wall_specs.cp / 7)))

        # Internal Air Temperature Update
        heat_into_air_from_battery = 0.0  # Placeholder as battery model is not connected yet

        self.internal_air_temp[i] = self.internal_air_temp[i - 1] + (
                -heat_into_air_from_battery + flux_to_inner_air_from_walls) * self.dt / (20.0 * 1006.0)


    def update_battery_temp(self, i):

        # Calculate Heat Generation
        total_heat_gen = self.calculate_battery_heat_generation(i)
        
        # Update Temperatures
        b_specs = self.system_specs.battery_specs
        
        # Placeholder for Chiller/Coolant state
        # TODO: Implement full chiller/pump logic.
        # Using values approximating 'circulation mode' or standard flow from C model for now.
        # 480 LPM max * 0.40 percent = 192 LPM
        volume_flow_rate_lpm = 192.0 
        coolant_mass_flow = (volume_flow_rate_lpm / 60000.0) * 1050.0 # kg/s (~3.36 kg/s)
        coolant_cp = 3400.0 # J/kgK
        
        # Temp leaving chiller (entering cold plate)
        # TODO: Link to chiller model
        tlc_last = 293.15 # 20 C
        
        # Max Enthalpy Delta
        # maxEnthalpyDelta = c->batteryStream->massFlowRate*c->batteryStream->coolantCp*(b->tempLast[0] - c->batteryStream->tlcLast);
        max_possible_heat_transfer = coolant_mass_flow * coolant_cp * (self.battery_temp[i-1, 0] - tlc_last)
        
        # Heat Fluxes
        # bottomQ = -0.4*maxEnthalpyDelta + (b->tempLast[1] - b->tempLast[0])*R[1];
        bottom_q = -0.4 * max_possible_heat_transfer + (self.battery_temp[i-1, 1] - self.battery_temp[i-1, 0]) * b_specs.R[1]
        
        # topQ    = (simmain->internalAirTemp - b->tempLast[6])*R[2] + (b->tempLast[5] - b->tempLast[6])*R[1];
        top_q = (self.internal_air_temp[i-1] - self.battery_temp[i-1, 6]) * b_specs.R[2] + \
                (self.battery_temp[i-1, 5] - self.battery_temp[i-1, 6]) * b_specs.R[1]
                

        # Node 0 (Bottom)
        # b->temperature[0] += (bottomQ + (ONE/7.0)*batteryTotalHeatGeneration(simmain))*transientDt/(b->mass * b->cp / 7.0);
        self.battery_temp[i, 0] = self.battery_temp[i-1, 0] + \
                                  (bottom_q + (1.0/7.0) * total_heat_gen) * self.dt / \
                                  (b_specs.mass * b_specs.cp / 7.0)

        # Node 6 (Top)
        # b->temperature[6] += (topQ    + (ONE/7.0)*batteryTotalHeatGeneration(simmain) +  batteryTabHeat)*transientDt/(b->mass * b->cp / 7.0);
        battery_tab_heat = 0.0 
        self.battery_temp[i, 6] = self.battery_temp[i-1, 6] + \
                                  (top_q + (1.0/7.0) * total_heat_gen + battery_tab_heat) * self.dt / \
                                  (b_specs.mass * b_specs.cp / 7.0)

        # Middle Nodes (1-5)
        for j in range(1, 6):
            # b->temperature[i] += (((ONE/7.0)*batteryTotalHeatGeneration(simmain)) 
            #                   +  (b->tempLast[i-1] - b->tempLast[i])*R[1]
            #                   +  (b->tempLast[i+1] - b->tempLast[i])*R[1])*transientDt/(b->mass * b->cp / 7.0);
            self.battery_temp[i, j] = self.battery_temp[i-1, j] + \
                                      ((1.0/7.0 * total_heat_gen) + \
                                       (self.battery_temp[i-1, j-1] - self.battery_temp[i-1, j]) * b_specs.R[1] + \
                                       (self.battery_temp[i-1, j+1] - self.battery_temp[i-1, j]) * b_specs.R[1]) * \
                                      self.dt / (b_specs.mass * b_specs.cp / 7.0)


    def update_soc(self, i):
        # b->soc += currentPower*transientDt /(3600.0*b->totalBatteryEnergy);
        
        self.soc[i] = np.clip(
            self.soc[i-1] + self.current_profile[i] / self.system_specs.battery_specs.cell_capacity,
            0, 1)

    def get_ocv(self, soc):
        ocv_df = self.system_specs.battery_specs.ocv_df
        # Assuming index 0 is SOC and index 1 is Voltage
        return np.interp(soc, ocv_df.iloc[:, 0], ocv_df.iloc[:, 1])

    def calculate_battery_heat_generation(self, i):
        # Interpolate 2D: SOC and C-Rate
        
        current_amps = self.current_profile[i]
        c_rate = current_amps / self.system_specs.battery_specs.cell_capacity
        
        soc = self.soc[i]
        cell_heat = self.heat_gen_interpolator((soc, c_rate))
        
        # Total Heat
        total_heat = cell_heat * self.system_specs.battery_specs.n_cells

        return total_heat

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
