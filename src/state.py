import re
from datetime import date


def init_state(user_query: str) -> dict:
    return {
        "user_query": user_query,
        "today": date.today().isoformat(),
        "trip_spec": None,
        "weather": None,
        "activities": None,
        "itinerary_v1": None,
        "critique": None,
        "itinerary_final": None,
        "trace": [],
    }


def append_trace(
    state,
    step_num,
    name,
    kind,
    *,
    model=None,
    ms=0,
    error=None,
    output_summary="",
    input_keys=None,
):
    if input_keys is None:
        input_keys = []
    s = output_summary if len(output_summary) <= 200 else output_summary[:197] + "..."
    state["trace"].append(
        {
            "step": step_num,
            "name": name,
            "kind": kind,
            "model": model,
            "input_keys": list(input_keys),
            "output_summary": s,
            "ms": ms,
            "error": error,
        }
    )


def slug_from_state(state) -> str:
    spec = state.get("trip_spec") or {}
    if spec.get("valid") is False:
        raw = (spec.get("reason_invalid") or state.get("user_query") or "invalid")[:48]
        slug = re.sub(r"[^a-z0-9]+", "-", raw.lower()).strip("-")
        return (slug or "invalid")[:80]
    dest = spec.get("destination") or "unknown"
    sd = spec.get("start_date") or "nodate"
    raw = f"{dest}-{sd}".lower()
    slug = re.sub(r"[^a-z0-9]+", "-", raw).strip("-")
    return (slug or "trip")[:80]
