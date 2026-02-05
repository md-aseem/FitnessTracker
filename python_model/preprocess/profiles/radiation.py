import numpy as np
from matplotlib import pyplot as plt


def generate_radiation_load_for_a_day(max_radiation: int = 170, sunrise_time: int = 7, sunset_time: int= 19 , dt: float = 1):

    SECONDS_IN_DAY = 86400
    total_steps = int(SECONDS_IN_DAY / dt) + 1

    # Initialize full day arrays
    time_s = np.arange(total_steps) * dt
    time_hr = time_s / 3600

    if sunset_time > sunrise_time:
        x = time_hr - (0.5 * (sunrise_time + sunset_time))
        half_duration = 0.5*(sunset_time - sunrise_time)
        radiation = 850.0 * (1 - (x * x / (half_duration * half_duration)));
        radiation = np.clip(radiation, 0, max_radiation)

    else: # no radiation
        print(f"No radiation load because sunrise_time = {sunrise_time}, sunset_time = {sunset_time}")
        radiation = np.zeros_like(time_s)

    return time_s, radiation


if __name__ == "__main__":
    time_s, radiation = generate_radiation_load_for_a_day()

    plt.figure()
    plt.plot(time_s / 3600, radiation)
    plt.show()

    pass