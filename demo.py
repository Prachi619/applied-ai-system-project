"""Console demo of one full game, using the same functions the app uses.

    python demo.py            offline: a stand-in host with canned replies (no key needed)
    python demo.py --live     real Gemini answers (needs GEMINI_API_KEY)

The secret is fixed to "bicycle" so the output is the same every run. One stand-in reply
deliberately leaks the answer so you can watch the guardrail block it.
"""

import argparse
import os
import random

from ai_client import ask_gemini
from logic_utils import (
    check_guess,
    generate_hint,
    is_repeat_guess,
    update_score,
    validate_question,
    validate_response,
    with_article,
)
from objects_db import OBJECTS

CLUE_LIMIT = 4  # Normal difficulty

# Canned replies for offline mode. They are NOT from Gemini.
STAND_IN = {
    "Does it have wheels?": "Yes, it has two of them.",
    "Is it alive?": "No, it is not a living thing.",
    "What is it called?": "Yes, a bicycle, obviously.",  # a leaking reply, to show the guardrail
}


def host_reply(question, secret, live, key):
    if live:
        return ask_gemini(question, secret, key)
    return STAND_IN.get(question, "Unclear.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args()
    key = os.environ.get("GEMINI_API_KEY")
    if args.live and not key:
        raise SystemExit("Set GEMINI_API_KEY to use --live.")

    secret = next(o for o in OBJECTS if o["name"] == "bicycle")
    mode = "live Gemini" if args.live else "offline stand-in host (canned replies, not Gemini)"
    print(f"Guess the Object demo - Normal difficulty, {CLUE_LIMIT} clues. Host: {mode}\n")

    clues, asked, guesses, hint_keys = 0, [], [], []

    for question in ["Does it have wheels?", "Is it a bike?", "Does it have wheels?",
                     "What is it called?", "Is it alive?"]:
        print(f'> ask: "{question}"')
        ok, cleaned, err = validate_question(question, asked, secret)
        if not ok:
            print(f"  blocked before the AI: {err}  (no clue used)\n")
            continue
        valid, reply = validate_response(host_reply(cleaned, secret, args.live, key), secret)
        if not valid:
            print("  AI reply blocked by the guardrail (it leaked the answer or broke the format)  (no clue used)\n")
            continue
        asked.append(cleaned)
        clues += 1
        print(f"  host: {reply}  (clues used: {clues}/{CLUE_LIMIT})\n")

    print("> hint")
    key_, hint = generate_hint(secret, hint_keys, random.Random(5))  # seeded: same hint every run
    hint_keys.append(key_)
    clues += 1
    print(f"  {hint}  (clues used: {clues}/{CLUE_LIMIT})\n")

    for guess in ["car", "CAR!", "bike"]:
        print(f'> guess: "{guess}"')
        outcome, message = check_guess(guess, secret)
        if is_repeat_guess(guess, guesses):
            print("  repeat guess, not counted\n")
            continue
        guesses.append(guess)
        print(f"  {message}  (guesses used: {len(guesses)})")
        if outcome == "Win":
            score = update_score(clues, len(guesses), CLUE_LIMIT)
            print(f"\nYou won! It was {with_article(secret['name'])}. Score: {score}")
            break
        print()


if __name__ == "__main__":
    main()
