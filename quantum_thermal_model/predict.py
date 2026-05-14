import numpy as np
from quantum_thermal_model.simulation import Simulation
from quantum_thermal_model.preprocess.loaders import load_input_config, load_library_data
from quantum_thermal_model.preprocess.builders.system import build_system_specs
from quantum_thermal_model.preprocess.builders.operational import load_operation_specs
from quantum_thermal_model.preprocess.properties import InputConfig

def predict_operating_resting_temp(n_cycles: float, chiller_setpoint: float, cp_rate: float, dod: float, ambient_temp: int) -> \
tuple[float, float]:
    """
    High-level wrapper to run a 1-day simulation and return the mean battery temperature in Kelvin.
    """
    # 0. make input config
    input_config = InputConfig(n_cycles=n_cycles,
                               ambient_temperature=ambient_temp,
                               max_charge_rate=cp_rate,
                               max_discharge_rate=cp_rate,
                               chiller_setpoint=chiller_setpoint,
                               battery_type="catl_306")
    # 1. Load library config
    library_data = load_library_data()
    
    # 2. Build specs
    system_specs = build_system_specs(input_config, library_data)
    operational_specs = load_operation_specs(input_config=input_config, library_data=library_data)
    
    # 3. Run simulation
    sim = Simulation(system_specs, operational_specs)
    sim.run()

    return sim.avg_temp_operating, sim.avg_temp_resting

if __name__ == "__main__":
    operating_temp, resting_temp = predict_operating_resting_temp(1, 19, 0.25, 1, 20)
    print(f"Operating Temperature: {operating_temp} C")
    print(f"Resting Temperature: {resting_temp} C")