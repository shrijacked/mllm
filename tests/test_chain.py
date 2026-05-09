import json

import pytest

from src.chain import run
from src.output_writer import write_outputs
from src.state import init_state
from src.steps import step3_activities, step5_critique


def activity(n):
    return {
        "name": f"Activity {n}",
        "type": "sightseeing",
        "duration_hours": 1.0,
        "indoor_outdoor": "both",
        "weather_sensitivity": "low",
        "best_time": "morning",
        "est_cost_tier": "mid",
        "notes": "Simple demo activity.",
    }


class FakeClient:
    model = "fake-model"

    def __init__(self, *, valid=True, activity_count=12):
        self.valid = valid
        self.activity_count = activity_count
        self.json_prompts = []
        self.text_prompts = []

    def chat_json(self, system, user, **kwargs):
        self.json_prompts.append(user)
        if "free-text trip description" in system:
            if not self.valid:
                return {
                    "valid": False,
                    "reason_invalid": "Input does not describe a trip.",
                }
            return {
                "valid": True,
                "reason_invalid": None,
                "destination": "Lisbon, Portugal",
                "start_date": "2026-05-08",
                "end_date": "2026-05-09",
                "duration_days": 2,
                "traveler_count": 2,
                "interests": ["food", "history"],
                "pace": "moderate",
                "budget_tier": "mid",
                "special_requests": ["one rest afternoon"],
            }
        if "candidate pool" in system:
            return {"activities": [activity(i) for i in range(self.activity_count)]}
        if "critique travel itineraries" in system:
            return {
                "weaknesses": [],
                "missing": [],
                "pacing_issues": [],
                "budget_concerns": [],
                "factual_concerns": [],
                "strengths": ["The draft is easy to scan."],
            }
        raise AssertionError(f"Unexpected JSON prompt: {system}")

    def chat(self, system, user, **kwargs):
        self.text_prompts.append(user)
        if "travel itinerary writer" in system:
            return (
                "# Lisbon, Portugal - 2-Day Itinerary\n\n"
                "## Day 1 - Friday, 2026-05-08\n"
                "**Weather:** Clear\n"
                "- 09:00 - Activity 1 (1h) - starts gently\n"
            )
        if "revise travel itineraries" in system:
            return (
                "# Lisbon, Portugal - 2-Day Itinerary\n\n"
                "## Day 1 - Friday, 2026-05-08\n"
                "**Weather:** Clear\n"
                "- 09:00 - Activity 1 (1h) - starts gently\n\n"
                "## Notes\n"
                "Weather drove outdoor timing."
            )
        raise AssertionError(f"Unexpected text prompt: {system}")


def ok_weather(destination, start, end):
    return {
        "status": "ok",
        "destination_resolved": destination,
        "lat": 38.72,
        "lon": -9.14,
        "days": [
            {
                "date": start,
                "high_c": 22,
                "low_c": 14,
                "precip_chance": 10,
                "summary": "Clear",
            }
        ],
    }


def test_chain_runs_all_steps_with_trace(monkeypatch):
    monkeypatch.setattr("src.steps.step2_weather.get_destination_weather", ok_weather)
    state = init_state("Two days in Lisbon for food and history")

    run(state, FakeClient())

    assert [entry["name"] for entry in state["trace"]] == [
        "extract_trip_spec",
        "fetch_weather",
        "recommend_activities",
        "build_itinerary",
        "critique_itinerary",
        "refine_itinerary",
    ]
    assert state["itinerary_final"].endswith("Weather drove outdoor timing.")
    assert state["trace"][2]["input_keys"] == ["trip_spec", "weather"]


def test_invalid_trip_short_circuits_before_tool(monkeypatch):
    def fail_weather(*args):
        raise AssertionError("weather should not run for invalid input")

    monkeypatch.setattr("src.steps.step2_weather.get_destination_weather", fail_weather)
    state = init_state("asdfqwer no real trip here")

    run(state, FakeClient(valid=False))

    assert state["trip_spec"]["valid"] is False
    assert [entry["name"] for entry in state["trace"]] == ["extract_trip_spec"]
    assert state["weather"] is None
    assert state["itinerary_final"] is None


def test_tool_unavailable_status_reaches_activity_prompt(monkeypatch):
    def unavailable_weather(destination, start, end):
        return {"status": "unavailable", "reason": "geocoding request failed"}

    monkeypatch.setattr("src.steps.step2_weather.get_destination_weather", unavailable_weather)
    client = FakeClient()
    state = init_state("Two days in Lisbon for food and history")

    run(state, client)

    activity_prompt = client.json_prompts[1]
    assert 'Weather status is "unavailable"' in activity_prompt
    assert "geocoding request failed" in activity_prompt
    assert state["weather"]["status"] == "unavailable"


def test_activity_pool_is_truncated_to_twenty_items():
    state = {
        "trip_spec": {"interests": ["food"], "budget_tier": "mid"},
        "weather": {"status": "ok", "days": []},
        "trace": [],
    }

    step3_activities.recommend_activities(state, FakeClient(activity_count=21))

    assert len(state["activities"]) == 20
    assert state["trace"][-1]["output_summary"] == "20 activities"


def test_activity_pool_with_too_few_items_fails():
    state = {
        "trip_spec": {"interests": ["food"], "budget_tier": "mid"},
        "weather": {"status": "ok", "days": []},
        "trace": [],
    }

    with pytest.raises(ValueError, match="at least 12"):
        step3_activities.recommend_activities(state, FakeClient(activity_count=11))


def test_critique_prompt_receives_activity_pool():
    class CapturingClient(FakeClient):
        def chat_json(self, system, user, **kwargs):
            self.captured_user = user
            return super().chat_json(system, user, **kwargs)

    client = CapturingClient()
    state = {
        "trip_spec": {"destination": "Lisbon, Portugal"},
        "weather": {"status": "ok", "days": []},
        "activities": [activity(1), activity(2)],
        "itinerary_v1": "# Draft\n\n- 09:00 - Activity 1",
        "trace": [],
    }

    step5_critique.critique_itinerary(state, client)

    assert "Activity pool" in client.captured_user
    assert "Activity 1" in client.captured_user
    assert state["trace"][-1]["input_keys"] == [
        "itinerary_v1",
        "trip_spec",
        "weather",
        "activities",
    ]


def test_output_writer_writes_markdown_and_state(tmp_path):
    state = init_state("Two days in Lisbon")
    state["trip_spec"] = {
        "valid": True,
        "destination": "Lisbon, Portugal",
        "start_date": "2026-05-08",
    }
    state["itinerary_final"] = "# Final Itinerary"

    md_path, json_path = write_outputs(state, outdir=str(tmp_path))

    assert md_path.endswith(".md")
    assert json_path.endswith(".json")
    assert "# Final Itinerary" in tmp_path.joinpath(md_path.split("/")[-1]).read_text()
    written_state = json.loads(tmp_path.joinpath(json_path.split("/")[-1]).read_text())
    assert written_state["trip_spec"]["destination"] == "Lisbon, Portugal"
