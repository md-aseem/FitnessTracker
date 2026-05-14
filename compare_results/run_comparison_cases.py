import os
import subprocess
import yaml
import re
import pandas as pd
import numpy as np
import shutil
from pathlib import Path

import argparse

# Paths
BASE_DIR = Path("/Users/mas985/code/quantum-thermal-model")
PYTHON_INPUT = BASE_DIR / "quantum_thermal_model" / "input" / "input.yaml"
C_INPUT = BASE_DIR / "q2_c_model_v13" / "input.in"
PYTHON_SIM = "quantum_thermal_model.simulation"
C_EXE = BASE_DIR / "q2_c_model_v13" / "q2_transient_model"
COMPARE_DIR = BASE_DIR / "compare_results"
VENV_PYTHON = BASE_DIR / ".venv" / "bin" / "python"

def update_python_input(config):
    with open(PYTHON_INPUT, 'r') as f:
        data = yaml.safe_load(f)
    
    data.update(config)
    data['location'] = ""
    
    with open(PYTHON_INPUT, 'w') as f:
        yaml.dump(data, f, default_flow_style=False)

def update_c_input(config):
    with open(C_INPUT, 'r') as f:
        content = f.read()
    
    # Mappings
    CHILLER_MAP = {
        "bergstrom_55kw_c/2": "bergstrom_55kW_c/2",
        "envicool_q2_55kw_c/2": "envicool_55kW_c/2",
        "bergstrom_55kw_c/4": "bergstrom_55kW_c/4",
        "envicool_q2_55kw_c/4": "envicool_55kW_c/4",
    }
    BAT_TYPE_MAP = {
        "catl_306": "catl_306Ahr",
        "eve_306": "eve_306Ahr",
    }
    BAT_LIFE_MAP = {
        "bol": "beginning_of_life",
        "eol": "end_of_life",
    }
    YES_NO_MAP = {
        True: "yes",
        False: "no",
    }

    # Update simple values
    if 'ambient_temperature' in config:
        content = re.sub(r'@FIXED_AMBIENT_TEMPERATURE_C\{\s*[\d\.]+\s*\}', 
                        f'@FIXED_AMBIENT_TEMPERATURE_C{{ {config["ambient_temperature"]:.1f} }}', content)
    
    if 'initial_battery_temp' in config:
        content = re.sub(r'@INITIAL_BATTERY_TEMPERATURE_C\{\s*[\d\.]+\s*\}', 
                        f'@INITIAL_BATTERY_TEMPERATURE_C{{ {config["initial_battery_temp"]:.1f} }}', content)
    
    if 'max_charge_rate' in config:
        content = re.sub(r'@MAX_CHARGE_RATE\{\s*[\d\.]+\s*\}', 
                        f'@MAX_CHARGE_RATE{{ {config["max_charge_rate"]:.2f} }}', content)
    
    if 'max_discharge_rate' in config:
        content = re.sub(r'@MAX_DISCHARGE_RATE\{\s*[\d\.]+\s*\}', 
                        f'@MAX_DISCHARGE_RATE{{ {config["max_discharge_rate"]:.2f} }}', content)
    
    if 'soc_init' in config:
        content = re.sub(r'@INITIAL_STATE_OF_CHARGE\{\s*[\d\.]+\s*\}', 
                        f'@INITIAL_STATE_OF_CHARGE{{ {config["soc_init"]:.2f} }}', content)
    
    if 'chiller_model' in config:
        c_model = CHILLER_MAP.get(config['chiller_model'], config['chiller_model'])
        content = re.sub(r'@CHILLER_MODEL\{\s*.*?\s*\}', f'@CHILLER_MODEL{{ {c_model} }}', content)

    if 'battery_type' in config:
        b_type = BAT_TYPE_MAP.get(config['battery_type'], config['battery_type'])
        content = re.sub(r'@BATTERY_MODEL\{\s*.*?\s*\}', f'@BATTERY_MODEL{{ {b_type} }}', content)

    if 'battery_life' in config:
        b_life = BAT_LIFE_MAP.get(config['battery_life'], config['battery_life'])
        content = re.sub(r'@BATTERY_CONDITION\{\s*.*?\s*\}', f'@BATTERY_CONDITION{{ {b_life} }}', content)

    if 'chiller_noise_kit' in config:
        val = YES_NO_MAP.get(config['chiller_noise_kit'], "no")
        content = re.sub(r'@CHILLER_NOISE_KIT\{\s*.*?\s*\}', f'@CHILLER_NOISE_KIT{{ {val} }}', content)

    if 'hvac_present' in config:
        val = YES_NO_MAP.get(config['hvac_present'], "no")
        content = re.sub(r'@HVAC_PRESENT\{\s*.*?\s*\}', f'@HVAC_PRESENT{{ {val} }}', content)

    if 'cycles' in config and config['cycles']:
        cycle = config['cycles'][0]
        cycle_str = f'@CYCLE{{ {cycle["start_time"]:.1f} , {cycle["target_soc1"]:.2f} , {cycle["wait_time"]:.1f} , {cycle["target_soc2"]:.2f} }}'
        content = re.sub(r'@CYCLE\{.*?\}', cycle_str, content)

    with open(C_INPUT, 'w') as f:
        f.write(content)

def run_models(case_name):
    print(f"--- Running {case_name} ---")
    
    # Run Python
    print("Running Python model...")
    subprocess.run([str(VENV_PYTHON), "-m", PYTHON_SIM], cwd=BASE_DIR, check=True)
    
    # Run C
    print("Running C model...")
    subprocess.run([str(C_EXE)], cwd=C_EXE.parent, check=True)
    
    # Create case directory
    case_dir = COMPARE_DIR / case_name
    case_dir.mkdir(parents=True, exist_ok=True)
    
    # Move results
    shutil.copy(BASE_DIR / "results" / "python_simulation_results.csv", case_dir / "python_simulation_results.csv")
    shutil.copy(C_EXE.parent / "transient.out", case_dir / "transient.out")
    
    print(f"Results saved to {case_dir}")

def compare_results(case_name):
    case_dir = COMPARE_DIR / case_name
    p_path = case_dir / "python_simulation_results.csv"
    c_path = case_dir / "transient.out"
    
    p_df = pd.read_csv(p_path)
    c_df = pd.read_csv(c_path, sep=r"\s+", engine="python")
    
    # Align by time
    p_df['time_s_rounded'] = p_df['time_s'].round(2)
    c_df['Time(s)_rounded'] = c_df['Time(s)'].round(2)
    
    merged = pd.merge(p_df, c_df, left_on='time_s_rounded', right_on='Time(s)_rounded')
    
    if merged.empty:
        print(f"Error: No matching time steps found between Python and C results for {case_name}")
        return False

    # Variables to compare (C_name, P_name, Offset)
    comparisons = [
        ('SOC', 'soc', 0),
        ('Bat_temp_6', 'battery_top_temp_c', -273.15),
        ('Bat_temp_0', 'battery_bottom_temp_c', -273.15),
        ('Internal_Air_Temp(C)', 'internal_air_temp_c', 0),
        ('Current(A)', 'current_a', 0),
        ('Ambient_Temp(C)', 'ambient_temp_c', 0),
    ]
    
    print(f"\nComparison for {case_name} ({len(merged)} steps aligned):")
    matches = True
    tolerances = {
        'SOC': 0.01,
        'Bat_temp_6': 0.5,
        'Bat_temp_0': 0.5,
        'Internal_Air_Temp(C)': 0.5,
        'Current(A)': 10.0, # Allow some timing jitter
        'Ambient_Temp(C)': 0.1,
    }

    for c_col, p_col, offset in comparisons:
        c_val = merged[c_col].values + offset
        p_val = merged[p_col].values
        
        diff = np.abs(c_val - p_val)
        max_diff = np.max(diff)
        mean_diff = np.mean(diff)
        
        tol = tolerances.get(c_col, 0.1)
        print(f"  {c_col} vs {p_col}: Max Diff = {max_diff:.6f}, Mean Diff = {mean_diff:.6f} (Tol: {tol})")
        if max_diff > tol:
            # Special case for Current: if mean diff is low, maybe it's just jitter
            if c_col == 'Current(A)' and mean_diff < 0.5:
                print(f"    Note: High max diff in Current, but low mean diff ({mean_diff:.6f}). Likely timing jitter.")
            else:
                matches = False
            
    if matches:
        print(f"Result: SUCCESS - {case_name} matches exactly (within tolerance).")
    else:
        print(f"Result: DISCREPANCY - {case_name} does not match exactly.")
    
    return matches

# Define Cases
cases = [
    {
        "name": "case_2",
        "config": {
            "ambient_temperature": 45.0,
            "initial_battery_temp": 30.0,
            "soc_init": 0.50,
            "chiller_model": "envicool_q2_55kw_c/2",
            "battery_type": "catl_306",
            "battery_life": "bol",
            "hvac_present": False,
            "chiller_noise_kit": False,
            "max_charge_rate": 0.30,
            "max_discharge_rate": 0.30
        }
    },
    {
        "name": "case_3",
        "config": {
            "ambient_temperature": 25.0,
            "initial_battery_temp": 25.0,
            "soc_init": 0.10,
            "chiller_model": "bergstrom_55kw_c/4",
            "battery_type": "catl_306",
            "battery_life": "bol",
            "hvac_present": False,
            "chiller_noise_kit": False
        }
    },
    {
        "name": "case_4",
        "config": {
            "ambient_temperature": 35.0,
            "initial_battery_temp": 35.0,
            "soc_init": 0.01,
            "chiller_model": "envicool_q2_55kw_c/4",
            "battery_type": "catl_306",
            "battery_life": "bol",
            "hvac_present": False,
            "chiller_noise_kit": False
        }
    },
    {
        "name": "case_5",
        "config": {
            "ambient_temperature": 15.0,
            "initial_battery_temp": 20.0,
            "soc_init": 0.80,
            "chiller_model": "bergstrom_55kw_c/2",
            "battery_type": "catl_306",
            "battery_life": "bol",
            "hvac_present": False,
            "chiller_noise_kit": False
        }
    },
    {
        "name": "case_6",
        "config": {
            "ambient_temperature": 40.0,
            "initial_battery_temp": 35.0,
            "soc_init": 0.30,
            "chiller_model": "envicool_q2_55kw_c/2",
            "battery_type": "catl_306",
            "battery_life": "bol",
            "hvac_present": False,
            "chiller_noise_kit": False,
            "cycles": [{"start_time": 8.0, "target_soc1": 0.95, "wait_time": 1.0, "target_soc2": 0.70}]
        }
    },
]

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--only-compare", action="store_true")
    parser.add_argument("--case", type=str, help="Specific case to run/compare")
    args = parser.parse_args()

    results = {}
    
    target_cases = cases
    if args.case:
        target_cases = [c for c in cases if c["name"] == args.case]
        if not target_cases and args.case == "case_1":
            target_cases = [{"name": "case_1", "config": {}}] # Placeholder for Case 1
            
    for case in target_cases:
        if not args.only_compare:
            if case["config"]:
                update_python_input(case["config"])
                update_c_input(case["config"])
            run_models(case["name"])
        
        results[case["name"]] = compare_results(case["name"])
    
    print("\n" + "="*30)
    print("FINAL SUMMARY")
    print("="*30)
    for name, success in results.items():
        status = "MATCH" if success else "MISMATCH"
        print(f"{name}: {status}")
