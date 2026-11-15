"""Guess the Object: Streamlit UI.

The game logic lives in logic_utils.py, the Gemini call in ai_client.py, the secret
objects in objects_db.py and the look (colors, flowers, cat, celebrations) in theme.py.
This file only wires them to the screen and keeps game state.

Streamlit reruns this whole script on every click, so anything that must survive between
clicks is stored in st.session_state.
"""

import os

import streamlit as st

from ai_client import ask_gemini
from logic_utils import (
    build_log_entry,
    check_guess,
    generate_hint,
    is_repeat_guess,
    level_complete_message,
    save_game_log,
    tier_progress,
    update_score,
    validate_question,
    validate_response,
    with_article,
    witty_reply,
)
from objects_db import OBJECTS, pick_object
from theme import (
    LEVEL_ORDER,
    cat_html,
    celebration_html,
    chips_html,
    clues_html,
    floral_strip_html,
    header_html,
    page_css,
    progress_html,
    win_html,
)

# Per-difficulty limits. Clues are questions and hints combined.
INFO_LIMIT_MAP = {"Easy": 5, "Normal": 4, "Hard": 3}
GUESS_LIMIT_MAP = {"Easy": 6, "Normal": 8, "Hard": 5}


def get_api_key():
    """Read the Gemini key from the environment first, then Streamlit secrets."""
    key = os.environ.get("GEMINI_API_KEY")
    if key:
        return key
    try:
        return st.secrets["GEMINI_API_KEY"]
    except Exception:  # no secrets.toml, or the key is not in it
        return None


def new_game(difficulty: str):
    """Start a fresh round: pick a secret from the difficulty's tier and reset all state."""
    previous = st.session_state.get("secret_obj", {}).get("name")
    st.session_state.game_difficulty = difficulty  # lets us notice when the sidebar changes
    # Easy gets everyday things, Hard gets rarer or more specific ones. Words the player has
    # already beaten are skipped until the whole tier is beaten, so every word gets a turn.
    st.session_state.secret_obj = pick_object(
        exclude=previous, difficulty=difficulty, avoid=st.session_state.beaten
    )
    st.session_state.guesses = []
    st.session_state.info_log = []  # [{"kind": "question"|"hint", "text": ..., "answer": ...}]
    st.session_state.hint_keys = []  # which properties hints have already revealed
    st.session_state.status = "playing"  # "playing" | "won" | "lost"
    st.session_state.score = 0
    st.session_state.notice = None  # one-shot message shown after the next rerun
    st.session_state.quip = None  # witty line shown with the win / game-over message
    st.session_state.celebrated = False  # balloons have not played yet
    st.session_state.level_msg = None  # "you cleared this level" message, set on a win
    st.session_state.level_fx_played = False  # flying words and flowers play once per clear


def finish_game(status: str):
    """End the round ("won" or "lost"): record progress, pick a witty line, write the log."""
    st.session_state.status = status
    if status == "won":
        level = st.session_state.game_difficulty
        done_before, total = tier_progress(st.session_state.beaten, OBJECTS, level)
        st.session_state.beaten.add(st.session_state.secret_obj["name"])
        done_after, _ = tier_progress(st.session_state.beaten, OBJECTS, level)
        # Only announce the moment the tier becomes complete, not on every later win.
        if done_after == total and done_before < total:
            st.session_state.level_msg = level_complete_message(level, total)
    st.session_state.quip = witty_reply("won" if status == "won" else "lost")
    save_game_log(
        build_log_entry(
            st.session_state.secret_obj,
            status,
            st.session_state.guesses,
            st.session_state.info_log,
            st.session_state.score,
        )
    )


# ----------------------------------------------------------------------------------
# Page setup and sidebar
# ----------------------------------------------------------------------------------
st.set_page_config(page_title="Guess the Object", page_icon="🎮")

st.sidebar.header("Settings")
difficulty = st.sidebar.selectbox("Difficulty", list(GUESS_LIMIT_MAP), index=0)

# Words the player has beaten this session. It survives New Game, so progress adds up.
if "beaten" not in st.session_state:
    st.session_state.beaten = set()

if "secret_obj" not in st.session_state:
    new_game(difficulty)  # first visit
elif st.session_state.game_difficulty != difficulty:
    # The secret, clue limit and guess limit all depend on difficulty, so switching
    # starts a new round instead of leaving a mismatched one in progress.
    new_game(difficulty)
    st.session_state.notice = ("info", f"Difficulty changed to {difficulty}. New game started.")

# Each level has its own flower, color and background (see theme.py).
st.markdown(page_css(difficulty) + header_html(difficulty), unsafe_allow_html=True)
st.caption("Use your questions and hints wisely, then guess the secret object.")
st.markdown(floral_strip_html(difficulty), unsafe_allow_html=True)

guess_limit = GUESS_LIMIT_MAP[difficulty]
INFO_LIMIT = INFO_LIMIT_MAP[difficulty]
st.sidebar.caption(f"Guesses allowed: {guess_limit}")
st.sidebar.caption(f"Questions + hints allowed: {INFO_LIMIT}")

# Progress per level, drawn as flowers that bloom for each word beaten. Nothing is locked:
# the player can play any level at any time.
st.sidebar.subheader("Progress")
progress = {lvl: tier_progress(st.session_state.beaten, OBJECTS, lvl) for lvl in LEVEL_ORDER}
st.sidebar.markdown(
    progress_html(
        {lvl: p[0] for lvl, p in progress.items()},
        {lvl: p[1] for lvl, p in progress.items()},
        difficulty,
    ),
    unsafe_allow_html=True,
)

# Without a key the game still works: only the Ask button is disabled (see below).
api_key = get_api_key()
if not api_key:
    st.warning(
        "No Gemini API key found. Set the GEMINI_API_KEY environment variable (or add it to "
        ".streamlit/secrets.toml) to ask questions. Hints and guessing still work."
    )

secret = st.session_state.secret_obj
info_used = len(st.session_state.info_log)
guesses_used = len(st.session_state.guesses)
playing = st.session_state.status == "playing"

# For testing and demos: reveals the secret on purpose. Tucked into the sidebar to keep
# the main screen clean.
with st.sidebar.expander("Developer Debug Info"):
    st.write("Secret:", secret["name"], f"({secret['difficulty']} tier)")
    st.write("Status:", st.session_state.status)
    st.write("Hints used:", st.session_state.hint_keys)

# Show the message left by the previous click, then clear it so it appears only once.
notice = st.session_state.notice
if notice:
    getattr(st, notice[0])(notice[1])  # notice = ("warning" | "error" | ..., text)
    st.session_state.notice = None

st.markdown(
    chips_html(INFO_LIMIT - info_used, guess_limit - guesses_used), unsafe_allow_html=True
)

# ----------------------------------------------------------------------------------
# End-of-game result: message on the left, cat on the right
# ----------------------------------------------------------------------------------
if not playing:
    won = st.session_state.status == "won"
    result_col, cat_col = st.columns([4, 1])
    with result_col:
        if won:
            st.success(
                f"You won! It was {with_article(secret['name'])}. "
                f"Score: {st.session_state.score}. {st.session_state.quip}"
            )
        else:
            st.error(f"Game over. The answer was: {secret['name']}. {st.session_state.quip}")
        if st.session_state.level_msg:
            st.info(st.session_state.level_msg)
    with cat_col:
        st.markdown(cat_html(won), unsafe_allow_html=True)
    # Balloons play once. The page reruns right after a win, so fire them here.
    if won and not st.session_state.celebrated:
        st.balloons()
        st.session_state.celebrated = True
        # Every win gets a small flying word and a few flowers. Clearing a whole level
        # gets the full show instead (below), so only one of the two plays.
        if not st.session_state.level_msg:
            st.markdown(win_html(st.session_state.game_difficulty), unsafe_allow_html=True)
    if st.session_state.level_msg and not st.session_state.level_fx_played:
        st.markdown(celebration_html(st.session_state.game_difficulty), unsafe_allow_html=True)
        st.session_state.level_fx_played = True

# ----------------------------------------------------------------------------------
# Player actions (only while the round is in progress)
# ----------------------------------------------------------------------------------
if playing:
    # Forms with clear_on_submit empty the text box after each click.
    ask_col, hint_col = st.columns([3, 1])
    with ask_col:
        # --- Ask a question (Input Validation -> AI Question Processor -> Response Validator) ---
        with st.form("question_form", clear_on_submit=True):
            raw_question = st.text_input("Ask a yes/no question about the object:")
            ask = st.form_submit_button("Ask ❓", disabled=info_used >= INFO_LIMIT or not api_key)
    with hint_col:
        # --- Request a hint (Hint Generator) ---
        st.markdown("<div style='height:1.9rem'></div>", unsafe_allow_html=True)  # line up with the input
        hint_clicked = st.button("Get a hint 💡", disabled=info_used >= INFO_LIMIT)

    # --- Submit a guess (Guess Checker) ---
    with st.form("guess_form", clear_on_submit=True):
        raw_guess = st.text_input("Your guess:")
        guess_clicked = st.form_submit_button("Submit Guess 🚀")

    if ask:
        asked = [e["text"] for e in st.session_state.info_log if e["kind"] == "question"]
        ok, question, err = validate_question(raw_question, asked, secret)
        if not ok:
            st.session_state.notice = ("error", err)
        else:
            try:
                raw_reply = ask_gemini(question, secret, api_key)
            except Exception as exc:  # network, quota, bad key...
                # API failures are free: nothing is logged, so no clue is used.
                st.session_state.notice = (
                    "error",
                    f"{witty_reply('api_error')} ({type(exc).__name__})",
                )
                st.rerun()
            valid, answer = validate_response(raw_reply, secret)
            if not valid:
                # Rejected replies are free: show a witty message and do not log a clue.
                st.session_state.notice = ("warning", witty_reply("fallback"))
            else:
                st.session_state.info_log.append(
                    {"kind": "question", "text": question, "answer": answer}
                )
        st.rerun()

    if hint_clicked:
        result = generate_hint(secret, st.session_state.hint_keys)
        if result is None:
            st.session_state.notice = ("warning", "No hints left for this object.")
        else:
            key, text = result
            st.session_state.hint_keys.append(key)  # so the same hint is never shown twice
            st.session_state.info_log.append({"kind": "hint", "text": "Hint", "answer": text})
        st.rerun()

    if guess_clicked:
        outcome, message = check_guess(raw_guess, secret)
        if outcome == "Invalid":
            st.session_state.notice = ("error", message)  # empty guess
        elif is_repeat_guess(raw_guess, st.session_state.guesses):
            # Repeats are free: not stored and not counted.
            st.session_state.notice = ("warning", witty_reply("repeat_guess"))
        else:
            st.session_state.guesses.append(raw_guess.strip())
            if outcome == "Win":
                st.session_state.score = update_score(
                    len(st.session_state.info_log), len(st.session_state.guesses), INFO_LIMIT
                )
                finish_game("won")
            elif len(st.session_state.guesses) >= guess_limit:
                finish_game("lost")  # that was the last guess
            else:
                st.session_state.notice = ("warning", f"{message} {witty_reply('wrong_guess')}")
        st.rerun()

# ----------------------------------------------------------------------------------
# Clue history and restart
# ----------------------------------------------------------------------------------
st.subheader("Clues so far")
st.markdown(clues_html(st.session_state.info_log), unsafe_allow_html=True)

if st.session_state.guesses:
    st.caption("Your guesses: " + ", ".join(st.session_state.guesses))

st.divider()
if st.button("New Game 🔁"):
    new_game(difficulty)
    st.rerun()
