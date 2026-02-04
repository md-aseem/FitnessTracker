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
                                      rest_between_cycles: float = 2,
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

    def get_voltage(soc):
        soc_bp = ocv_curve['soc'].values
        ocv_bp = ocv_curve['ocv'].values
        return np.interp(soc, soc_bp, ocv_bp)

    # initializing the counter and charge direction
    soc[:starting_rest_steps] = soc_init
    half_cycle_ah_throughput = 0
    is_charge = True
    rest_timer = 0
    cycles = 0
    half_cycle_ah_throughput_array = []

    for i in range(starting_rest_steps, total_steps):

        if cycles > n_cycles:
            break

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
            if rest_timer > rest_between_cycles:
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
                                 ocv_curve: pd.DataFrame,
                                 battery_capacity_ah: float,
                                 soc_init: float,
                                 dt: float = 1.0
                                 ):
    """
    Process a custom power profile:
    1. Interpolate power to simulation time steps (dt).
    2. Calculate Current and SOC iteratively.
    """
    
    # 1. Determine Simulation Time
    t_start = custom_time[0]
    t_end = custom_time[-1]
    duration = t_end - t_start
    
    total_steps = int(duration / dt) + 1
    time_s = np.arange(total_steps) * dt + t_start
    
    # 2. Interpolate Power
    power_watts = np.interp(time_s, custom_time, custom_power)
    
    # 3. Calculate SOC and Current
    current = np.zeros(total_steps)
    soc = np.zeros(total_steps)
    soc[0] = soc_init
    
    # OCV Interp Helpers
    ocv_soc_vals = ocv_curve.iloc[:, 0].values
    ocv_voltage_vals = ocv_curve.iloc[:, 1].values
    
    def get_voltage(s):
        v = np.interp(s, ocv_soc_vals, ocv_voltage_vals)
        return max(1.0, v)
        
    for i in range(total_steps):
        
        # Setup Current SOC
        if i > 0:
            current_soc = soc[i-1]
        else:
            current_soc = soc_init
            
        # Get Voltage & Current
        v = get_voltage(current_soc)
        
        # I = P / V
        # If P is provided, I is result.
        i_val = power_watts[i] / v
        current[i] = i_val
        
        # Update SOC for next step
        if i < total_steps - 1:
            # dSOC = - I * dt / Cap
            d_ah = -(i_val * dt / 3600.0)
            new_soc = current_soc + (d_ah / battery_capacity_ah)
            
            # Clamp SOC
            new_soc = max(0.0, min(1.0, new_soc))
            
            soc[i+1] = new_soc
            
    return time_s, soc, current, power_watts


if __name__ == "__main__":
    
    ocv_curve = pd.DataFrame({
        'soc': [0, 0.2, 0.5, 1],
        'ocv': [2.8, 3.2, 3.3, 3.4]
    })
    
    time_s, soc, current, power = generate_power_profiles_for_a_day(charge_rate=0.4,
                                                                    discharge_rate=0.8,
                                                                    n_cycles=2,
                                                                    total_energy=300*3.2,
                                                                    ocv_curve=ocv_curve,
                                                                    battery_capacity_ah=300,
                                                                    soc_init=0.0)
    
    import matplotlib.pyplot as plt

    plt.figure(figsize=(10, 5))
    plt.plot(time_s, soc)
    plt.show()