import numpy as np

def generate_ambient_temp_profile_for_a_day(constant_temp: int | float = 25):

    SECONDS_IN_DAY = 86400 + 1

    time_s = np.arange(SECONDS_IN_DAY) / SECONDS_IN_DAY
    temp_profile = np.ones_like(time_s) * constant_temp

    return time_s, temp_profile
