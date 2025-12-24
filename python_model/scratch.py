from python_model.preprocess.profiles import generate_current_profile_for_a_day
import numpy as np
import matplotlib.pyplot as plt

time, current = generate_current_profile_for_a_day(c_rate=0.25,
                                             n_cycles=1,
                                             rest_between_cycles=2,
                                             capacity_ah=300)


plt.figure()
plt.plot(time/3600, current)
plt.show()

print(time)
print(current)