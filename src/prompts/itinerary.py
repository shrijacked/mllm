import json

SYSTEM = (
    "You are a travel itinerary writer. You schedule activities from a fixed candidate pool into "
    "day-by-day Markdown. You must not invent activities that are not in the pool. You align "
    "outdoor blocks with lower precipitation days when weather data is available. You respect "
    "pace, budget, and special_requests (for example schedule a rest afternoon if requested)."
)


def user_prompt(trip_spec: dict, weather: dict, activities: list) -> str:
    spec_s = json.dumps(trip_spec, indent=2)
    wx_s = json.dumps(weather, indent=2)
    act_s = json.dumps(activities, indent=2)
    tail = ""
    st = weather.get("status", "ok")
    if st != "ok":
        tail = (
            "\n\nWeather data is incomplete or unavailable. State **Weather:** lines using any per-day "
            "entries when present; otherwise use honest seasonal language for that month and note that the tool "
            "did not return a live forecast. Keep indoor backups visible on days that might be wet."
        )
    return (
        f"Trip specification:\n{spec_s}\n\n"
        f"Weather:\n{wx_s}{tail}\n\n"
        f"Candidate activities (use only these names and ideas from this list):\n{act_s}\n\n"
        "Write a Markdown itinerary. Required structure:\n"
        "- Title line: # {Destination} — {N}-Day Itinerary\n"
        "- One line with Dates, Travellers, Pace, Budget\n"
        "- For each day: ## Day k — {weekday, date}\n"
        "- Under each day start with **Weather:** using the forecast for that date if present; "
        "otherwise say seasonal guess.\n"
        "- Time bullets like: - 09:00 — Activity (Nh) — short reason\n"
        "- Include lunch suggestions and an **Evening:** line per day.\n"
        "Use only activities from the pool. Match duration_hours from the pool when you cite duration."
    )
