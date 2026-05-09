import time

from src.state import append_trace
from src.tools.weather import get_destination_weather


def fetch_weather(state: dict) -> dict:
    t0 = time.perf_counter()
    spec = state["trip_spec"]
    dest = spec["destination"]
    start = spec["start_date"]
    end = spec["end_date"]
    weather = get_destination_weather(dest, start, end)
    state["weather"] = weather
    ms = int((time.perf_counter() - t0) * 1000)
    summ = f"{weather.get('status')} {len(weather.get('days') or [])}d"
    append_trace(
        state,
        2,
        "fetch_weather",
        "tool",
        model=None,
        ms=ms,
        output_summary=summ,
        input_keys=["trip_spec.destination", "trip_spec.start_date", "trip_spec.end_date"],
    )
    return state
