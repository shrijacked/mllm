SYSTEM = (
    "You are a travel planning assistant. You read a free-text trip description from a user and "
    "extract a strict JSON object describing the trip. You output JSON only — no prose, no markdown fences, "
    "no preamble before the first brace. If the input does not describe a real trip, set \"valid\": false "
    "and explain why in \"reason_invalid\"."
)


def user_prompt(query: str, today: str) -> str:
    return (
        f"Today's date (ISO, use this to resolve relative dates): {today}\n\n"
        f"Trip description:\n{query}\n\n"
        "Return only a single JSON object with exactly these keys and types:\n"
        "- valid: boolean\n"
        "- reason_invalid: null or string (required when valid is false)\n"
        "- destination: string (city and country when known)\n"
        "- start_date: string YYYY-MM-DD\n"
        "- end_date: string YYYY-MM-DD\n"
        "- duration_days: integer\n"
        "- traveler_count: integer\n"
        "- interests: array of strings\n"
        "- pace: string (e.g. relaxed, moderate, active)\n"
        "- budget_tier: string (e.g. low, mid, high)\n"
        "- special_requests: array of strings\n\n"
        "All dates must be ISO-8601. Resolve phrases like \"end of May\" against the provided today.\n\n"
        "Example input: \"3 days in Porto next weekend, one person, loves wine, low budget\"\n"
        "Example output:\n"
        '{"valid":true,"reason_invalid":null,"destination":"Porto, Portugal","start_date":"2026-05-09",'
        '"end_date":"2026-05-11","duration_days":3,"traveler_count":1,"interests":["wine"],'
        '"pace":"moderate","budget_tier":"low","special_requests":[]}'
    )
