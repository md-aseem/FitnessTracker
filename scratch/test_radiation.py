import sys
import os
from pathlib import Path

# Add project root to sys.path
sys.path.append(str(Path(__file__).parent.parent))

from quantum_thermal_model.preprocess.profiles.radiation import generate_historical_radiation_profile
from quantum_thermal_model.preprocess.loaders import load_input_config
from quantum_thermal_model.preprocess.builders.operational import load_operation_specs

def test_fetch():
    print("Testing historical radiation fetch for London in June...")
    time_s, radiation = generate_historical_radiation_profile("London", 6)
    if time_s is not None:
        print(f"Success! Max radiation: {max(radiation):.1f} W/m2")
    else:
        print("Failed to fetch.")

def test_operational_specs():
    print("\nTesting operational specs loading with location/month...")
    try:
        specs = load_operation_specs()
        print(f"Operational Specs loaded. Max radiation in profile: {max(specs.radiation_profile):.1f} W/m2")
    except Exception as e:
        print(f"Error loading operational specs: {e}")

if __name__ == "__main__":
    test_fetch()
    test_operational_specs()
