"""Look and feel: per-level colors, drawn flowers, page CSS and celebration effects.

Everything here returns plain HTML/CSS strings and has no Streamlit dependency, so it can
be tested. app.py passes the strings to st.markdown(..., unsafe_allow_html=True). All
motion is CSS animation (no JavaScript), and it switches off for users who prefer reduced
motion.

Each difficulty has its own flower, palette and congratulation words. Colors are stored as
"r, g, b" triples so the CSS can use them at any transparency, which keeps the page readable
in both light and dark mode.
"""

import html
import re
from urllib.parse import quote

THEMES = {
    "Easy": {
        "style": "daisy",
        "accent": "244, 180, 0",  # golden yellow
        "palette": ["255, 214, 64", "255, 214, 64", "120, 72, 20"],  # petal, petal2, center
        "words": ["Congratulations!", "Easy Peasy!", "Sunny Work!", "Nice One!"],
        "win_word": "You got it!",
    },
    "Normal": {
        "style": "blossom",
        "accent": "224, 90, 154",  # blossom pink
        "palette": ["255, 160, 200", "255, 160, 200", "255, 214, 102"],
        "words": ["Well Done!", "Brilliant!", "Sharp Mind!", "Congratulations!"],
        "win_word": "Nailed it!",
    },
    "Hard": {
        "style": "rose",
        "accent": "179, 32, 58",  # deep rose
        "palette": ["200, 40, 70", "160, 24, 52", "100, 14, 34"],
        "words": ["Legendary!", "Masterful!", "Unstoppable!", "Congratulations!"],
        "win_word": "Impressive!",
    },
}

LEVEL_ORDER = ["Easy", "Normal", "Hard"]


# ---------------------------------------------------------------------------------
# Drawn flowers (inline SVG, so they look the same on every device, unlike emoji)
# ---------------------------------------------------------------------------------
def _flower_parts(level: str) -> str:
    """SVG shapes for one flower, drawn in a 40 x 40 box."""
    theme = THEMES[level]
    petal, petal2, center = (f"rgb({c})" for c in theme["palette"])
    parts = []
    if theme["style"] == "daisy":  # ten narrow petals around a brown center
        for i in range(10):
            parts.append(
                f"<ellipse cx='20' cy='9' rx='3.4' ry='8.5' fill='{petal}' "
                f"transform='rotate({i * 36} 20 20)'/>"
            )
        parts.append(f"<circle cx='20' cy='20' r='5.5' fill='{center}'/>")
    elif theme["style"] == "blossom":  # five round petals
        for i in range(5):
            parts.append(
                f"<circle cx='20' cy='10.5' r='8' fill='{petal}' "
                f"transform='rotate({i * 72} 20 20)'/>"
            )
        parts.append(f"<circle cx='20' cy='20' r='4' fill='{center}'/>")
    else:  # rose: two rings of overlapping petals, darker toward the middle
        for i in range(5):
            parts.append(
                f"<circle cx='20' cy='11' r='8.5' fill='{petal}' "
                f"transform='rotate({i * 72} 20 20)'/>"
            )
        for i in range(5):
            parts.append(
                f"<circle cx='20' cy='14.5' r='6' fill='{petal2}' "
                f"transform='rotate({i * 72 + 36} 20 20)'/>"
            )
        parts.append(f"<circle cx='20' cy='20' r='4.5' fill='{center}'/>")
    return "".join(parts)


def flower_svg(level: str, size: int = 28, faded: bool = False) -> str:
    """One flower for the level. `faded` draws it grey and see-through (an unbloomed slot)."""
    style = " style='filter:grayscale(1);opacity:0.4'" if faded else ""
    return (
        f"<svg class='flower' viewBox='0 0 40 40' width='{size}' height='{size}'{style}>"
        f"{_flower_parts(level)}</svg>"
    )


def _pattern_uri(level: str) -> str:
    """Faint repeating flowers for the page background, as a CSS url() value."""
    svg = (
        "<svg xmlns='http://www.w3.org/2000/svg' width='160' height='160'>"
        f"<g opacity='0.09' transform='translate(16 18) scale(1.1)'>{_flower_parts(level)}</g>"
        f"<g opacity='0.07' transform='translate(100 98) scale(0.8)'>{_flower_parts(level)}</g>"
        "</svg>"
    )
    return f'url("data:image/svg+xml,{quote(svg)}")'


# ---------------------------------------------------------------------------------
# Page CSS
# ---------------------------------------------------------------------------------
def page_css(level: str) -> str:
    """All styling for the page, tinted with the level's accent color."""
    accent = THEMES[level]["accent"]
    return f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Quicksand:wght@500;700&display=swap');
:root {{ --accent: {accent}; }}

/* Faint flowers behind everything; the page's own background color shows through. */
.stApp {{ background-image: {_pattern_uri(level)}; background-size: 160px 160px; }}

/* Rounded display font for headings; body text keeps Streamlit's font. */
h1, h2, h3, .app-title, .chip, .who {{ font-family: 'Quicksand', 'Trebuchet MS', sans-serif; }}
[data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {{ color: rgb(var(--accent)); }}

/* Buttons and alerts take the level color. */
div.stButton > button, div[data-testid="stFormSubmitButton"] > button {{
  border-radius: 999px; border: 1.5px solid rgba(var(--accent), 0.75);
  background: rgba(var(--accent), 0.12); color: inherit; font-weight: 600;
}}
div.stButton > button:hover:not(:disabled),
div[data-testid="stFormSubmitButton"] > button:hover:not(:disabled) {{
  background: rgba(var(--accent), 0.28); border-color: rgb(var(--accent));
}}
[data-testid="stAlert"] {{ border-radius: 14px; border-left: 5px solid rgb(var(--accent)); }}

/* Header and flower strip */
.app-header {{ display: flex; align-items: center; justify-content: center; gap: 12px; margin: 4px 0 2px; }}
.app-title {{ font-size: 2.1rem; font-weight: 700; color: rgb(var(--accent)); }}
.floral-strip {{
  display: flex; justify-content: center; gap: 10px; padding: 4px 0 6px;
  border-radius: 12px; margin-bottom: 8px; background: rgba(var(--accent), 0.14);
}}
.floral-strip .flower {{ animation: sway 3s ease-in-out infinite; }}

/* Status chips */
.chips {{ display: flex; flex-wrap: wrap; gap: 8px; margin: 6px 0 10px; }}
.chip {{
  padding: 4px 14px; border-radius: 999px; font-size: 0.95rem;
  background: rgba(var(--accent), 0.16); border: 1px solid rgba(var(--accent), 0.4);
}}

/* Sidebar progress */
.prog {{ margin: 6px 0 12px; padding: 6px 8px; border-radius: 12px; }}
.prog.current {{ background: rgba(var(--accent), 0.14); }}
.prog-label {{ font-size: 0.85rem; margin-bottom: 4px; }}
.prog-row {{ display: flex; flex-wrap: wrap; gap: 3px; }}

/* Clue history as chat bubbles. Colors are translucent so they work on light and dark. */
.clues {{ display: flex; flex-direction: column; gap: 8px; margin: 6px 0; }}
.bubble {{ max-width: 85%; padding: 8px 14px; border-radius: 16px; line-height: 1.35; }}
.bubble .who {{ font-size: 0.72rem; opacity: 0.7; font-weight: 700; letter-spacing: 0.04em; text-transform: uppercase; }}
.bubble.q {{ align-self: flex-end; background: rgba(var(--accent), 0.2); border-bottom-right-radius: 4px; }}
.bubble.a {{ align-self: flex-start; background: rgba(128, 128, 128, 0.16); border-bottom-left-radius: 4px; }}
.bubble.h {{ align-self: flex-start; background: rgba(255, 200, 0, 0.2); border-left: 4px solid rgb(255, 190, 0); }}
.bubble.latest {{ animation: fade-in 0.5s ease-out both; }}
.empty-clues {{ opacity: 0.65; font-style: italic; margin: 6px 0; }}

/* End-of-game cat */
.cat-box {{ text-align: center; line-height: 1; }}
.cat-dance {{ display: inline-block; animation: cat-dance 0.8s ease-in-out infinite; }}
.tear-drop {{ animation: tear-fall 1.4s ease-in infinite; }}
.cat-label {{ font-size: 0.8rem; opacity: 0.75; margin-top: 4px; }}

/* Celebration layer: flying words and falling flowers */
.fx-layer {{ position: fixed; inset: 0; pointer-events: none; overflow: hidden; z-index: 9999; }}
.fly-word {{
  position: absolute; left: 0; white-space: nowrap; font-weight: 800; font-size: 2.4rem;
  font-family: 'Quicksand', 'Trebuchet MS', sans-serif;
  text-shadow: 0 0 6px rgba(255,255,255,0.95), 0 1px 3px rgba(0,0,0,0.5);
  animation: fly-across 5.5s linear both;
}}
.petal {{ position: absolute; top: -8vh; animation: petal-fall 6s linear both; }}

@keyframes sway {{ 0%,100% {{ transform: rotate(-6deg); }} 50% {{ transform: rotate(6deg); }} }}
@keyframes fade-in {{ from {{ opacity: 0; transform: translateY(6px); }} to {{ opacity: 1; transform: none; }} }}
@keyframes cat-dance {{
  0%   {{ transform: translateY(0) rotate(-10deg); }}
  25%  {{ transform: translateY(-16px) rotate(0deg); }}
  50%  {{ transform: translateY(0) rotate(10deg); }}
  75%  {{ transform: translateY(-16px) rotate(0deg); }}
  100% {{ transform: translateY(0) rotate(-10deg); }}
}}
@keyframes tear-fall {{
  0%   {{ transform: translateY(0); opacity: 0; }}
  20%  {{ opacity: 1; }}
  100% {{ transform: translateY(18px); opacity: 0; }}
}}
@keyframes fly-across {{
  0%   {{ transform: translateX(-40vw); opacity: 0; }}
  10%  {{ opacity: 1; }}
  85%  {{ opacity: 1; }}
  100% {{ transform: translateX(110vw); opacity: 0; }}
}}
@keyframes petal-fall {{
  0%   {{ transform: translateY(0) rotate(0deg); opacity: 0; }}
  10%  {{ opacity: 1; }}
  100% {{ transform: translateY(115vh) rotate(360deg); opacity: 0.9; }}
}}
@media (max-width: 480px) {{
  .app-title {{ font-size: 1.5rem; }}
  .fly-word {{ font-size: 1.6rem; }}
}}
@media (prefers-reduced-motion: reduce) {{
  .fx-layer {{ display: none; }}
  .floral-strip .flower, .cat-dance, .tear-drop, .bubble.latest {{ animation: none !important; }}
}}
</style>
"""


# ---------------------------------------------------------------------------------
# Page pieces
# ---------------------------------------------------------------------------------
def header_html(level: str) -> str:
    """Title with a flower on each side."""
    return (
        f"<div class='app-header'>{flower_svg(level, 34)}"
        f"<span class='app-title'>Guess the Object</span>{flower_svg(level, 34)}</div>"
    )


def floral_strip_html(level: str) -> str:
    """A row of swaying flowers in the level's color, shown under the title."""
    flowers = "".join(
        f"<span style='animation-delay:{i * 0.25}s'>{flower_svg(level, 30)}</span>" for i in range(9)
    )
    return f"<div class='floral-strip'>{flowers}</div>"


def chips_html(clues_left: int, guesses_left: int) -> str:
    """The two counters the player watches."""
    return (
        "<div class='chips'>"
        f"<span class='chip'>Clues left <b>{clues_left}</b></span>"
        f"<span class='chip'>Guesses left <b>{guesses_left}</b></span></div>"
    )


def progress_html(beaten_by_level: dict, totals: dict, current: str) -> str:
    """Sidebar progress: one row of flowers per level, bloomed for each word beaten."""
    rows = []
    for level in LEVEL_ORDER:
        done, total = beaten_by_level[level], totals[level]
        flowers = "".join(flower_svg(level, 20, faded=i >= done) for i in range(total))
        cleared = " ✓ cleared" if done == total else ""
        cls = "prog current" if level == current else "prog"
        rows.append(
            f"<div class='{cls}'><div class='prog-label'><b>{level}</b> {done}/{total}{cleared}</div>"
            f"<div class='prog-row'>{flowers}</div></div>"
        )
    return "".join(rows)


def clues_html(info_log: list) -> str:
    """Clue history as chat bubbles. All text is escaped because it can come from the AI."""
    if not info_log:
        return "<div class='empty-clues'>Nothing yet. Ask a question or request a hint.</div>"
    last = len(info_log) - 1
    items = []
    for i, entry in enumerate(info_log):
        latest = " latest" if i == last else ""
        if entry["kind"] == "question":
            items.append(
                f"<div class='bubble q{latest}'><div class='who'>You asked</div>"
                f"{html.escape(entry['text'])}</div>"
                f"<div class='bubble a{latest}'><div class='who'>Host</div>"
                f"{html.escape(entry['answer'])}</div>"
            )
        else:
            # Hint text looks like "Hint (category): a household item."
            match = re.match(r"^Hint \((.+?)\): (.*)$", entry["answer"])
            label, body = (f"Hint · {match.group(1)}", match.group(2)) if match else ("Hint", entry["answer"])
            items.append(
                f"<div class='bubble h{latest}'><div class='who'>{html.escape(label)}</div>"
                f"{html.escape(body)}</div>"
            )
    return f"<div class='clues'>{''.join(items)}</div>"


def cat_html(won: bool) -> str:
    """A drawn cat: dancing with a smile for a win, crying with falling tears for a loss."""
    fur, ear, dark = "rgb(236,170,92)", "rgb(255,170,170)", "rgb(60,40,30)"
    base = (
        f"<polygon points='18,44 24,8 52,30' fill='{fur}'/><polygon points='82,44 76,8 48,30' fill='{fur}'/>"
        f"<polygon points='25,38 27,18 42,30' fill='{ear}'/><polygon points='75,38 73,18 58,30' fill='{ear}'/>"
        f"<circle cx='50' cy='60' r='34' fill='{fur}'/>"
        f"<polygon points='46,64 54,64 50,69' fill='{ear}'/>"
        f"<g stroke='{dark}' stroke-width='1.6' fill='none' stroke-linecap='round'>"
        "<line x1='14' y1='60' x2='34' y2='64'/><line x1='14' y1='70' x2='34' y2='68'/>"
        "<line x1='86' y1='60' x2='66' y2='64'/><line x1='86' y1='70' x2='66' y2='68'/></g>"
    )
    if won:
        face = (
            f"<g stroke='{dark}' stroke-width='3' fill='none' stroke-linecap='round'>"
            "<path d='M32 56 q7 -9 14 0'/><path d='M54 56 q7 -9 14 0'/>"
            "<path d='M40 73 q10 12 20 0'/></g>"
        )
        body = f"<div class='cat-box'><div class='cat-dance'>{_svg(base + face, 84)}</div>"
        label = "<div class='cat-label'>the cat approves</div></div>"
    else:
        face = (
            f"<g fill='{dark}'><circle cx='39' cy='57' r='4'/><circle cx='61' cy='57' r='4'/></g>"
            f"<g stroke='{dark}' stroke-width='3' fill='none' stroke-linecap='round'>"
            "<path d='M31 48 l12 4'/><path d='M69 48 l-12 4'/><path d='M40 77 q10 -9 20 0'/></g>"
            "<ellipse class='tear-drop' cx='38' cy='66' rx='3' ry='5' fill='rgb(90,170,255)'/>"
            "<ellipse class='tear-drop' cx='62' cy='66' rx='3' ry='5' fill='rgb(90,170,255)' "
            "style='animation-delay:0.6s'/>"
        )
        body = f"<div class='cat-box'>{_svg(base + face, 84)}"
        label = "<div class='cat-label'>the cat is devastated</div></div>"
    return body + label


def _svg(inner: str, size: int) -> str:
    return f"<svg viewBox='0 0 100 100' width='{size}' height='{size}'>{inner}</svg>"


# ---------------------------------------------------------------------------------
# Celebrations
# ---------------------------------------------------------------------------------
def _petals(level: str, count: int, spread: int, size: int) -> str:
    """Flowers falling from spread-out positions with staggered delays."""
    return "".join(
        f"<div class='petal' style='left:{(i * spread + 3) % 94}vw; "
        f"animation-delay:{(i % 6) * 0.5}s'>{flower_svg(level, size)}</div>"
        for i in range(count)
    )


def win_html(level: str) -> str:
    """Small celebration for a single win: one flying word and a few flowers."""
    theme = THEMES[level]
    word = (
        f"<div class='fly-word' style='top:20%; color:rgb({theme['accent']})'>"
        f"{theme['win_word']}</div>"
    )
    return f"<div class='fx-layer'>{word}{_petals(level, 8, 12, 30)}</div>"


def celebration_html(level: str) -> str:
    """Full celebration for clearing a level: four flying words and many flowers."""
    theme = THEMES[level]
    words = "".join(
        f"<div class='fly-word' style='top:{12 + i * 18}%; color:rgb({theme['accent']}); "
        f"animation-delay:{i * 0.9}s'>{w}</div>"
        for i, w in enumerate(theme["words"])
    )
    return f"<div class='fx-layer'>{words}{_petals(level, 18, 7, 32)}</div>"
