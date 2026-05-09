import json

SYSTEM = (
    "You revise travel itineraries in Markdown. You address every critique item while keeping "
    "what worked. You only use activities from the provided pool. You end with a ## Notes section "
    "that explains which weather days influenced outdoor versus indoor scheduling."
)


def user_prompt(itinerary_v1: str, critique: dict, weather: dict, activities: list) -> str:
    return (
        f"Draft itinerary:\n{itinerary_v1}\n\n"
        f"Critique (JSON):\n{json.dumps(critique, indent=2)}\n\n"
        f"Weather:\n{json.dumps(weather, indent=2)}\n\n"
        f"Activity pool (do not add venues outside this set):\n{json.dumps(activities, indent=2)}\n\n"
        "Produce the final Markdown itinerary. Same heading and day structure as the draft. "
        "Address every entry in weaknesses, missing, pacing_issues, budget_concerns, and factual_concerns. "
        "Preserve strengths where they still apply. Close with ## Notes listing how forecasted "
        "weather (or its absence) drove scheduling choices."
    )
