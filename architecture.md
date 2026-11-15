flowchart TD
    %% Guess the Object. Each box names the real code it stands for (file: function).

    A[Player] --> B["Streamlit UI<br/>app.py"]
    B --> LV["Pick difficulty<br/>Easy / Normal / Hard<br/>sets clue limit 5/4/3, guess limit 6/8/5"]
    LV --> NG["New game<br/>app.py: new_game"]
    J[("Object Database<br/>objects_db.py<br/>30 objects in 3 tiers, with properties")] --> NG
    NG -->|"random secret from the tier,<br/>skipping words already beaten"| C["Game state<br/>st.session_state"]
    LV -->|"changing difficulty<br/>starts a new game"| NG

    C --> D{Player action}
    D -->|Ask a question| E["Input Validation<br/>logic_utils: validate_question<br/>needs ?, under 150 chars, no answer name, not a duplicate"]
    D -->|Request a hint| F["Hint Generator<br/>logic_utils: generate_hint<br/>skips hints that contain any part of the answer"]
    D -->|Submit a guess| G{"Empty or repeated?<br/>logic_utils: is_repeat_guess"}

    E -->|Invalid| I["Show witty or error message<br/>no clue used"]
    I --> B
    E -->|Valid| H["AI Question Processor<br/>ai_client: ask_gemini<br/>Gemini with the secret and its facts in the prompt"]
    J --> H
    H -->|"API error"| M2["Friendly error message<br/>no clue used"]
    M2 --> B
    H --> K["Response Validator<br/>logic_utils: validate_response<br/>starts Yes/No/Sometimes/Unclear, no part of the answer, under 200 chars"]
    K -->|"Passes"| L["Add Q and A to clues"]
    K -->|"Fails"| M["Witty fallback message<br/>no clue used"]
    M --> B

    J --> F
    F --> L2["Add hint to clues"]
    L --> N["Update clue counter<br/>buttons disable at the limit"]
    L2 --> N
    N --> B

    G -->|"Empty or repeat"| R0["Message, guess not counted"]
    R0 --> B
    G -->|New guess| O{"Guess Checker<br/>logic_utils: check_guess<br/>name or alias, ignoring case and punctuation"}
    O -->|Correct| P["Win: score = 100 - 5 per clue - 10 per extra guess, minimum 10"]
    O -->|Wrong| Q["Update guess counter"]
    Q --> RR{Guesses remaining?}
    RR -->|Yes| B
    RR -->|No| S["Game over<br/>reveal the answer"]

    P --> BT["Record word as beaten<br/>app.py: finish_game"]
    BT --> LC{"Whole tier beaten?<br/>logic_utils: tier_progress"}
    LC -->|Yes| CL["Level-clear message + full celebration<br/>theme.py: celebration_html"]
    LC -->|No| WC["Win celebration: balloons, dancing cat, flowers<br/>theme.py: win_html, cat_html"]
    S --> LS["Crying cat<br/>theme.py: cat_html"]

    P --> T["Save Game Log<br/>logic_utils: save_game_log<br/>game_log.jsonl, one line per finished game"]
    S --> T

    CL --> X[New Game button]
    WC --> X
    LS --> X
    X --> NG

    U["Automated checks<br/>pytest tests/ and evaluate.py"] -.->|tests| E
    U -.->|tests| K
    U -.->|tests| O
    U -.->|tests| J
    V["Human review<br/>read game_log.jsonl and evaluation_report.md"] -.-> W[Review results]
    T --> W
    W --> V
    V -->|"Refine prompt and rules"| H
    V -->|"Edit properties and tiers"| J
