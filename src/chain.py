import sys

from src.steps import step1_extract
from src.steps import step2_weather
from src.steps import step3_activities
from src.steps import step4_itinerary
from src.steps import step5_critique
from src.steps import step6_refine


def run(state, client, verbose=False):
    def v():
        if verbose and state.get("trace"):
            print(state["trace"][-1], file=sys.stderr)

    step1_extract.extract_trip_spec(state, client)
    v()
    if state["trip_spec"].get("valid") is False:
        return state
    step2_weather.fetch_weather(state)
    v()
    step3_activities.recommend_activities(state, client)
    v()
    step4_itinerary.build_itinerary(state, client)
    v()
    step5_critique.critique_itinerary(state, client)
    v()
    step6_refine.refine_itinerary(state, client)
    v()
    return state
