# 🎮 Guess the Object

A Streamlit guessing game where Google Gemini answers your yes/no questions about a secret object or living thing, and you have a limited number of guesses to name it.

## 📌 Original Project

This project builds on **Game Glitch Investigator** (Module 1), a Streamlit number-guessing game that an AI wrote with deliberate bugs. The original goal was to find and fix those bugs: swapped "Higher/Lower" hints, a secret number that kept changing, input that was not validated, and a broken "New Game" button. It ended as a playable game with its logic in `logic_utils.py`, covered by pytest.

## 📖 Summary

The secret is no longer a number. It is an object or living thing (umbrella, guitar, cat, cactus, and so on). You get a limited number of clues. Each clue is either a yes/no question answered by Gemini or a hint from the game's own database. Then you guess.

| Difficulty | Clues (questions + hints) | Guesses | Words | Secrets |
|---|---|---|---|---|
| Easy | 5 | 6 | 5 | cat, cheese, apple, umbrella, clock |
| Normal | 4 | 8 | 10 | bicycle, guitar, refrigerator, backpack, sunflower, butterfly, telescope, cactus, goldfish, elephant |
| Hard | 3 | 5 | 15 | sphinx (the hairless cat), gouda, axolotl, metronome, stethoscope, hourglass, kaleidoscope, chameleon, platypus, pangolin, abacus, typewriter, periscope, pomegranate, venus flytrap |

That is 30 words in total. The tiers are paired on purpose. Easy has a cat and cheese, Hard has a sphinx and gouda, which are narrower versions of the same ideas.

**Level progress.** Beating every word in a level shows a message pointing to the next one: clear all 5 Easy words and you are invited to try Normal, clear all 10 Normal words and you are invited to try Hard. Nothing is locked, so you can switch levels at any time and keep playing a cleared level. The sidebar shows how many words you have beaten in each level. The game picks words you haven't beaten yet, so you can actually finish a level. Progress lasts for the browser session and resets when the page is reloaded.

**Level look and celebration.** Each level has its own drawn flower and color: golden daisies for Easy, pink blossoms for Normal and deep red roses for Hard.

- **Color everywhere:** The level color tints the title, buttons, alerts, sidebar headings, counters and a faint flower pattern behind the page.
- **Clues as chat bubbles:** Your questions, the host's answers and hints each get their own style.
- **Flower progress:** The sidebar shows one flower per word in each level, and a flower blooms for every word you beat.
- **Drawn art:** The flowers and the cat are inline SVG, so they look the same on every device instead of depending on the system's emoji.
- **Less clutter:** The debug info moved into the sidebar, and the hint button sits next to the question box.

- **Every win** shows balloons, a dancing cat, one flying word ("You got it!" on Easy, "Nailed it!" on Normal, "Impressive!" on Hard) and a few falling flowers.
- **Clearing a level** replaces that with the full show: four congratulation words ("Congratulations!", "Easy Peasy!", "Legendary!" and others, different per level) fly across the screen while more flowers fall.

Each plays once, and the flying words and flowers are switched off for people who prefer reduced motion.

It matters because an AI that answers questions can also give away the answer, contradict itself or fail. The project puts checks around the AI so the game stays fair, and tests those checks.

**How to play**

1. Pick a difficulty in the sidebar (it starts on Easy). It sets how many clues and guesses you get, and how hard the secret is. Changing difficulty starts a new game.
2. Spend clues. **Ask** sends a yes/no question to Gemini. **Get a hint** reveals one fact from the object's database entry. Both use up one clue.
3. Guess in the guess box. Capitals and punctuation don't matter, and aliases work ("fridge" for refrigerator).
4. A win shows balloons and a dancing cat. A loss shows a crying cat and reveals the answer.

**Fair-play rules**

- Repeat guesses and repeat questions are free.
- If Gemini's reply is rejected, or the API fails, no clue is used.
- A win scores 100, minus 5 per clue used and 10 per extra guess, with a minimum of 10.

## 🏗️ Architecture Overview

The system diagram is [architecture.mmd](architecture.mmd) (Mermaid source). Every box names the function or file it stands for, and it was written from the code, not from the original plan. It parses and renders as valid Mermaid.

**Flow, from input to output**

1. **Setup:** The player picks a difficulty. That chooses the clue and guess limits and a secret from that tier of the Object Database, skipping words already beaten.
2. **Ask a question:** Input Validation checks it (a question mark, a sensible length, not a duplicate, not naming the answer). If it passes, the AI Question Processor sends it to Gemini with the secret and its facts. The Response Validator checks the reply. A good reply is added to the clues and the counter drops. A bad reply or an API error shows a friendly message and costs nothing.
3. **Request a hint:** The Hint Generator reads the database and skips any hint that contains part of the answer.
4. **Submit a guess:** Empty and repeated guesses are not counted. The Guess Checker compares the rest with the name and aliases. A win scores the round and may complete the level. A wrong guess drops the counter, and running out ends the game and reveals the answer.
5. **Output:** Messages, clue bubbles, counters, flower progress, the cat and celebrations are shown. Finished games are written to `game_log.jsonl`.
6. **Evaluation:** `pytest` and `evaluate.py` test the validators, the guess checker and the database. Human review of the log and the report feeds back into the prompt, the rules and the word list.

| Diagram part | Code |
|---|---|
| Input Validation | `validate_question` in [logic_utils.py](logic_utils.py) |
| AI Question Processor | `ask_gemini` in [ai_client.py](ai_client.py) |
| Object Database | [objects_db.py](objects_db.py) |
| Hint Generator | `generate_hint` in logic_utils.py |
| Response Validator | `validate_response` in logic_utils.py |
| Guess Checker | `check_guess`, `is_repeat_guess` in logic_utils.py |
| Level progress | `tier_progress`, `level_complete_message` in logic_utils.py |
| Counters, win, game over, restart | [app.py](app.py) |
| Cat, flowers, celebrations | [theme.py](theme.py) |
| Save Game Log | `save_game_log`, writes `game_log.jsonl` |
| Automated checks | [tests/](tests/) and [evaluate.py](evaluate.py) |

Project layout:

```
app.py                 Streamlit UI and game state
logic_utils.py         Validation, hints, guess checking, scoring, witty replies, logging
ai_client.py           Gemini prompt and API call
objects_db.py          The 30 secret objects and living things, with properties and difficulty tiers
theme.py               Per-level colors, drawn flowers and cat, page CSS, celebrations (HTML/CSS strings)
evaluate.py            Evaluation harness: predefined inputs, pass/fail score, markdown report
demo.py                Console demo of one full game
evaluation_report.md   Output of evaluate.py (input, expected behavior, result)
model_card.md          Responsible-AI reflection, limitations, and evaluation summary
tests/                 pytest suite
architecture.mmd       System diagram (Mermaid)
```

## 🛠️ Setup

1. Install dependencies: `pip install -r requirements.txt`
2. Get a Gemini API key from Google AI Studio.
3. Set it as an environment variable. In PowerShell: `$env:GEMINI_API_KEY = "your-key"`. Or put `GEMINI_API_KEY = "your-key"` in `.streamlit/secrets.toml`. Both are kept out of git.
4. Optional: set `GEMINI_MODEL` to use a different model (default `gemini-2.5-flash`).
5. Run the app: `python -m streamlit run app.py`
6. Run the tests: `python -m pytest tests/`
7. Run the evaluation: `python evaluate.py` (add `--report evaluation_report.md` to save a markdown report, or `--live` to also score real Gemini answers)
8. Run the console demo: `python demo.py` (add `--live` to use real Gemini)

Without a key, the Ask button is disabled. Hints and guessing still work, and steps 6 to 8 run without a key. If you change the code while the app is running, stop the server with Ctrl+C and start it again, because Streamlit can keep the old modules cached.

## 💬 Sample Interactions

### A full game, end to end

This is the real output of `python demo.py`. The same functions the app uses run one whole round. The secret is fixed to a bicycle so the output is the same every time. In this offline mode the host's replies are canned stand-ins, not Gemini, and one of them deliberately leaks the answer so you can watch the guardrail block it.

```
$ python demo.py
Guess the Object demo - Normal difficulty, 4 clues. Host: offline stand-in host (canned replies, not Gemini)

> ask: "Does it have wheels?"
  host: Yes, it has two of them.  (clues used: 1/4)

> ask: "Is it a bike?"
  blocked before the AI: If you think you know the answer, use the Guess box instead.  (no clue used)

> ask: "Does it have wheels?"
  blocked before the AI: You already asked that.  (no clue used)

> ask: "What is it called?"
  AI reply blocked by the guardrail (it leaked the answer or broke the format)  (no clue used)

> ask: "Is it alive?"
  host: No, it is not a living thing.  (clues used: 2/4)

> hint
  Hint (moving parts): it has two wheels, pedals and a chain.  (clues used: 3/4)

> guess: "car"
  ❌ It's not car.  (guesses used: 1)

> guess: "CAR!"
  repeat guess, not counted

> guess: "bike"
  🎉 Correct! It was a bicycle.  (guesses used: 2)

You won! It was a bicycle. Score: 75
```

The score is 100, minus 5 for each of the 3 clues, minus 10 for the one extra guess.

Run `python demo.py --live` with `GEMINI_API_KEY` set to run the same round against real Gemini.

### The same checks in the app

| You do this (secret: bicycle) | What happens |
|---|---|
| Ask `Does it have wheels?` | Gemini answers, for example `Yes, it has two of them.`, and the clue counter drops by one |
| Ask `Is it a bike?` | `If you think you know the answer, use the Guess box instead.` No clue is used. |
| Gemini replies `Yes, you can cycle on it.` | Blocked, because "cycle" is part of "bicycle". You see `My lips are sealed on that one. Rephrase it and I'll try again. No clue spent.` |
| Guess `zebra`, then `Zebra!` | `It's not zebra. Bold guess. Wrong, yet bold.`, then `Déjà vu! You already tried that one. No guess spent.` |
| Guess `bike` | `You won! It was a bicycle.` plus the score and a witty line. Balloons play, a cat dances, and one flower blooms in the sidebar progress. |

### Guardrail examples

Each row shows an input, the guardrail's behavior and the result. All of these are run by `python evaluate.py`, and the full list is in [evaluation_report.md](evaluation_report.md).

| Guardrail | Input (secret: bicycle) | Behavior | Result |
|---|---|---|---|
| Input validation | `does it have wheels` | Rejected: no question mark | PASS |
| Input validation | `Is it a BICYCLE?` | Rejected: names the answer | PASS |
| Input validation | `Does it have wheels?` asked twice | Second one rejected: duplicate | PASS |
| Response validator | `Maybe, hard to say.` | Rejected: no Yes/No/Sometimes/Unclear start | PASS |
| Response validator | `Yes, a bicycle has wheels.` | Rejected: reveals the name | PASS |
| Response validator | `Yes, you can cycle on it.` | Rejected: reveals part of the name | PASS |
| Guess checker | `A BIKE!` | Accepted as a win: alias, ignoring case and punctuation | PASS |
| Hint generator | every hint for all 30 objects | None contains any part of its answer | PASS |

### The evaluation script

```
$ python evaluate.py
...
Database
  PASS  30 objects x their hints                             no hint contains any part of its answer
  PASS  hint generator, every object                         never repeats and eventually runs out
  PASS  tiers                                                5 Easy, 10 Normal, 15 Hard, 30 unique names
  PASS  every name as a guess for every other object         never wins

Witty replies
  PASS  15 lines x 30 objects                                none can hint at any answer

Offline result: 37/37 passed (100%)
```

`python evaluate.py --live` also asks real Gemini twelve questions whose correct answer is known, such as "Is it a living thing?" for a cat, and scores the replies. **I have not run it with a real key yet**, so there are no live Gemini results here. After you run `python evaluate.py --live --report evaluation_report.md`, the report will include them.

## 🧠 Design Decisions

- **Gemini only answers questions.** Hints, guess checking and scoring are plain code. They are fast and free, and they can't be wrong.
- **One source of truth.** The Gemini prompt and the hints are both built from the same object properties, so they agree with each other.
- **Strict leak check.** A hint or AI reply is rejected if it contains the secret's name, an alias, or any part of either. For a bicycle, "bike" and "cycle" are both blocked. Trade-off: some harmless replies are rejected too.
- **Rejected replies are free.** If a reply fails validation, or the API errors, the player sees a safe message and no clue is used. This keeps the strict leak check from punishing the player. The diagram shows this as the "No clue used" arrow.
- **Repeats are free.** A repeated guess or question is caught before it is counted, so a typo or a forgotten guess never costs the player.
- **Difficulty changes clues, guesses and the secret.** Hard gives 3 clues, 5 guesses and rarer words, Normal 4 and 8, Easy 5 and 6 with everyday words. Fewer clues make each question matter more, and a harder word makes the questions harder to choose.
- **Switching difficulty starts a new game.** The secret, clue limit and guess limit all depend on it, so keeping a half-finished round would leave a mismatch. The cost is that a mid-game switch loses progress.
- **Drawn flowers instead of emoji.** Emoji change shape from one device to the next, and some show as flat black icons on Windows. Inline SVG looks identical everywhere and can take each level's colors.
- **Translucent colors, no fixed page colors.** The page keeps Streamlit's own background and text, and the level color is layered on at low opacity. That keeps both light and dark mode readable without writing a second theme. For the same reason there is no `[theme]` section in a Streamlit config file: I tried one, and it pinned the app to the light theme so it ignored a dark system setting.
- **Escaped clue text.** Clue bubbles are HTML, and the answers come from an AI, so all clue text is escaped before it is shown. A test checks that a `<script>` tag in an answer is rendered as plain text.
- **Celebration in pure CSS.** The flying words and flowers use CSS animation with no JavaScript, so there is nothing extra to install or break. The HTML lives in `theme.py`, away from the UI code, so it can be tested.
- **Progress invites, it never locks.** Clearing a level shows a message, but every level stays open. Forcing players forward would punish people who enjoy an easier level.
- **Beaten words are skipped.** Without this, a player could replay the same few words and never clear a level. The trade-off is that the secret is slightly less random once some words are beaten.
- **Progress is session-only.** It lives in Streamlit's session state, which keeps the project simple. A saved profile would survive reloads but needs storage.
- **Tiers are a hand-made list.** Difficulty is a judgment call, so each object is placed in a tier by hand in `TIERS` instead of computed.
- **Witty automatic replies.** Messages for rejected replies, errors, wrong and repeat guesses, wins and losses come from a fixed list. They are cheap, repeatable and testable, and a test checks that none of them can hint at any object.
- **Wrong guesses give no warmer/colder feedback.** That would leak information the clue limit is meant to control.
- **Cat and balloons as feedback.** The win and loss states are easy to see at a glance, and the animation turns off for users who prefer reduced motion.
- **Logic stays out of the UI.** Everything testable is in `logic_utils.py`. `app.py` only handles buttons and state.
- **Fixed answer format.** Gemini must start with Yes, No, Sometimes or Unclear. This makes replies easy to validate and gives up open-ended answers.
- **Temperature 0 and no thinking.** Answers are short and repeatable.
- **Objects live in code.** A Python list is simple to edit and test. A real database would scale better.

## 🧪 Testing Summary

```
$ python -m pytest tests/
48 passed

$ python evaluate.py
Offline result: 37/37 passed (100%)
```

- **What worked:** Unit tests cover input validation, response validation, hints, guess checking, repeat guesses, scoring, witty replies and logging. The leak check is tested against every object in the database and every witty reply.
- **App behavior:** I also played full games through Streamlit's test harness with a fake Gemini reply: hints, rejected replies, API errors, wrong and repeat guesses, a win, a loss, New Game, and running with no API key. All behaved as designed.
- **What they caught:** A test found that the bicycle hint said "bike paths", and the stricter test then found "cycle paths", "your back" for backpack and "walls" for clock. The hint text was reworded.
- **What is not tested:** Live Gemini calls. Those need a key, so Gemini's real answer quality has not been measured yet (`python evaluate.py --live` does it). I also ran about 90 edge-case checks outside pytest: odd questions and guesses, bad or hostile Gemini replies, API errors, clue and guess limits, winning on the last guess, difficulty switching, and a full playthrough of all 30 words. A browser pass in Edge covered light and dark mode, a 390px phone width, reduced motion, and the level-clear animation.
- **A bug that pass found:** My Streamlit config file with a `[theme]` section pinned the app to light mode, so it ignored a dark system setting. I removed it and added a test to keep it out.
- **A layout fix:** The title wrapped onto two large lines on a phone, so it is smaller on narrow screens.
- **Stale server gotcha:** A Streamlit server started before a code change kept the old `logic_utils.py` cached and raised an ImportError. Restarting the server fixed it.
- **What I learned:** Validate the AI's output in code. A prompt that says "never reveal the name" is a request, not a guarantee.

## 🪞 Reflection

This project showed me that using AI well is mostly about the code around it: what you let it decide, what you check afterwards and what happens when it fails. My responsible-AI reflection (how I collaborated with AI, one suggestion I accepted, one I rejected, the limitations and future work) is in [model_card.md](model_card.md).
