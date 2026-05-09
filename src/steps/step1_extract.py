import time

from src.prompts import extract as extract_prompts
from src.state import append_trace

_SCHEMA = """{
  "valid": true or false,
  "reason_invalid": null or string,
  "destination": string,
  "start_date": "YYYY-MM-DD",
  "end_date": "YYYY-MM-DD",
  "duration_days": number,
  "traveler_count": number,
  "interests": [strings],
  "pace": string,
  "budget_tier": string,
  "special_requests": [strings]
}"""


def _validate_spec(spec: dict) -> None:
    if not spec.get("valid", True):
        return
    for k in ("destination", "start_date", "end_date", "duration_days"):
        if k not in spec or spec[k] in (None, ""):
            raise ValueError(f"trip_spec missing required field: {k}")
    d = int(spec["duration_days"])
    if d < 1 or d > 21:
        raise ValueError("duration_days must be between 1 and 21")
    if spec["start_date"] > spec["end_date"]:
        raise ValueError("start_date must be on or before end_date")


def extract_trip_spec(state: dict, client) -> dict:
    t0 = time.perf_counter()
    user = extract_prompts.user_prompt(state["user_query"], state["today"])
    model = getattr(client, "model", None)
    try:
        spec = client.chat_json(
            extract_prompts.SYSTEM,
            user,
            temperature=0.2,
            schema_hint=_SCHEMA,
        )
    except Exception as e:
        ms = int((time.perf_counter() - t0) * 1000)
        append_trace(
            state,
            1,
            "extract_trip_spec",
            "llm",
            model=model,
            ms=ms,
            error=str(e),
            output_summary="json parse or api failure",
            input_keys=["user_query", "today"],
        )
        raise

    state["trip_spec"] = spec
    ms = int((time.perf_counter() - t0) * 1000)
    try:
        _validate_spec(spec)
    except ValueError as e:
        append_trace(
            state,
            1,
            "extract_trip_spec",
            "llm",
            model=model,
            ms=ms,
            error=str(e),
            output_summary="trip_spec validation failed",
            input_keys=["user_query", "today"],
        )
        raise
    summ = "valid=false" if not spec.get("valid", True) else spec.get("destination", "")[:120]
    append_trace(
        state,
        1,
        "extract_trip_spec",
        "llm",
        model=model,
        ms=ms,
        output_summary=summ,
        input_keys=["user_query", "today"],
    )
    return state
