from pathlib import Path
from process_input import load_config
from simulation import Simulation

def main():
    # 1. Load configuration
    try:
        config_path = Path(__file__).parent / "input.yaml"
        config = load_config(str(config_path))
        print("Config loaded successfully.")
    except Exception as e:
        print(f"Error loading config: {e}")
        return

    # 2. Initialize simulation
    sim = Simulation(config)
    
    # 3. Run simulation (placeholder for now)
    print("Simulation ready to run.")
    # sim.run()

if __name__ == "__main__":
    main()
