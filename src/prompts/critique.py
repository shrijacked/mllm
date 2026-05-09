import json

SYSTEM = (
    "You critique travel itineraries only. You do not rewrite the itinerary. "
    "Be specific: reference the day, time, or section you mean. Output strict JSON only."
)


def user_prompt(itinerary_md: str, trip_spec: dict, weather: dict, activities: list) -> str:
    return (
        f"Itinerary (Markdown):\n{itinerary_md}\n\n"
        f"Trip specification:\n{json.dumps(trip_spec, indent=2)}\n\n"
        f"Weather:\n{json.dumps(weather, indent=2)}\n\n"
        f"Activity pool:\n{json.dumps(activities, indent=2)}\n\n"
        "Return one JSON object with keys: weaknesses, missing, pacing_issues, budget_concerns, "
        "factual_concerns, strengths — each an array of strings (use empty arrays if none). "
        "factual_concerns should flag activities or venues that were not in the original activity pool."
    )
