#!/usr/bin/env python3
import argparse
import sys

from src.chain import run
from src.config import OPENAI_API_KEY, OPENAI_MODEL
from src.openai_client import OpenAIClient
from src.output_writer import write_outputs
from src.state import init_state


def main():
    p = argparse.ArgumentParser(description="Travel itinerary planner chain")
    p.add_argument("--query", type=str, help="Trip description text")
    p.add_argument("--input", type=str, help="Path to a text file with the trip description")
    p.add_argument("--verbose", action="store_true", help="Print trace lines to stderr as steps finish")
    args = p.parse_args()

    if not OPENAI_API_KEY:
        print("Set OPENAI_API_KEY in .env or your shell environment (see .env.example)", file=sys.stderr)
        sys.exit(1)

    if args.input:
        with open(args.input, encoding="utf-8") as f:
            text = f.read().strip()
    elif args.query:
        text = args.query.strip()
    else:
        text = input("Describe your trip: ").strip()

    if not text:
        print("Empty trip description.", file=sys.stderr)
        sys.exit(1)

    client = OpenAIClient(OPENAI_API_KEY, OPENAI_MODEL)
    state = init_state(text)
    run(state, client, verbose=args.verbose)
    spec = state.get("trip_spec") or {}
    if spec.get("valid") is False:
        msg = spec.get("reason_invalid") or "Could not parse a trip from that description."
        print(msg)
    paths = write_outputs(state)
    print(paths[0])
    print(paths[1])


if __name__ == "__main__":
    main()
