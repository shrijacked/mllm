# Prompt design appendix

This file mirrors the strings in `src/prompts/` as used at runtime. User prompts that embed JSON use the live `json.dumps` of state slices; the prose around those dumps is what appears here.

Provider note: this implementation uses OpenAI for all LLM steps. The prompt contracts stay explicit and provider-light: each step receives structured state slices and returns either JSON or Markdown in the shape required by the next step.

## Step 1 — extract (`src/prompts/extract.py`)

**SYSTEM (verbatim):**

You are a travel planning assistant. You read a free-text trip description from a user and extract a strict JSON object describing the trip. You output JSON only — no prose, no markdown fences, no preamble before the first brace. If the input does not describe a real trip, set "valid": false and explain why in "reason_invalid".

**USER template (verbatim, with `query` and `today` interpolated):**

Today's date (ISO, use this to resolve relative dates): {today}

Trip description:
{query}

Return only a single JSON object with exactly these keys and types:
- valid: boolean
- reason_invalid: null or string (required when valid is false)
- destination: string (city and country when known)
- start_date: string YYYY-MM-DD
- end_date: string YYYY-MM-DD
- duration_days: integer
- traveler_count: integer
- interests: array of strings
- pace: string (e.g. relaxed, moderate, active)
- budget_tier: string (e.g. low, mid, high)
- special_requests: array of strings

All dates must be ISO-8601. Resolve phrases like "end of May" against the provided today.

Example input: "3 days in Porto next weekend, one person, loves wine, low budget"
Example output:
{"valid":true,"reason_invalid":null,"destination":"Porto, Portugal","start_date":"2026-05-09","end_date":"2026-05-11","duration_days":3,"traveler_count":1,"interests":["wine"],"pace":"moderate","budget_tier":"low","special_requests":[]}

This step forces a single machine-readable contract before the weather tool runs. If dates are not ISO, step 2 cannot request a forecast window. The worked example anchors field names (`traveler_count`, not `travelers`) so downstream code does not guess.

## Step 3 — activities (`src/prompts/activities.py`)

**SYSTEM (verbatim):**

You are a travel planner specialising in personalised, well-paced itineraries. Given a trip specification and a weather forecast, you produce a candidate pool of activities matched to the traveller's interests, pace, and budget. You output strict JSON only.

**USER template:** the trip specification and weather objects are inserted as indented JSON. After the weather block, a conditional tail is appended when `weather.status` is not `"ok"`:

Weather status is "{status}". Reason: {reason}. Use seasonal norms for this destination and month. Prefer indoor options in notes where rain is plausible. If only partial daily forecasts exist, trust those days for outdoor timing and mark the rest as uncertain.

Then the fixed instruction block:

Produce exactly one JSON object with a single key "activities" whose value is an array of 12 to 20 activity objects (no fewer, no more). Each activity must have: name (string), type (string), duration_hours (number), indoor_outdoor ("indoor"|"outdoor"|"both"), weather_sensitivity ("low"|"medium"|"high"), best_time (string), est_cost_tier (string), notes (string). Mix indoor and outdoor in proportion to forecast precipitation where weather.days exists. Cover every interest in trip_spec.interests at least twice across the pool. Honour budget_tier (no luxury-only ideas for mid budget). Do not assign days or times to days; this is only a candidate pool.

Step 4 needs a bounded pool to schedule against. Twelve to twenty items keeps the itinerary step searchable without drowning it in options.

## Step 4 — itinerary (`src/prompts/itinerary.py`)

**SYSTEM (verbatim):**

You are a travel itinerary writer. You schedule activities from a fixed candidate pool into day-by-day Markdown. You must not invent activities that are not in the pool. You align outdoor blocks with lower precipitation days when weather data is available. You respect pace, budget, and special_requests (for example schedule a rest afternoon if requested).

**USER template:** trip specification JSON, weather JSON, activities JSON. If weather status is not ok, this tail is appended after the weather JSON:

Weather data is incomplete or unavailable. State **Weather:** lines using any per-day entries when present; otherwise use honest seasonal language for that month and note that the tool did not return a live forecast. Keep indoor backups visible on days that might be wet.

Then the Markdown structure requirements (title, metadata line, per-day sections with **Weather:**, time bullets, lunch, **Evening:**).

This separates scheduling from ideation: step 3 already fixed the pool, so the model cannot silently invent a "must-see" venue that was never vetted against budget or interests.

## Step 5 — critique (`src/prompts/critique.py`)

**SYSTEM (verbatim):**

You critique travel itineraries only. You do not rewrite the itinerary. Be specific: reference the day, time, or section you mean. Output strict JSON only.

**USER template:** full Markdown itinerary, then trip specification JSON, weather JSON, activity pool JSON, then:

Return one JSON object with keys: weaknesses, missing, pacing_issues, budget_concerns, factual_concerns, strengths — each an array of strings (use empty arrays if none). factual_concerns should flag activities or venues that were not in the original activity pool.

Critique is a different skill from writing. Keeping it JSON makes step 6's job mechanical: it can iterate keys instead of re-reading vague prose feedback. Passing the activity pool into this step matters because `factual_concerns` cannot reliably flag invented activities unless the model can see the allowed set.

## Step 6 — refine (`src/prompts/refine.py`)

**SYSTEM (verbatim):**

You revise travel itineraries in Markdown. You address every critique item while keeping what worked. You only use activities from the provided pool. You end with a ## Notes section that explains which weather days influenced outdoor versus indoor scheduling.

**USER template:** draft Markdown, critique JSON, weather JSON, activity pool JSON, then instructions to preserve strengths, fix all critique buckets, and close with ## Notes on weather-driven decisions.

This is where the chain proves the tool mattered: the model must tie scheduling back to forecasted days (or to the absence of data) instead of hand-waving.

## Step 1 — Iteration

**v1 SYSTEM (used in early commits before the tighten):**

You are a travel planning assistant. Read the user's trip description and pull out the key fields. Return a JSON object with destination, dates, interests, and so on.

**v1 USER:** today's date line, trip description, and a single line asking for a JSON object with inferred fields.

**Real failure transcript from an early model run, slightly trimmed:**

Here is the structured trip information you asked for:

```json
{
  "destination": "Lisbon",
  "when": "end of May 2026 for four days",
  "travelers": 2,
  "interests": ["food", "history", "walking"],
  "budget": "mid",
  "notes": "wants one lazy afternoon"
}
```

The parser expected ISO `start_date` / `end_date`, stable keys, and a top-level `valid` flag. v1 answers mixed prose, fences, natural-language dates, and `travelers` instead of `traveler_count`, so the chain would need brittle cleanup in Python.

**v2 change:** strict key list, explicit "JSON only", ISO rule tied to `today`, worked mini example, and `valid` / `reason_invalid` for garbage input. That moves constraints into the prompt instead of compensating in code after a flaky parse.
