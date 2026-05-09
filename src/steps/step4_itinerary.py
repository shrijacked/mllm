import time

from src.prompts import itinerary as it_prompts
from src.state import append_trace


def build_itinerary(state: dict, client) -> dict:
    t0 = time.perf_counter()
    model = getattr(client, "model", None)
    user = it_prompts.user_prompt(state["trip_spec"], state["weather"], state["activities"])
    md = client.chat(it_prompts.SYSTEM, user, temperature=0.5)
    state["itinerary_v1"] = md
    ms = int((time.perf_counter() - t0) * 1000)
    append_trace(
        state,
        4,
        "build_itinerary",
        "llm",
        model=model,
        ms=ms,
        output_summary=f"markdown {len(md)} chars",
        input_keys=["trip_spec", "weather", "activities"],
    )
    return state
