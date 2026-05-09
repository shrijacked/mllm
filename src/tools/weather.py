import logging
from datetime import date, timedelta
from typing import Optional

import requests

log = logging.getLogger(__name__)

_TIMEOUT = 10

_WMO = {
    0: "Clear",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Drizzle",
    55: "Dense drizzle",
    56: "Freezing drizzle",
    57: "Dense freezing drizzle",
    61: "Slight rain",
    63: "Rain",
    65: "Heavy rain",
    66: "Freezing rain",
    67: "Heavy freezing rain",
    71: "Slight snow",
    73: "Snow",
    75: "Heavy snow",
    77: "Snow grains",
    80: "Slight rain showers",
    81: "Rain showers",
    82: "Violent rain showers",
    85: "Slight snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}


def _summary_from_code(code: int) -> str:
    return _WMO.get(int(code), "Mixed conditions")


def _geocode(destination: str) -> Optional[dict]:
    url = "https://geocoding-api.open-meteo.com/v1/search"
    params = {"name": destination.strip(), "count": 10, "language": "en", "format": "json"}
    try:
        r = requests.get(url, params=params, timeout=_TIMEOUT)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        log.warning("geocode failed: %s", e)
        return None

    results = data.get("results") or []
    if not results:
        return {"_empty": True}

    if "," in destination:
        hint = destination.split(",", 1)[1].strip().lower()
        for row in results:
            country = (row.get("country") or "").lower()
            admin1 = (row.get("admin1") or "").lower()
            if hint and (hint in country or hint in admin1 or country.startswith(hint)):
                return row
    return results[0]


def _build_days(daily: dict) -> list:
    dates = daily.get("time") or []
    highs = daily.get("temperature_2m_max") or []
    lows = daily.get("temperature_2m_min") or []
    precips = daily.get("precipitation_probability_max") or []
    codes = daily.get("weather_code") or []
    days = []
    for i, d in enumerate(dates):
        hi = highs[i] if i < len(highs) else None
        lo = lows[i] if i < len(lows) else None
        pr = precips[i] if i < len(precips) else None
        code = codes[i] if i < len(codes) else 0
        days.append(
            {
                "date": d,
                "high_c": int(round(hi)) if hi is not None else None,
                "low_c": int(round(lo)) if lo is not None else None,
                "precip_chance": int(pr) if pr is not None else 0,
                "summary": _summary_from_code(int(code) if code is not None else 0),
            }
        )
    return days


def get_destination_weather(destination: str, start_date: str, end_date: str) -> dict:
    today = date.today()
    trip_start = date.fromisoformat(start_date)
    trip_end = date.fromisoformat(end_date)
    horizon_end = today + timedelta(days=16)

    geo = _geocode(destination)
    if geo is None:
        return {"status": "unavailable", "reason": "geocoding request failed"}
    if geo.get("_empty"):
        return {
            "status": "unresolved_destination",
            "reason": f"Open-Meteo could not locate '{destination}'",
        }

    lat = geo.get("latitude")
    lon = geo.get("longitude")
    name = geo.get("name") or ""
    country = geo.get("country") or ""
    resolved = f"{name}, {country}".strip(", ")

    if lat is None or lon is None:
        return {"status": "unavailable", "reason": "geocoding returned no coordinates"}

    if trip_start > horizon_end:
        return {
            "status": "out_of_window",
            "destination_resolved": resolved,
            "lat": lat,
            "lon": lon,
            "days": [],
            "reason": "Forecast only available within about 16 days from today; trip start is beyond that window.",
        }

    fetch_start = max(trip_start, today)
    fetch_end = min(trip_end, horizon_end)
    if fetch_start > fetch_end:
        return {
            "status": "out_of_window",
            "destination_resolved": resolved,
            "lat": lat,
            "lon": lon,
            "days": [],
            "reason": "No forecastable dates overlap the trip window.",
        }

    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_max,weather_code",
        "start_date": fetch_start.isoformat(),
        "end_date": fetch_end.isoformat(),
        "timezone": "auto",
    }
    try:
        r = requests.get(url, params=params, timeout=_TIMEOUT)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        return {"status": "unavailable", "reason": type(e).__name__}

    daily = data.get("daily") or {}
    days = _build_days(daily)

    if trip_end > horizon_end:
        n = len(days)
        return {
            "status": "out_of_window",
            "destination_resolved": resolved,
            "lat": lat,
            "lon": lon,
            "days": days,
            "reason": (
                f"Forecast only available for the first {n} day(s) of the trip within the 16-day horizon; "
                "remaining days will use seasonal expectations."
            ),
        }

    return {
        "status": "ok",
        "destination_resolved": resolved,
        "lat": lat,
        "lon": lon,
        "days": days,
    }
