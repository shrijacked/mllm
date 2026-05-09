import time

from src.prompts import critique as cr_prompts
from src.state import append_trace


def critique_itinerary(state: dict, client) -> dict:
    t0 = time.perf_counter()
    model = getattr(client, "model", None)
    user = cr_prompts.user_prompt(
        state["itinerary_v1"],
        state["trip_spec"],
        state["weather"],
        state["activities"],
    )
    data = client.chat_json(cr_prompts.SYSTEM, user, temperature=0.2)
    for k in ("weaknesses", "missing", "pacing_issues", "budget_concerns", "factual_concerns", "strengths"):
        if k not in data or not isinstance(data[k], list):
            data[k] = []
    state["critique"] = data
    ms = int((time.perf_counter() - t0) * 1000)
    n = sum(len(data[k]) for k in data)
    append_trace(
        state,
        5,
        "critique_itinerary",
        "llm",
        model=model,
        ms=ms,
        output_summary=f"{n} critique items",
        input_keys=["itinerary_v1", "trip_spec", "weather", "activities"],
    )
    return state
