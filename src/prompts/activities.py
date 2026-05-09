import json

SYSTEM = (
    "You are a travel planner specialising in personalised, well-paced itineraries. "
    "Given a trip specification and a weather forecast, you produce a candidate pool of "
    "activities matched to the traveller's interests, pace, and budget. You output strict JSON only."
)


def user_prompt(trip_spec: dict, weather: dict) -> str:
    spec_s = json.dumps(trip_spec, indent=2)
    wx_s = json.dumps(weather, indent=2)
    tail = ""
    st = weather.get("status", "ok")
    if st != "ok":
        tail = (
            f"\n\nWeather status is \"{st}\". Reason: {weather.get('reason', '')}. "
            "Use seasonal norms for this destination and month. Prefer indoor options in notes where rain is plausible. "
            "If only partial daily forecasts exist, trust those days for outdoor timing and mark the rest as uncertain."
        )
    return (
        f"Trip specification (JSON):\n{spec_s}\n\n"
        f"Weather tool output (JSON):\n{wx_s}\n"
        f"{tail}\n\n"
        "Produce exactly one JSON object with a single key \"activities\" whose value is an array of "
        "12 to 20 activity objects (no fewer, no more). Each activity must have: "
        "name (string), type (string), duration_hours (number), indoor_outdoor (\"indoor\"|\"outdoor\"|\"both\"), "
        "weather_sensitivity (\"low\"|\"medium\"|\"high\"), best_time (string), est_cost_tier (string), notes (string). "
        "Mix indoor and outdoor in proportion to forecast precipitation where weather.days exists. "
        "Cover every interest in trip_spec.interests at least twice across the pool. "
        "Honour budget_tier (no luxury-only ideas for mid budget). Do not assign days or times to days; "
        "this is only a candidate pool."
    )
