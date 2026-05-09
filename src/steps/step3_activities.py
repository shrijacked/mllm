import json
import time

from src.prompts import activities as act_prompts
from src.state import append_trace


def recommend_activities(state: dict, client) -> dict:
    t0 = time.perf_counter()
    model = getattr(client, "model", None)
    user = act_prompts.user_prompt(state["trip_spec"], state["weather"])
    data = client.chat_json(act_prompts.SYSTEM, user, temperature=0.5)
    acts = data.get("activities")
    if not isinstance(acts, list) or len(acts) < 12:
        raise ValueError("activities must be a list of at least 12 items")
    if len(acts) > 20:
        acts = acts[:20]
    state["activities"] = acts
    ms = int((time.perf_counter() - t0) * 1000)
    append_trace(
        state,
        3,
        "recommend_activities",
        "llm",
        model=model,
        ms=ms,
        output_summary=f"{len(acts)} activities",
        input_keys=["trip_spec", "weather"],
    )
    return state
