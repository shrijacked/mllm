# Travel Itinerary Planner

A multi-step LLM agent that turns a free-text trip description into a day-by-day itinerary, factoring in real weather forecasts. Built for an NLP coursework assignment.

The LLM steps use the OpenAI API. The weather step uses Open-Meteo as the external tool.

## What it does

Given input like "4 day trip to Lisbon at the end of May, two adults, mid-budget, love food and history", it produces a markdown itinerary with one section per day, weather notes per day, and activities matched to interests, pace, and budget.

## How the chain works

Six steps. Five LLM calls (OpenAI), one tool call (Open-Meteo).

1. extract — parses the trip description into structured fields.
2. weather — fetches the forecast for the destination and dates.
3. activities — generates a candidate pool of 12-20 activities.
4. itinerary — schedules activities into days.
5. critique — reviews the draft for pacing, weather mismatches, missed interests.
6. refine — rewrites the itinerary addressing the critique.

Each step writes to a shared state dict. Step N's output is step N+1's input. The orchestrator is `src/chain.py`; each step lives in its own file under `src/steps/`.

## Install

    python -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    cp .env.example .env

Edit `.env` and set `OPENAI_API_KEY`. Optional: set `OPENAI_MODEL` (defaults to `gpt-4o-mini`; the client falls back to `gpt-4o` if the requested model is rejected).

Use Python 3.10 or newer. Run commands from the repository root so `src` imports resolve.

## Run

    python run.py --input samples/lisbon.txt
    python run.py --query "5 days in tokyo, vegetarian, love anime and parks"
    python run.py
    python run.py --input samples/lisbon.txt --verbose

Output appears in `outputs/`:

- `itinerary_<slug>_<timestamp>.md` — the final itinerary (or a short message if the trip description could not be parsed).
- `state_<slug>_<timestamp>.json` — the full state dict including the trace.

See `samples/example_output.md` for a saved example of a successful itinerary shape (content from a real run may differ).

## Notes

No agent framework. The chain is hand-rolled in `src/chain.py`. The OpenAI wrapper is `src/openai_client.py`. Everything else is one file per step plus prompts under `src/prompts/`.

Open-Meteo is the tool — free, no auth, roughly sixteen days of forecast horizon from today. Trips starting beyond that window still run: step 2 marks `out_of_window` or partial days, and later steps fall back to seasonal language. See `src/tools/weather.py`.

Some placenames still geocode to a real location (for example "Atlantis" may resolve to a town name). For a clear malformed-input demo, use a nonsense destination such as `FaketownXYZ123nowhere`; the extractor usually rejects it before the weather step. The deterministic weather-failure path is covered in `tests/test_chain.py` by forcing `weather.status = "unavailable"` and proving the later prompts continue with fallback language.

Full prompt text and a step-1 prompt iteration write-up live in `PROMPTS.md`. The written report for the assignment is `REPORT.md`.

## Tests

    python -m compileall -q run.py src tests
    pytest
