import numpy as np
from matplotlib import pyplot as plt
import urllib.request
import urllib.parse
import json
import math


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


def geocode_location(location_str: str):
    """Geocode a location string using Nominatim API."""
    try:
        url = f"https://nominatim.openstreetmap.org/search?q={urllib.parse.quote(location_str)}&format=json&limit=1"
        headers = {"User-Agent": "QuantumThermalModel/1.0"}
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            if data:
                return float(data[0]["lat"]), float(data[0]["lon"])
            else:
                print(f"Location not found: {location_str}")
                return None
    except Exception as e:
        print(f"Geocoding error: {e}")
        return None


def fetch_solar_data(lat: float, lon: float, month: int):
    """Fetch monthly average solar radiation from PVGIS."""
    try:
        url = f"https://re.jrc.ec.europa.eu/api/v5_2/PVcalc?lat={lat}&lon={lon}&peakpower=1&loss=14&slope=0&outputformat=json"
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read().decode())
            monthly_data = data.get("outputs", {}).get("monthly", {}).get("fixed", [])
            if not monthly_data:
                print(f"No solar data found for lat={lat}, lon={lon}")
                return None
            
            # Month is 1-indexed
            if 1 <= month <= len(monthly_data):
                entry = monthly_data[month - 1]
                # H(i)_d is average daily irradiation in kWh/m2/day
                avg_daily_kwh_m2 = entry.get("H(i)_d")
                return avg_daily_kwh_m2
            else:
                print(f"Month {month} not found in PVGIS data")
                return None
    except Exception as e:
        print(f"PVGIS error: {e}")
        return None


def calculate_sunrise_sunset(lat: float, month: int):
    """Calculate approximate sunrise and sunset times (local solar time)."""
    # Approximate day of year for the middle of the month
    day_of_year = (month - 1) * 30 + 15
    
    # Simple solar geometry
    lat_rad = math.radians(lat)
    delta = 23.45 * math.sin(math.radians(360 / 365 * (284 + day_of_year)))
    delta_rad = math.radians(delta)
    
    # Hour angle at sunrise/sunset
    cos_ws = -math.tan(lat_rad) * math.tan(delta_rad)
    cos_ws = max(-1, min(1, cos_ws))  # Clamp for extreme latitudes
    
    ws_deg = math.degrees(math.acos(cos_ws))
    delta_t = ws_deg / 15.0  # Hours from solar noon
    
    sunrise = 12 - delta_t
    sunset = 12 + delta_t
    
    return round(sunrise, 2), round(sunset, 2)


def generate_historical_radiation_profile(location: str, month: int, dt: float = 1):
    """Get max radiation and sunrise/sunset for a location and month, then generate profile."""
    print(f"Fetching radiation data for {location}, month {month}...")
    
    geo = geocode_location(location)
    if not geo:
        return None, None
    
    lat, lon = geo
    avg_daily_kwh_m2 = fetch_solar_data(lat, lon, month)
    if avg_daily_kwh_m2 is None:
        return None, None
    
    sunrise, sunset = calculate_sunrise_sunset(lat, month)
    duration = sunset - sunrise
    
    # peak_rad = 1.5 * total_energy / duration (from parabolic integral)
    # total_energy is in kWh/m2/day, we want peak in W/m2
    # peak_rad = 1.5 * (avg_daily_kwh_m2 * 1000) / duration
    peak_rad = 1.5 * (avg_daily_kwh_m2 * 1000) / duration
    
    print(f"Fetched: Peak Rad={peak_rad:.1f} W/m2, Sunrise={sunrise}, Sunset={sunset}")
    
    # We use the same generation logic but with these specific values
    return generate_radiation_load_for_a_day(max_radiation=int(peak_rad), 
                                             sunrise_time=sunrise, 
                                             sunset_time=sunset, 
                                             dt=dt)


if __name__ == "__main__":
    # Test
    time_s, radiation = generate_historical_radiation_profile("London", 6)
    if time_s is not None:
        plt.figure()
        plt.plot(time_s / 3600, radiation)
        plt.title("Radiation Profile for London in June")
        plt.xlabel("Hour")
        plt.ylabel("Radiation (W/m2)")
        plt.show()
    else:
        print("Failed to generate historical profile.")