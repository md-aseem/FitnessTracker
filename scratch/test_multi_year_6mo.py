from quantum_thermal_model.simulation_multi_year import SimulationMultiYear
import os

if __name__ == "__main__":
    # Override n_years for testing
    sim = SimulationMultiYear(n_years=2)
    sim.run()
