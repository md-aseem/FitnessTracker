
import pandas as pd
import numpy as np
from preprocess.profiles.power import generate_power_profiles_for_a_day

# Mock OCV curve
ocv_data = {
    'soc': [0.0, 0.5, 1.0],
    'ocv': [3.0, 3.5, 4.2]
}
ocv_curve = pd.DataFrame(ocv_data)

# Parameters
charge_rate = 1.0 # 1C
discharge_rate = 1.0 # 1C
n_cycles = 1
total_energy = 100.0 # Wh
battery_capacity_ah = 100.0 / 3.5 # Approx 28 Ah
soc_init = 0.5
dt = 1.0

print("Running generation...")
time_s, soc, current, power = generate_power_profiles_for_a_day(
    charge_rate=charge_rate,
    discharge_rate=discharge_rate,
    n_cycles=n_cycles,
    total_energy=total_energy,
    ocv_curve=ocv_curve,
    battery_capacity_ah=battery_capacity_ah,
    soc_init=soc_init,
    rest_between_cycles=10, # 10 seconds rest
    starting_time=0,
    dt=dt
)

print(f"Initial SOC: {soc[0]}")
print(f"First step Power: {power[1]}")
print(f"First step Current: {current[1]}")
print(f"First step SOC: {soc[1]}")

if soc[1] > soc[0]:
    direction = "Increased"
else:
    direction = "Decreased"

is_charge = (power[1] < 0) # Based on code p_charge = -charge_rate...
print(f"Power allows us to infer we are {'Charging' if is_charge else 'Discharging'}")
print(f"SOC {direction}")

# Check Rest
# Find first rest
# The code starts 'active'.
# Let's see if we can find a rest period
rest_indices = np.where(power == 0)[0]
print(f"Number of rest steps: {len(rest_indices)}")
if len(rest_indices) > 0:
    # Check consecutive zeros
    diffs = np.diff(rest_indices)
    print(f"Consective rest steps max run: {np.max(np.diff(np.where(np.diff(rest_indices) == 1)[0] ) ) if len(diffs) > 1 else 'N/A'}")
