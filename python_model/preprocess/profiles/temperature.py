import numpy as np

def generate_ambient_temp_profile_for_a_day(constant_temp: int | float = 25, dt: float = 1.0):

    SECONDS_IN_DAY = 86400
    total_steps = int(SECONDS_IN_DAY / dt) + 1

    time_s = np.arange(total_steps) * dt
    temp_profile = np.ones_like(time_s) * constant_temp

    return time_s, temp_profile
