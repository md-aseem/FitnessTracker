"""
Unified weather data fetcher using Open-Meteo Historical Weather API.

A single API call fetches both hourly temperature and hourly radiation data for
a location and month. Results are cached in a single JSON file with LRU eviction.
"""
import numpy as np
import urllib.request
import urllib.parse
import json
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

# Single cache file alongside data/
_CACHE_FILE = Path(__file__).parent.parent.parent / "data" / "weather_cache.json"
_MAX_CACHE_ENTRIES = 50


@dataclass
class HistoricalWeatherData:
    """Container for historical weather data for a location and month."""
    location: str
    display_name: str
    month: int
    lat: float
    lon: float
    hourly_temperature: np.ndarray      # °C, 24 values (one per hour)
    hourly_radiation: np.ndarray        # W/m2, 24 values (one per hour)


def _cache_key(location: str, month: int) -> str:
    return f"{location.lower().strip()}:{month}"


def _load_cache() -> dict:
    """Load the entire cache file."""
    if not _CACHE_FILE.exists():
        return {}
    try:
        with open(_CACHE_FILE) as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def _save_cache(cache: dict):
    """Save the entire cache file, evicting oldest entries if over limit."""
    # Evict oldest entries if over the limit
    if len(cache) > _MAX_CACHE_ENTRIES:
        # Sort by last_accessed, keep newest
        sorted_keys = sorted(cache.keys(), key=lambda k: cache[k].get("last_accessed", 0))
        for key in sorted_keys[:len(cache) - _MAX_CACHE_ENTRIES]:
            del cache[key]

    _CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(_CACHE_FILE, "w") as f:
        json.dump(cache, f, indent=2)


def _load_from_cache(location: str, month: int) -> Optional[HistoricalWeatherData]:
    """Try to load cached weather data. Updates last_accessed on hit."""
    import time
    cache = _load_cache()
    key = _cache_key(location, month)

    if key not in cache:
        return None

    entry = cache[key]
    if "hourly_temperature" not in entry or "display_name" not in entry:
        return None  # Stale format

    # Update last_accessed timestamp
    entry["last_accessed"] = int(time.time())
    _save_cache(cache)

    return HistoricalWeatherData(
        location=entry["location"],
        display_name=entry["display_name"],
        month=entry["month"],
        lat=entry["lat"],
        lon=entry["lon"],
        hourly_temperature=np.array(entry["hourly_temperature"]),
        hourly_radiation=np.array(entry["hourly_radiation"]),
    )


def _save_to_cache(data: HistoricalWeatherData):
    """Save weather data to cache."""
    import time
    cache = _load_cache()
    key = _cache_key(data.location, data.month)

    cache[key] = {
        "location": data.location,
        "display_name": data.display_name,
        "month": data.month,
        "lat": data.lat,
        "lon": data.lon,
        "hourly_temperature": data.hourly_temperature.tolist(),
        "hourly_radiation": data.hourly_radiation.tolist(),
        "last_accessed": int(time.time()),
    }

    _save_cache(cache)


def _geocode(location_str: str) -> Optional[tuple[float, float, str]]:
    """Geocode a location string using Nominatim API.
    
    Returns (lat, lon, display_name) or None on failure.
    """
    try:
        url = f"https://nominatim.openstreetmap.org/search?q={urllib.parse.quote(location_str)}&format=json&limit=1"
        headers = {"User-Agent": "QuantumThermalModel/1.0"}
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            if data:
                return float(data[0]["lat"]), float(data[0]["lon"]), data[0].get("display_name", location_str)
    except Exception as e:
        print(f"Geocoding error: {e}")
    return None


def _fetch_weather(lat: float, lon: float, month: int):
    """Fetch hourly temperature and radiation from Open-Meteo for a single representative day.

    Uses the 15th of the given month (2023) as the representative day.
    Returns (hourly_temp_24h, hourly_radiation_24h) or (None, None) on failure.
    """
    try:
        date = f"2023-{month:02d}-15"
        url = (f"https://archive-api.open-meteo.com/v1/archive?"
               f"latitude={lat}&longitude={lon}"
               f"&start_date={date}&end_date={date}"
               f"&hourly=temperature_2m,shortwave_radiation"
               f"&timezone=auto")

        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read().decode())

            hourly = data.get("hourly", {})

            temps = hourly.get("temperature_2m", [])
            hourly_temp = np.array([t if t is not None else 25.0 for t in temps[:24]])

            rads = hourly.get("shortwave_radiation", [])
            hourly_rad = np.array([r if r is not None else 0.0 for r in rads[:24]])

        return hourly_temp, hourly_rad
    except Exception as e:
        print(f"Open-Meteo fetch error: {e}")
        return None, None


def fetch_historical_weather(location: str, month: int) -> Optional[HistoricalWeatherData]:
    """Fetch historical weather data (hourly temperature + radiation) for a location and month.

    Results are cached locally in a single file. Subsequent calls for the same
    location+month return instantly from disk. Cache is capped at 50 entries
    with LRU eviction.
    """
    # Check cache first
    cached = _load_from_cache(location, month)
    if cached is not None:
        print(f"Using cached weather data for {cached.display_name}, month {month}")
        print(f"  Temperature range: {np.min(cached.hourly_temperature):.1f}–{np.max(cached.hourly_temperature):.1f}°C")
        print(f"  Peak Radiation: {np.max(cached.hourly_radiation):.1f} W/m2")
        return cached

    print(f"Fetching historical weather data for {location}, month {month}...")

    geo = _geocode(location)
    if not geo:
        print(f"Location not found: {location}")
        return None

    lat, lon, display_name = geo
    print(f"  Resolved: {display_name}")

    hourly_temp, hourly_rad = _fetch_weather(lat, lon, month)

    if hourly_temp is None and hourly_rad is None:
        return None

    result = HistoricalWeatherData(
        location=location,
        display_name=display_name,
        month=month,
        lat=lat,
        lon=lon,
        hourly_temperature=hourly_temp if hourly_temp is not None else np.full(24, 25.0),
        hourly_radiation=hourly_rad if hourly_rad is not None else np.zeros(24),
    )

    _save_to_cache(result)

    print(f"  Temperature range: {np.min(result.hourly_temperature):.1f}–{np.max(result.hourly_temperature):.1f}°C")
    print(f"  Peak Radiation: {np.max(result.hourly_radiation):.1f} W/m2")

    return result
