# 🎮 Game Glitch Investigator: The Impossible Guesser

## 🚨 The Situation

You asked an AI to build a simple "Number Guessing Game" using Streamlit.
It wrote the code, ran away, and now the game is unplayable. 

- You can't win.
- The hints lie to you.
- The secret number seems to have commitment issues.

## 🛠️ Setup

1. Install dependencies: `pip install -r requirements.txt`
2. Run the broken app: `python -m streamlit run app.py`

## 🕵️‍♂️ Your Mission

1. **Play the game.** Open the "Developer Debug Info" tab in the app to see the secret number. Try to win.
2. **Find the State Bug.** Why does the secret number change every time you click "Submit"? Ask ChatGPT: *"How do I keep a variable from resetting in Streamlit when I click a button?"*
3. **Fix the Logic.** The hints ("Higher/Lower") are wrong. Fix them.
4. **Refactor & Test.** - Move the logic into `logic_utils.py`.
   - Run `pytest` in your terminal.
   - Keep fixing until all tests pass!

## 📝 Document Your Experience

- [x] **Purpose:** Glitchy Guesser is a Streamlit number-guessing game. You pick a difficulty (Easy 1-20, Normal 1-100, Hard 1-50), guess the secret number within a limited number of attempts, and get "Go HIGHER!" / "Go LOWER!" hints and a score. The project is about finding and fixing bugs in AI-generated code.
- [x] **Bugs found:**
  1. **Wrong hints:** the "Too High" and "Too Low" messages were swapped, and on even attempts the secret was converted to a string, so numbers were compared as text (`"9" > "40"`).
  2. **New Game broke play:** it never reset `status` to "playing", so `st.stop()` blocked every guess after a win or loss. Score and history were not reset either.
  3. **Invalid input accepted:** decimals were silently truncated, and numbers like 500 or -5 were accepted and used up an attempt, because `parse_guess` had no range check.
  4. **Wrong number of guesses:** attempts started at 1, so the game gave one guess too few. Invalid input also used up an attempt, and the info text always said 1 to 100.
- [x] **Fixes applied:**
  1. `check_guess` now lives in `logic_utils.py`, returns the correct hint for each outcome, and compares ints numerically. `app.py` imports it and no longer casts the secret to a string.
  2. "New Game" now resets attempts, secret, status, score, and history.
  3. `parse_guess` also moved to `logic_utils.py`. It now rejects decimals, text, and numbers outside the selected difficulty's range, with a clear error.
  4. Attempts start at 0, only valid guesses count, and the range message uses the selected difficulty.
  4. Added regression tests in `tests/test_game_logic.py`.

## 📸 Demo Walkthrough

Describe your fixed game in numbered steps so a reader can follow along without watching a video:

1. Run `python -m streamlit run app.py` and open the local URL. Choose a difficulty in the sidebar; the range and attempts allowed are shown there.
2. Open "Developer Debug Info" to see the secret number, then enter a guess and click **Submit Guess**. The secret stays the same between guesses.
3. A guess above the secret says "Go LOWER!" and a guess below says "Go HIGHER!". "Attempts left" counts down from the full limit.
4. Guess the secret to win: balloons appear, and the final score is shown.
5. Click **New Game**. The attempts, score, and history reset, a new secret is picked, and you can guess again right away.

**Screenshot** *(optional)*: <!-- Insert a screenshot of your fixed, winning game here -->

## 🧪 Test Results

```
$ python -m pytest tests/
============================= test session starts =============================
platform win32 -- Python 3.13.15, pytest-9.1.1, pluggy-1.6.0
collected 12 items

tests\test_game_logic.py ............                                    [100%]

============================= 12 passed in 1.65s ==============================
```

## 🚀 Stretch Features

- [ ] [If you choose to complete Challenge 4, describe the Enhanced UI changes here — a screenshot is optional]
