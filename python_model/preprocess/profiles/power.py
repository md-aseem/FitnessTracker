import numpy as np
import pandas as pd

def generate_power_profiles_for_a_day(cp_rate: float,
                                      n_cycles: int,
                                      total_energy: float,
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
    power_watts = np.zeros(total_steps)
    current = np.zeros(total_steps)
    soc = np.zeros(total_steps)
    
    # Initialization
    soc[0] = soc_init
    
    # Power Magnitudes
    p_discharge = cp_rate * total_energy
    p_charge = -cp_rate * total_energy
    
    # Throughput Targets (Ah)
    # 1 Cycle = 2 * Capacity (Charge fully + Discharge fully)
    target_throughput_ah = n_cycles * 2.0 * battery_capacity_ah
    cumulative_throughput_ah = 0.0
    
    # State Machine Constants
    STATE_CHARGE = 1
    STATE_DISCHARGE = 2
    STATE_REST = 3
    
    # Initial State
    current_state = STATE_CHARGE
    next_state_after_rest = STATE_DISCHARGE # If we hit limit in Charge, we go to Discharge
    
    steps_in_rest = 0
    rest_duration_steps = int(rest_between_cycles * 3600 / dt)
    start_delay_steps = int(starting_time * 3600 / dt)
    
    # Performance optimization: pre-fetch arrays
    ocv_soc_vals = ocv_curve.iloc[:, 0].values
    ocv_voltage_vals = ocv_curve.iloc[:, 1].values
    
    # Helper to clean code
    def get_voltage(s):
        v = np.interp(s, ocv_soc_vals, ocv_voltage_vals)
        return max(1.0, v) # safety
    
    # Main Loop
    for i in range(total_steps):
        
        # 1. Setup Step
        # If not first step, propagate SOC from previous
        if i > 0:
            current_soc = soc[i-1]
        else:
            current_soc = soc_init
            
        # 2. Check Start Delay
        if i < start_delay_steps:
            power_watts[i] = 0.0
            current[i] = 0.0
            if i < total_steps - 1: soc[i+1] = current_soc
            continue
            
        # 3. Check Completion
        if cumulative_throughput_ah >= target_throughput_ah:
            power_watts[i] = 0.0
            current[i] = 0.0
            if i < total_steps - 1: soc[i+1] = current_soc
            continue
            
        # 4. State Machine Logic
        
        step_power = 0.0
        step_current = 0.0
        
        if current_state == STATE_REST:
            step_power = 0.0
            step_current = 0.0
            steps_in_rest += 1
            
            if steps_in_rest >= rest_duration_steps:
                current_state = next_state_after_rest
                steps_in_rest = 0
                
        elif current_state == STATE_CHARGE:
            # Check Limits first
            if current_soc >= 1.0:
                current_state = STATE_REST
                next_state_after_rest = STATE_DISCHARGE
                steps_in_rest = 0 # Start rest immediately
                # No power this step? or treat as first step of rest?
                # Treat as transition/rest, so 0 power.
                step_power = 0.0
                step_current = 0.0
            else:
                step_power = p_charge
                v = get_voltage(current_soc)
                step_current = step_power / v
                
        elif current_state == STATE_DISCHARGE:
            # Check Limits first
            if current_soc <= 0.0:
                current_state = STATE_REST
                next_state_after_rest = STATE_CHARGE
                steps_in_rest = 0
                step_power = 0.0
                step_current = 0.0
            else:
                step_power = p_discharge
                v = get_voltage(current_soc)
                step_current = step_power / v
        
        # 5. Apply & Update
        power_watts[i] = step_power
        current[i] = step_current
        
        # Update SOC
        if i < total_steps - 1:
            # soc_change = - (I * dt / 3600) / Cap
            d_ah = -(step_current * dt / 3600.0) # Amp-Hours (signed)
            
            new_soc = current_soc + (d_ah / battery_capacity_ah)
            new_soc = max(0.0, min(1.0, new_soc)) # Clamp
            soc[i+1] = new_soc
            
            # Accumulate Throughput (Absolute Ah)
            cumulative_throughput_ah += abs(d_ah)

    return time_s, soc, current, power_watts


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
