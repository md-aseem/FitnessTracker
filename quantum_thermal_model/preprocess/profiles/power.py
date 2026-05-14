import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

def generate_power_profiles_for_a_day(charge_rate: float,
                                      discharge_rate: float,
                                      n_cycles: int,
                                      total_energy: float, # total_energy = battery_ah_capacity * nominal_voltage
                                      ocv_curve: pd.DataFrame,
                                      battery_capacity_ah: float,
                                      soc_init: float,
                                      rest_between_cycles: float = 4,
                                      starting_time: int = 4,  # 24 hour timezone
                                      dt: float = 1.0
                                      ):
    """
    Generates Power, Current and SOC profiles for a day.
    
    Args:
        ocv_curve: DataFrame with col 0 = SOC, col 1 = Voltage
    """

    SECONDS_IN_DAY = 86400
    total_steps = int(SECONDS_IN_DAY / dt) + 1
    
    # Initialize full day arrays
    time_s = np.arange(total_steps) * dt
    power = np.zeros(total_steps)
    current = np.zeros(total_steps)
    soc = np.zeros(total_steps)

    # Throughput Targets (Ah)
    # 1 Cycle = 2 * Capacity (Charge fully + Discharge fully)
    half_cycle_target_ah_throughput = battery_capacity_ah

    # initial rest
    starting_rest_steps = int(3600 * starting_time / dt)
    soc[:starting_rest_steps] = soc_init

    soc_bp = ocv_curve['soc'].values
    ocv_bp = ocv_curve['ocv'].values
    def get_voltage(soc):
        return np.interp(soc, soc_bp, ocv_bp)

    # initializing the counter and charge direction
    soc[:starting_rest_steps] = soc_init
    half_cycle_ah_throughput = 0
    is_charge = True
    rest_timer = 0
    cycles = 0
    half_cycle_ah_throughput_array = []

    for i in range(starting_rest_steps, total_steps):
        if cycles >= n_cycles:
            soc[i] = soc[i-1]
            continue

        # update state
        ### we are using two variables to track the state -> state = active/rest and is_charge = True/False
        if half_cycle_ah_throughput < half_cycle_target_ah_throughput:
            state = 'active'
            rest_timer = 0

            if is_charge and soc[i-1] >= 1: # changing state to discharging if prev state is charging and soc is 1.
                is_charge = not is_charge
            elif not is_charge and soc[i-1] <= 0: # changing state to charging if prev state is discharging and soc is 0.
                is_charge = not is_charge

        else:
            state = 'rest'
            if rest_timer > rest_between_cycles * 3600:
                state = 'active'
                cycles += 0.5
                half_cycle_ah_throughput = 0

        # time-stepping according to the state
        if state == 'rest':
            soc[i] = soc[i-1]
            current[i] = 0
            power[i] = 0
            rest_timer += dt

        if state == 'active':
            voltage = get_voltage(soc[i-1])
            rate = charge_rate if is_charge else -discharge_rate
            current_power = rate * total_energy
            current_current = current_power / voltage
            soc[i] = soc[i-1] + current_current * dt / (battery_capacity_ah * 3600)
            power[i] = current_power
            current[i] = current_current
            half_cycle_ah_throughput += abs(current_current) * dt / 3600

        half_cycle_ah_throughput_array.append(half_cycle_ah_throughput)

    return time_s, soc, current, power


def process_custom_power_profile(custom_time: np.ndarray,
                                 custom_power: np.ndarray,
                                 ocv_df: pd.DataFrame,
                                 battery_capacity_ah: float,
                                 soc_init: float,
                                 dt: float = 1.0
                                 ):
    """
    Process a custom power profile:
    1. Interpolate power to simulation time steps (dt).
    2. Calculate Current and SOC iteratively.
    """
    print(f"Loading custom power profile")
    # 1. Determine Simulation Time (Fixed 24 hours)
    SECONDS_IN_DAY = 86400
    
    # Generate time steps for exactly one day
    total_steps = int(SECONDS_IN_DAY / dt) + 1
    time_s = np.arange(total_steps) * dt
    
    # 2. Interpolate Power
    # Use np.interp with left/right fill of 0.0 to pad if custom profile is shorter
    # If custom profile is longer, it will just pick values up to 24h
    power_watts = np.interp(time_s, custom_time, custom_power, left=0.0, right=0.0)
    
    # 3. Calculate SOC and Current
    current = np.zeros(total_steps)
    soc = np.zeros(total_steps)
    soc[0] = soc_init
    
    # OCV Interp Helpers
    ocv_soc_vals = ocv_df['soc'].values
    ocv_voltage_vals = ocv_df['ocv'].values
    
    def get_voltage(soc, current):
        ocv = np.interp(soc, ocv_soc_vals, ocv_voltage_vals)
        v = ocv + current * 0.0004 # assuming the resistance is constant to 0.4 mOhm
        # v = ocv + current * 0      # assuming the resistance is constant to zero for validation
        return max(2.5, v)

    for i in range(1, total_steps-1):

        # Setup Current SOC
        current_soc = soc[i-1]
            
        # Get Voltage & Current
        v = get_voltage(soc[i-1], current[i-1])
        
        # I = P / V
        # If P is provided, I is result.
        i_val = power_watts[i] / v
        current[i] = i_val
        
        # Update SOC for next step
        # dSOC = - I * dt / Cap
        d_ah = -(i_val * dt / 3600.0)
        new_soc = current_soc + (d_ah / battery_capacity_ah)

        # Clamp SOC
        new_soc = max(0.0, min(1.0, new_soc))

        soc[i] = new_soc
            
    return time_s, soc, current, power_watts


def generate_power_profiles_from_cycles(cycles: list,
                                        charge_rate: float,
                                        discharge_rate: float,
                                        total_energy: float,
                                        ocv_curve: pd.DataFrame,
                                        battery_capacity_ah: float,
                                        soc_init: float,
                                        dt: float = 1.0
                                        ):
    SECONDS_IN_DAY = 86400
    total_steps = int(SECONDS_IN_DAY / dt) + 1
    
    time_s = np.arange(total_steps) * dt
    power = np.zeros(total_steps)
    current = np.zeros(total_steps)
    soc = np.zeros(total_steps)
    soc[0] = soc_init
    
    ocv_soc_vals = ocv_curve.iloc[:, 0].values
    ocv_voltage_vals = ocv_curve.iloc[:, 1].values
    def get_voltage(s):
        v = np.interp(s, ocv_soc_vals, ocv_voltage_vals)
        return max(1.0, v)

    current_cycle_idx = 0
    phase = 0 # 0=wait for start, 1=goto soc1, 2=wait_time, 3=goto soc2, 4=done with cycle
    timer = 0.0

    for i in range(1, total_steps):
        t = time_s[i]
        soc[i] = soc[i-1] # default rest
        power[i] = 0.0
        current[i] = 0.0
        
        if current_cycle_idx < len(cycles):
            cyc = cycles[current_cycle_idx]
            start_time_s = cyc['start_time'] * 3600
            target_soc1 = cyc['target_soc1']
            wait_time_s = cyc['wait_time'] * 3600
            target_soc2 = cyc['target_soc2']
            
            if phase == 0:
                if t >= start_time_s:
                    phase = 1
            
            if phase == 1:
                # Go to target_soc1
                diff = target_soc1 - soc[i-1]
                if abs(diff) < 0.0001:
                    phase = 2
                    timer = 0.0
                else:
                    is_charge = diff > 0
                    rate = charge_rate if is_charge else -discharge_rate
                    current_power = rate * total_energy
                    v = get_voltage(soc[i-1])
                    current_current = current_power / v
                    
                    # C model updates SOC based on power (assuming constant nominal voltage), not actual current
                    dsoc = current_power * dt / (total_energy * 3600)
                    
                    if is_charge and soc[i-1] + dsoc >= target_soc1:
                        dsoc = target_soc1 - soc[i-1]
                        current_power = dsoc * total_energy * 3600 / dt
                        current_current = current_power / v
                    elif not is_charge and soc[i-1] + dsoc <= target_soc1:
                        dsoc = target_soc1 - soc[i-1]
                        current_power = dsoc * total_energy * 3600 / dt
                        current_current = current_power / v
                    
                    soc[i] = soc[i-1] + dsoc
                    power[i] = current_power
                    current[i] = current_current
                    
            if phase == 2:
                timer += dt
                if timer >= wait_time_s:
                    phase = 3
                    
            if phase == 3:
                # Go to target_soc2
                diff = target_soc2 - soc[i-1]
                if abs(diff) < 0.0001:
                    phase = 4
                else:
                    is_charge = diff > 0
                    rate = charge_rate if is_charge else -discharge_rate
                    current_power = rate * total_energy
                    v = get_voltage(soc[i-1])
                    current_current = current_power / v
                    
                    # C model updates SOC based on power
                    dsoc = current_power * dt / (total_energy * 3600)
                    
                    if is_charge and soc[i-1] + dsoc >= target_soc2:
                        dsoc = target_soc2 - soc[i-1]
                        current_power = dsoc * total_energy * 3600 / dt
                        current_current = current_power / v
                    elif not is_charge and soc[i-1] + dsoc <= target_soc2:
                        dsoc = target_soc2 - soc[i-1]
                        current_power = dsoc * total_energy * 3600 / dt
                        current_current = current_power / v
                        
                    soc[i] = soc[i-1] + dsoc
                    power[i] = current_power
                    current[i] = current_current
            
            if phase == 4:
                current_cycle_idx += 1
                phase = 0
                
    return time_s, soc, current, power

if __name__ == "__main__":
    
    ocv_curve = pd.DataFrame({
        'soc': [0, 0.2, 0.5, 1],
        'ocv': [2.8, 3.2, 3.3, 3.4]
    })
    
    time_s, soc, current, power = generate_power_profiles_for_a_day(charge_rate=0.4,
                                                                    discharge_rate=0.5,
                                                                    n_cycles=2,
                                                                    total_energy=300*3.2,
                                                                    ocv_curve=ocv_curve,
                                                                    battery_capacity_ah=300,
                                                                    soc_init=0.2,
                                                                    starting_time=2)

    fig, axs = plt.subplots(3, 1)
    axs[0].plot(time_s/3600, soc)
    axs[1].plot(time_s/3600, current)
    axs[2].plot(time_s/3600, power)
    fig.show()