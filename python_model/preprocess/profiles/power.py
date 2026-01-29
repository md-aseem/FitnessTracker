import numpy as np

def generate_power_profile_for_a_day(cp_rate: float,
                             n_cycles: int,
                             total_energy: float,
                             rest_between_cycles: float = 2,
                             start_with_rest: bool = True,
                             start_with_charge: bool = True,
                             starting_time: int = 4, # 24 hour timezone
                             dt: float = 1.0 
                             ) -> tuple[np.ndarray, np.ndarray]:

    SECONDS_IN_DAY = 86400
    total_steps = int(SECONDS_IN_DAY / dt) + 1
    
    # Initialize full day arrays
    time_s = np.arange(total_steps) * dt
    power_watts = np.zeros(total_steps)

    # Calculate durations in seconds
    t_discharge = (1.0 / cp_rate) * 3600
    t_charge = (1.0 / cp_rate) * 3600
    t_rest = rest_between_cycles * 3600

    # Calculate power magnitudes
    # Power = CP_rate * Total Energy
    p_discharge = cp_rate * total_energy
    p_charge = -cp_rate * total_energy

    # Generate profile segments
    seg_discharge = np.full(int(t_discharge / dt), p_discharge)
    seg_charge = np.full(int(t_charge / dt), p_charge)
    seg_rest = np.zeros(int(t_rest / dt))

    # Construct one cycle based on start_with_charge preference
    # Default cycle (start_with_charge=False): Discharge -> Rest -> Charge -> Rest
    # Charge cycle (start_with_charge=True): Charge -> Rest -> Discharge -> Rest
    if start_with_charge:
        one_cycle = np.concatenate([seg_charge, seg_rest, seg_discharge, seg_rest])
    else:
        one_cycle = np.concatenate([seg_discharge, seg_rest, seg_charge, seg_rest])

    # Repeat for the specified number of cycles
    sequence = np.tile(one_cycle, int(n_cycles))

    # Prepend rest if requested
    if start_with_rest:
        sequence = np.concatenate([seg_rest, sequence])
        
    # Insert sequence into the day profile at the correct starting time
    start_idx = int(starting_time * 3600 / dt)
    
    if start_idx < total_steps:
        # Determine how much of the sequence fits in the remaining day
        points_to_fill = min(len(sequence), total_steps - start_idx)
        power_watts[start_idx : start_idx + points_to_fill] = sequence[:points_to_fill]

    return time_s, power_watts
