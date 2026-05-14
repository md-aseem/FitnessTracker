import cProfile
import pstats
from quantum_thermal_model.preprocess.builders import load_operation_specs
from quantum_thermal_model.preprocess.builders.system import build_system_specs
from quantum_thermal_model.simulation import Simulation

def main():
    system_specs = build_system_specs()
    operational_specs = load_operation_specs()
    sim = Simulation(system_specs, operational_specs)
    
    profiler = cProfile.Profile()
    profiler.enable()
    sim.run(steps=1000) # Run for 1000 steps to get a good profile
    profiler.disable()
    
    stats = pstats.Stats(profiler).sort_stats('tottime')
    stats.print_stats(20)

if __name__ == "__main__":
    main()
