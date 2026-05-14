import numpy as np
import pandas as pd
from functools import lru_cache
from scipy.interpolate import LinearNDInterpolator, NearestNDInterpolator
from scipy.stats import t as student_t

# Constants from aging_actual.py
CYCLIC_PARAMS = [
    {
        "cell_id": "CAT001E", "DOD": 0.8, "Temp_C": 20.0,
        "C_hat": 0.000267255835031656, "C_lo": 0.0002592796358088172, "C_hi": 0.0002752320342544948,
        "sigma2_hat": 1.8331682375025935e-05, "szz": 2144986.8127327925, "dof": 34, "y_shared": 0.717207,
    },
    {
        "cell_id": "CAT008E", "DOD": 1.0, "Temp_C": 35.0,
        "C_hat": 0.00045007506109562864, "C_lo": 0.0004421543456418417, "C_hi": 0.0004579957765494156,
        "sigma2_hat": 1.0521286508964683e-05, "szz": 1321687.2955858344, "dof": 23, "y_shared": 0.717207,
    },
    {
        "cell_id": "CAT007E", "DOD": 1.0, "Temp_C": 20.0,
        "C_hat": 0.0003189126785489749, "C_lo": 0.0003120614655202596, "C_hi": 0.0003257638915776902,
        "sigma2_hat": 2.4493406047039566e-05, "szz": 3836647.5809421404, "dof": 38, "y_shared": 0.717207,
    },
    {
        "cell_id": "CAT005E", "DOD": 0.6, "Temp_C": 15.0,
        "C_hat": 0.00019644190777641984, "C_lo": 0.00019034101139242922, "C_hi": 0.00020254280416041046,
        "sigma2_hat": 7.560469469113276e-06, "szz": 1550978.3597915806, "dof": 28, "y_shared": 0.717207,
    },
    {
        "cell_id": "CAT011E", "DOD": 0.6, "Temp_C": 35.0,
        "C_hat": 0.00018586801888646702, "C_lo": 0.00017325984188664204, "C_hi": 0.000198476195886292,
        "sigma2_hat": 2.0802773957236737e-06, "szz": 131442.5172950472, "dof": 10, "y_shared": 0.717207,
    },
]
Y_SHARED = CYCLIC_PARAMS[0]["y_shared"]
PI_ALPHA = 0.01

calendar_coeff = {
    "S0_hat": 1.0266519800458012,
    "C1_hat": 0.016301049825725018,
    "C2_hat": 0.06682143342801454,
    "C3_hat": 9.999999999996593e-05,
}

S0 = calendar_coeff["S0_hat"]
C1 = calendar_coeff["C1_hat"]
C2 = calendar_coeff["C2_hat"]
C3 = calendar_coeff["C3_hat"]
max_cal_val = 1.0265519800458012

class DegradationModel:
    """
    Advanced battery degradation model based on actual test data and Arrhenius physics.
    Adapted from aging_actual.py.
    """
    def __init__(self):
        self.df_params = pd.DataFrame(CYCLIC_PARAMS)
        self.interp_map = self._build_interpolators(self.df_params)

    def _build_single_interpolator(self, Xs: np.ndarray, values: np.ndarray):
        lin = LinearNDInterpolator(Xs, values, fill_value=np.nan, rescale=False)
        nn = NearestNDInterpolator(Xs, values)
        return lin, nn

    def _build_interpolators(self, df_params: pd.DataFrame):
        Xs = df_params[["Temp_C", "DOD"]].to_numpy(dtype=float)

        def col_or_fallback(col_name: str, fallback: str | float):
            if col_name in df_params.columns:
                return df_params[col_name].to_numpy(dtype=float)
            if isinstance(fallback, str):
                return df_params[fallback].to_numpy(dtype=float)
            return np.full(len(df_params), float(fallback), dtype=float)

        values_map = {
            "C_hat": col_or_fallback("C_hat", 0.0),
            "C_lo": col_or_fallback("C_lo", "C_hat"),
            "C_hi": col_or_fallback("C_hi", "C_hat"),
            "sigma2_hat": col_or_fallback("sigma2_hat", 0.0),
            "szz": col_or_fallback("szz", 1.0),
            "dof": col_or_fallback("dof", 2.0),
        }

        return {name: self._build_single_interpolator(Xs, vals) for name, vals in values_map.items()}

    def _interp(self, name: str, temp: float, dod: float) -> float:
        Xqs = np.array([[temp, dod]], dtype=float)
        lin, nn = self.interp_map[name]
        value = lin(Xqs)[0]
        if np.isnan(value):
            value = nn(Xqs)[0]
        return float(value)

    @lru_cache(maxsize=64)
    def _tcrit_from_dof(self, dof: int) -> float:
        return float(student_t.ppf(1.0 - PI_ALPHA / 2.0, max(int(dof), 2)))

    def _calendar_update(self, soh_cyclic_updated: float, delta_calendar_time: float, scale: float) -> float:
        delta_calendar_time_in_months = delta_calendar_time / (24 * 30)
        # Avoid division by zero and log of zero if soh is 1.0 and S0 is slightly different
        inner = (S0 - (soh_cyclic_updated * max_cal_val) - C3 * scale) / C1
        time_from_bol_in_months = (inner ** 2 / scale) if inner > 0 else 0.0
        
        calendar_time_updated_in_months = time_from_bol_in_months + delta_calendar_time_in_months

        soh_calendar_updated = (
            S0 - C1 * np.sqrt(np.maximum(calendar_time_updated_in_months, 0.0) * scale) - C3 * scale
        ) / max_cal_val
        return float(soh_calendar_updated)

    def update_soh(self, initial_soh: float, avg_cp_rate: float, max_temperature: float, max_soc: float, time_hours: float) -> float:
        """
        Calculates the new SOH after a time step.
        
        initial_soh: Starting SOH (0.0 to 1.0)
        avg_cp_rate: Average C-rate during the period
        max_temperature: Peak/Representative temperature in Celsius
        max_soc: Peak SOC during the period (0.0 to 1.0)
        time_hours: Duration of the step in hours
        """
        scale = np.exp(C2 * (max_temperature - 25.0))
        cp_rate = abs(avg_cp_rate)
        max_cp_rate = 0.5
        
        # Calculate split between cycling and calendar aging
        delta_cycling_time = time_hours * min(1.0, (cp_rate / max_cp_rate))
        delta_calendar_time = max(0.0, time_hours - delta_cycling_time)

        delta_cycling_cycles = delta_cycling_time * max_cp_rate / 2

        # Interpolate cyclic parameters
        c_hat = max(self._interp("C_hat", max_temperature, max_soc), 1e-16)

        # Back-calculate current "cycle number" based on initial_soh
        fade_seed = max(1.0 - float(initial_soh), 0.0)
        cycle_number = (fade_seed / c_hat) ** (1.0 / Y_SHARED)
        cycle_number_updated = cycle_number + delta_cycling_cycles
        z_eval = cycle_number_updated**Y_SHARED

        # Cyclic portion of SOH
        soh_cyclic_hat = 1.0 - c_hat * z_eval

        # Final combined SOH including calendar aging
        soh_point = self._calendar_update(soh_cyclic_hat, delta_calendar_time, scale)
        
        return float(np.clip(soh_point, 0.0, 1.0))
