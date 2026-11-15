"""Evaluation harness: runs predefined inputs through the guardrails and prints a score.

    python evaluate.py                    offline checks (no API key needed)
    python evaluate.py --report FILE.md   also write the results as a markdown report
    python evaluate.py --live             also ask real Gemini labeled questions (needs a key)

Offline mode tests the code around the AI: input validation, the response validator, the
guess checker, hints and the object database. Live mode tests the AI itself: it asks
Gemini questions whose correct Yes/No answer is known and scores the replies.
The exit code is 1 if any offline check fails, so it can run in CI.
"""

import argparse
import os
import sys

from logic_utils import (
    WITTY_REPLIES,
    check_guess,
    generate_hint,
    is_repeat_guess,
    leaks_secret,
    validate_question,
    validate_response,
)
from objects_db import OBJECTS, TIERS

BY_NAME = {o["name"]: o for o in OBJECTS}

# (guardrail, secret, input, behavior, expected). expected is True/False for "accepted".
QUESTION_CASES = [
    ("bicycle", "Does it have wheels?", [], True, "accepted"),
    ("bicycle", "does it have wheels", [], False, "rejected: no question mark"),
    ("bicycle", "   ", [], False, "rejected: empty"),
    ("bicycle", "?", [], False, "rejected: too short"),
    ("bicycle", "Is it a bike?", [], False, "rejected: names the answer (alias)"),
    ("bicycle", "Is it a BICYCLE?", [], False, "rejected: names the answer (capitals)"),
    ("bicycle", "Does it have wheels?", ["does it have wheels?"], False, "rejected: duplicate"),
    ("bicycle", "Is it big? " + "very " * 40, [], False, "rejected: too long"),
    ("cat", "Is it located in a house?", [], True, "accepted: 'located' is not 'cat'"),
    ("cat", "Is it a kitten?", [], False, "rejected: names the answer (alias)"),
]

# (secret, Gemini reply, expected_valid, behavior)
RESPONSE_CASES = [
    ("bicycle", "Yes, it has two of them.", True, "accepted: starts with a verdict"),
    ("bicycle", "no", True, "accepted: lowercase verdict"),
    ("bicycle", "Maybe, hard to say.", False, "rejected: no Yes/No/Sometimes/Unclear start"),
    ("bicycle", "Yes, a bicycle has wheels.", False, "rejected: reveals the name"),
    ("bicycle", "Yes, it is a bike.", False, "rejected: reveals an alias"),
    ("bicycle", "Yes, you can cycle on it.", False, "rejected: reveals part of the name"),
    ("bicycle", "", False, "rejected: empty reply"),
    ("bicycle", None, False, "rejected: no reply"),
    ("bicycle", "Yes " + "x" * 300, False, "rejected: rambling reply"),
    ("cat", "Yes, it purrs.", True, "accepted"),
    ("cat", "Yes, like a kitten.", False, "rejected: reveals an alias"),
]

# (secret, guess, expected outcome)
GUESS_CASES = [
    ("bicycle", "bicycle", "Win"),
    ("bicycle", "A BIKE!", "Win"),
    ("bicycle", "car", "Wrong"),
    ("bicycle", "   ", "Invalid"),
    ("bicycle", "!!!", "Invalid"),
    ("cat", "cats", "Wrong"),
    ("venus flytrap", "flytrap", "Win"),
    ("sphinx", "sphynx", "Win"),
    ("sphinx", "cat", "Wrong"),
    ("gouda", "cheese", "Wrong"),
]

# Live questions with a known correct answer: (secret, question, expected first word).
LIVE_CASES = [
    ("cat", "Is it a living thing?", "yes"),
    ("cat", "Is it made of metal?", "no"),
    ("cat", "Does it have a tail?", "yes"),
    ("cat", "Is it a vehicle?", "no"),
    ("guitar", "Is it a musical instrument?", "yes"),
    ("guitar", "Is it alive?", "no"),
    ("guitar", "Does it have strings?", "yes"),
    ("guitar", "Is it a kitchen appliance?", "no"),
    ("gouda", "Is it something you can eat?", "yes"),
    ("gouda", "Is it alive?", "no"),
    ("gouda", "Is it made from milk?", "yes"),
    ("gouda", "Does it have wheels?", "no"),
]


def run_offline():
    """Return a list of (section, input, behavior, passed) rows."""
    rows = []

    for secret, question, asked, expected, behavior in QUESTION_CASES:
        ok, _, _ = validate_question(question, asked, BY_NAME[secret])
        shown = question if len(question) < 50 else question[:47] + "..."
        rows.append(("Input validation", f"[{secret}] {shown!r}", behavior, ok == expected))

    for secret, reply, expected, behavior in RESPONSE_CASES:
        ok, _ = validate_response(reply, BY_NAME[secret])
        shown = repr(reply if reply is None or len(reply) < 50 else reply[:47] + "...")
        rows.append(("Response validator", f"[{secret}] {shown}", behavior, ok == expected))

    for secret, guess, expected in GUESS_CASES:
        outcome, _ = check_guess(guess, BY_NAME[secret])
        rows.append(("Guess checker", f"[{secret}] {guess!r}", f"expected {expected}", outcome == expected))
    rows.append(("Guess checker", "'CAT!!' after 'cat'", "repeat is detected", is_repeat_guess("CAT!!", ["cat"])))

    # Rules that must hold for the whole database.
    leaky = [
        (o["name"], k)
        for o in OBJECTS
        for k in o["properties"]
        if leaks_secret(f"{k} {o['properties'][k]}", o)
    ]
    rows.append(("Database", f"{len(OBJECTS)} objects x their hints", "no hint contains any part of its answer", not leaky))
    rows.append(("Database", "hint generator, every object", "never repeats and eventually runs out",
                 all(_hints_exhaust_cleanly(o) for o in OBJECTS)))
    rows.append(("Database", "tiers", "5 Easy, 10 Normal, 15 Hard, 30 unique names",
                 [len(TIERS[t]) for t in ("Easy", "Normal", "Hard")] == [5, 10, 15]
                 and len({o["name"] for o in OBJECTS}) == 30))
    cross = [(a["name"], b["name"]) for a in OBJECTS for b in OBJECTS
             if a is not b and check_guess(b["name"], a)[0] == "Win"]
    rows.append(("Database", "every name as a guess for every other object", "never wins", not cross))
    witty_leaks = [line for lines in WITTY_REPLIES.values() for line in lines
                   if any(leaks_secret(line, o) for o in OBJECTS)]
    rows.append(("Witty replies", f"{sum(len(v) for v in WITTY_REPLIES.values())} lines x {len(OBJECTS)} objects",
                 "none can hint at any answer", not witty_leaks))
    return rows


def _hints_exhaust_cleanly(obj):
    used = []
    while (hint := generate_hint(obj, used)) is not None:
        if hint[0] in used:
            return False
        used.append(hint[0])
    return 0 < len(used) <= len(obj["properties"])


def run_live(api_key):
    """Ask Gemini the labeled questions. Returns rows of (secret, question, reply, verdict, correct)."""
    from ai_client import ask_gemini

    rows = []
    for secret, question, expected in LIVE_CASES:
        obj = BY_NAME[secret]
        try:
            raw = ask_gemini(question, obj, api_key)
        except Exception as exc:  # report the failure instead of crashing the evaluation
            rows.append((secret, question, f"<error: {type(exc).__name__}>", "api error", False))
            continue
        valid, cleaned = validate_response(raw, obj)
        if not valid:
            rows.append((secret, question, repr(raw), "blocked by guardrail", False))
            continue
        first = cleaned.split()[0].strip(".,!").lower()
        rows.append((secret, question, cleaned, "accepted", first == expected))
    return rows


def markdown_report(offline, live):
    passed = sum(1 for r in offline if r[3])
    lines = ["# Evaluation Report", "",
             f"Offline guardrail checks: **{passed}/{len(offline)} passed**.", ""]
    section = None
    for sec, inp, behavior, ok in offline:
        if sec != section:
            section = sec
            lines += ["", f"## {sec}", "", "| Input | Expected behavior | Result |", "|---|---|---|"]
        lines.append(f"| `{inp}` | {behavior} | {'PASS' if ok else 'FAIL'} |")
    if live is not None:
        correct = sum(1 for r in live if r[4])
        lines += ["", f"## Live Gemini ({correct}/{len(live)} correct)", "",
                  "| Secret | Question | Reply | Guardrail | Correct |", "|---|---|---|---|---|"]
        for secret, q, reply, verdict, ok in live:
            lines.append(f"| {secret} | {q} | {reply} | {verdict} | {'yes' if ok else 'no'} |")
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--live", action="store_true", help="also evaluate real Gemini replies (needs GEMINI_API_KEY)")
    parser.add_argument("--report", metavar="FILE", help="write a markdown report to FILE")
    args = parser.parse_args()

    offline = run_offline()
    section = None
    for sec, inp, behavior, ok in offline:
        if sec != section:
            section = sec
            print(f"\n{sec}")
        print(f"  {'PASS' if ok else 'FAIL'}  {inp:<52} {behavior}")
    passed = sum(1 for r in offline if r[3])
    print(f"\nOffline result: {passed}/{len(offline)} passed ({100 * passed // len(offline)}%)")

    live = None
    if args.live:
        key = os.environ.get("GEMINI_API_KEY")
        if not key:
            print("\nLive evaluation skipped: set GEMINI_API_KEY to run it.")
        else:
            live = run_live(key)
            print("\nLive Gemini")
            for secret, q, reply, verdict, ok in live:
                print(f"  {'PASS' if ok else 'FAIL'}  [{secret}] {q:<34} -> {reply[:50]} ({verdict})")
            correct = sum(1 for r in live if r[4])
            blocked = sum(1 for r in live if r[3] == "blocked by guardrail")
            print(f"\nLive result: {correct}/{len(live)} correct, {blocked} blocked by the guardrail")

    if args.report:
        with open(args.report, "w", encoding="utf-8") as f:
            f.write(markdown_report(offline, live))
        print(f"\nReport written to {args.report}")

    sys.exit(0 if passed == len(offline) else 1)


if __name__ == "__main__":
    main()
