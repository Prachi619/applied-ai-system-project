"""Game logic that does not depend on Streamlit or the network, so pytest can cover it.

Maps to architecture.mmd:
  validate_question  -> Input Validation
  generate_hint      -> Hint Generator
  validate_response  -> Response Validator
  check_guess        -> Guess Checker
  build_log_entry / save_game_log -> Save Game Log
"""

import json
import random
import re

MAX_QUESTION_LENGTH = 150
ALLOWED_VERDICTS = ("yes", "no", "sometimes", "unclear")

# Automatic witty replies. Generic on purpose: they never mention the secret.
WITTY_REPLIES = {
    "fallback": [
        "My lips are sealed on that one. Rephrase it and I'll try again. No clue spent.",
        "That question wandered very close to the vault. Try a different angle. No clue spent.",
        "I started to answer and my conscience kicked in. Ask it another way. No clue spent.",
    ],
    "api_error": [
        "My brain just lost Wi-Fi. Give it another go. No clue spent.",
        "The AI tripped over its own shoelaces. Try again. No clue spent.",
    ],
    "wrong_guess": [
        "Bold guess. Wrong, yet bold.",
        "Not even close. Okay, a little close.",
        "Nope! The mystery object is laughing at you.",
        "Swing and a miss. Check the clues again.",
    ],
    "repeat_guess": [
        "Déjà vu! You already tried that one. No guess spent.",
        "Same guess, same wrong answer. Try something new. No guess spent.",
    ],
    "won": [
        "Detective of the year. Somebody call the newspapers.",
        "You cracked it. Humble yourself, Sherlock.",
    ],
    "lost": [
        "Out of guesses. The object remains undefeated.",
        "Don't worry, even detectives have off days.",
    ],
}


def witty_reply(kind: str, rng: random.Random | None = None) -> str:
    """Pick an automatic witty reply for a game event (see WITTY_REPLIES for kinds)."""
    rng = rng or random
    return rng.choice(WITTY_REPLIES[kind])


# ---- Text helpers --------------------------------------------------------------------
def normalize(text: str) -> str:
    """Lowercase and strip punctuation so comparisons ignore case and symbols."""
    return re.sub(r"[^a-z0-9 ]+", "", (text or "").lower()).strip()


def _names_for(obj: dict) -> list[str]:
    return [normalize(n) for n in [obj["name"], *obj.get("aliases", [])] if normalize(n)]


def mentions_secret(text: str, obj: dict) -> bool:
    """True if the text contains the secret's name or an alias as a whole word/phrase."""
    # Pad with spaces so " cat " matches but "located" does not.
    padded = f" {normalize(text)} "
    return any(f" {name} " in padded for name in _names_for(obj))


_IGNORED_WORDS = {"a", "an", "the", "and", "its", "for", "you", "are"}


def _keyword_tokens(obj: dict) -> set[str]:
    """Every word of the name and aliases, e.g. 'a bike' -> {'bike'}."""
    words = {w for n in _names_for(obj) for w in n.split()}
    return words - _IGNORED_WORDS


def leaks_secret(text: str, obj: dict) -> bool:
    """
    Strict leak check for hints and AI replies: True if any word of the text contains a
    keyword, or is itself a piece of a keyword (3+ letters). So for 'bicycle', both
    'bicycles' and 'cycle' are leaks. Keywords of 3 letters ('cat') match whole words only.
    """
    tokens = _keyword_tokens(obj)
    for word in normalize(text).split():
        if word in _IGNORED_WORDS:
            continue
        for token in tokens:
            if word == token:  # exact keyword
                return True
            if len(token) >= 4 and token in word:  # keyword inside a longer word: "bicycles"
                return True
            if len(word) >= 3 and word in token:  # word is a piece of the keyword: "cycle"
                return True
    return False


def validate_question(raw: str, asked: list[str], obj: dict):
    """
    Input Validation. Returns (ok, cleaned_question | None, error | None).
    """
    if raw is None or raw.strip() == "":
        return False, None, "Type a question first."

    question = " ".join(raw.split())
    if len(question) > MAX_QUESTION_LENGTH:
        return False, None, f"Keep questions under {MAX_QUESTION_LENGTH} characters."
    if not question.endswith("?"):
        return False, None, "Ask a yes/no question that ends with a question mark."
    if len(normalize(question).split()) < 2:
        return False, None, "That question is too short to answer."
    if mentions_secret(question, obj):
        return False, None, "If you think you know the answer, use the Guess box instead."
    if normalize(question) in {normalize(q) for q in asked}:
        return False, None, "You already asked that."

    return True, question, None


def validate_response(text: str | None, obj: dict):
    """
    Response Validator. Returns (ok, cleaned_response | None).

    A response is valid when it starts with Yes / No / Sometimes / Unclear and does not
    contain the secret's name or any part of it. Anything else is replaced by the fallback response.
    """
    if not text:
        return False, None

    cleaned = " ".join(text.split())  # collapse newlines and repeated spaces
    first_word = normalize(cleaned.split(" ")[0]) if cleaned else ""
    if first_word not in ALLOWED_VERDICTS:  # the prompt demands Yes/No/Sometimes/Unclear first
        return False, None
    if len(cleaned) > 200:  # the prompt asks for short replies; long ones suggest rambling
        return False, None
    if leaks_secret(cleaned, obj):
        return False, None

    return True, cleaned


def generate_hint(obj: dict, used_keys: list[str], rng: random.Random | None = None):
    """
    Hint Generator. Returns (property_key, hint_text) for a property not yet revealed,
    or None if every property has been used.
    """
    rng = rng or random
    remaining = [
        k
        for k in obj["properties"]
        if k not in used_keys and not leaks_secret(f"{k} {obj['properties'][k]}", obj)
    ]
    if not remaining:
        return None
    key = rng.choice(remaining)
    return key, f"Hint ({key}): {obj['properties'][key]}."


def is_repeat_guess(guess: str, previous: list[str]) -> bool:
    """True if the guess matches an earlier one (ignoring case, spacing and punctuation)."""
    cleaned = normalize(guess)
    return bool(cleaned) and cleaned in {normalize(g) for g in previous}


def tier_progress(beaten: set[str], objects: list[dict], difficulty: str):
    """Return (words beaten, total words) for one difficulty tier."""
    names = {o["name"] for o in objects if o.get("difficulty") == difficulty}
    return len(names & beaten), len(names)


NEXT_LEVEL = {"Easy": "Normal", "Normal": "Hard", "Hard": None}


def level_complete_message(difficulty: str, total: int) -> str:
    """Message shown the moment a player has beaten every word in a tier."""
    nxt = NEXT_LEVEL[difficulty]
    if nxt is None:
        return f"🏆 You've beaten all {total} {difficulty} words. You've cleared every level!"
    return (
        f"🏅 You've beaten all {total} {difficulty} words! Ready for {nxt}? "
        f"Switch in the sidebar, or keep playing {difficulty}."
    )


def with_article(name: str) -> str:
    """'elephant' -> 'an elephant', 'cat' -> 'a cat'."""
    return f"{'an' if name[0].lower() in 'aeiou' else 'a'} {name}"


def check_guess(guess: str, obj: dict):
    """
    Guess Checker. Returns (outcome, message). Outcome is "Win", "Wrong" or "Invalid".
    """
    cleaned = normalize(guess)
    if not cleaned:
        return "Invalid", "Type your guess first."
    if cleaned in _names_for(obj):
        return "Win", f"🎉 Correct! It was {with_article(obj['name'])}."
    return "Wrong", f"❌ It's not {guess.strip()}."


def update_score(info_used: int, guesses_used: int, info_limit: int = 5):
    """Score for a win: start at 100, lose 10 per extra guess and 5 per question/hint used."""
    # Clues are capped by info_limit; the 10-point floor keeps a win from scoring zero.
    points = 100 - 10 * max(guesses_used - 1, 0) - 5 * min(info_used, info_limit)
    return max(points, 10)


def build_log_entry(obj: dict, status: str, guesses: list[str], info_log: list[dict], score: int):
    return {
        "secret": obj["name"],
        "status": status,
        "guesses": guesses,
        "info": info_log,
        "score": score,
    }


def save_game_log(entry: dict, path: str = "game_log.jsonl") -> None:
    """Save Game Log: append one JSON line per finished game."""
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
