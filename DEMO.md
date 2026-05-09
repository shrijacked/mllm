# Demo checklist

Use this file before the live evaluation. It is meant to make the chain easy to narrate from saved artifacts, not to replace the README.

## Before the demo

1. Create and activate a virtual environment.
2. Install dependencies with `pip install -r requirements.txt`.
3. Put the key in `.env` as `OPENAI_API_KEY=...`, or export it in the shell before running.
4. Run `python -m compileall -q run.py src tests`.
5. Run `pytest`.

## Happy path

Run:

```bash
python run.py --input samples/lisbon.txt --verbose
python run.py --input samples/tokyo.txt --verbose
```

Save the printed paths for at least one successful run. Open the state JSON and be ready to show:

- `trace[2]` for what Step 3 received and returned at a glance.
- `trip_spec` from Step 1.
- `weather` from Step 2.
- `activities` from Step 3.
- `critique` from Step 5.

The answer to "Show me what Step 3 received" is: Step 3 receives `trip_spec` and `weather`, both visible in the state JSON. Its prompt asks for 12 to 20 activities with indoor/outdoor fields, duration, weather sensitivity, best time, cost tier, and notes.

## Malformed input

Run:

```bash
python run.py --input samples/garbage.txt --verbose
```

Expected behavior: Step 1 sets `valid` to false, the chain stops before weather, and the output writer still saves a minimal Markdown message plus full state JSON. There should be no stack trace.

## Tool failure explanation

Use either a nonsense destination or inspect the tests for the forced unavailable branch. The nonsense destination may be rejected by Step 1 as malformed input, which is also a valid failure mode. The deterministic weather fallback is `test_tool_unavailable_status_reaches_activity_prompt` in `tests/test_chain.py`.

```bash
python run.py --query "2 days in FaketownXYZ123nowhere, low budget, museums" --verbose
```

Expected behavior for the forced weather-failure test: later prompts receive `weather.status = "unavailable"` and fall back to honest seasonal language instead of crashing.

## What to say if asked where it breaks

- Forecasts only cover the short Open-Meteo horizon, so long-lead trips use seasonal language.
- Geocoding can pick the wrong city for ambiguous names.
- The system does not verify opening hours, tickets, current closures, or transit time.
