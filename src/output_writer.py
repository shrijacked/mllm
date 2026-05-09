import json
import os
from datetime import datetime

from src.state import slug_from_state


def write_outputs(state: dict, outdir: str = "outputs") -> tuple[str, str]:
    os.makedirs(outdir, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%dT%H%M%S")
    slug = slug_from_state(state)
    base = f"{slug}_{ts}"
    md_path = os.path.join(outdir, f"itinerary_{base}.md")
    json_path = os.path.join(outdir, f"state_{base}.json")
    trip = state.get("trip_spec") or {}
    if trip.get("valid") is False:
        reason = trip.get("reason_invalid") or "Invalid trip description."
        body = f"## Trip could not be planned\n\n{reason}"
    else:
        body = state.get("itinerary_final") or "## Itinerary\n\nNot generated."
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(body)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)
    return md_path, json_path
