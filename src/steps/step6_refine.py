import time

from src.prompts import refine as ref_prompts
from src.state import append_trace


def refine_itinerary(state: dict, client) -> dict:
    t0 = time.perf_counter()
    model = getattr(client, "model", None)
    user = ref_prompts.user_prompt(
        state["itinerary_v1"],
        state["critique"],
        state["weather"],
        state["activities"],
    )
    md = client.chat(ref_prompts.SYSTEM, user, temperature=0.5)
    state["itinerary_final"] = md
    ms = int((time.perf_counter() - t0) * 1000)
    append_trace(
        state,
        6,
        "refine_itinerary",
        "llm",
        model=model,
        ms=ms,
        output_summary=f"final markdown {len(md)} chars",
        input_keys=["itinerary_v1", "critique", "weather", "activities"],
    )
    return state
