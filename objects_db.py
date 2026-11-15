"""Object Database: the secret objects the player tries to guess.

Each object has a name, accepted aliases, and a dict of properties. The properties are
the single source of truth: the Hint Generator reads them and the Gemini prompt is built
from them, so answers and hints stay consistent with each other.
"""

import random

OBJECTS = [
    {
        "name": "umbrella",
        "aliases": ["an umbrella"],
        "properties": {
            "category": "a household item",
            "use": "it keeps you dry in the rain",
            "material": "fabric stretched over a metal frame",
            "size": "about the length of your arm when folded",
            "moving parts": "it opens and closes",
            "where you find it": "by the front door or in a bag",
        },
    },
    {
        "name": "bicycle",
        "aliases": ["bike", "a bicycle", "a bike"],
        "properties": {
            "category": "a vehicle",
            "use": "it carries a person using pedal power",
            "material": "mostly metal with rubber tires",
            "size": "larger than a chair but smaller than a car",
            "moving parts": "it has two wheels, pedals and a chain",
            "where you find it": "on roads, trails and in garages",
        },
    },
    {
        "name": "guitar",
        "aliases": ["a guitar"],
        "properties": {
            "category": "a musical instrument",
            "use": "it makes music when its strings are played",
            "material": "wood, with metal or nylon strings",
            "size": "about as long as a small child is tall",
            "moving parts": "it has tuning pegs but is mostly rigid",
            "where you find it": "on stages, in bedrooms and in music shops",
        },
    },
    {
        "name": "refrigerator",
        "aliases": ["fridge", "a refrigerator", "a fridge"],
        "properties": {
            "category": "a kitchen appliance",
            "use": "it keeps food cold",
            "material": "metal and plastic",
            "size": "about as tall as a person",
            "moving parts": "it has a door and a hidden motor",
            "where you find it": "in the kitchen, plugged into the wall",
        },
    },
    {
        "name": "backpack",
        "aliases": ["a backpack", "rucksack", "bag"],
        "properties": {
            "category": "something you carry",
            "use": "it holds books and other belongings, carried on your shoulders",
            "material": "fabric or nylon with zippers",
            "size": "about the size of a large pillow",
            "moving parts": "it has zippers and straps",
            "where you find it": "at school, on hikes and in airports",
        },
    },
    {
        "name": "clock",
        "aliases": ["a clock", "wall clock"],
        "properties": {
            "category": "a household item",
            "use": "it tells you the time",
            "material": "plastic, glass and metal",
            "size": "from palm-sized to the width of a dinner plate",
            "moving parts": "it has hands that move around a face",
            "where you find it": "on desks, shelves and in classrooms",
        },
    },
    {
        "name": "telescope",
        "aliases": ["a telescope"],
        "properties": {
            "category": "a scientific instrument",
            "use": "it makes faraway things look closer",
            "material": "metal tube with glass lenses or mirrors",
            "size": "from forearm-length to taller than a person",
            "moving parts": "it can be aimed and focused",
            "where you find it": "in observatories and on balconies at night",
        },
    },
    # --- Living things ---
    {
        "name": "cat",
        "aliases": ["a cat", "kitten"],
        "living": True,
        "properties": {
            "category": "a mammal that people keep as a pet",
            "use": "it purrs, naps a lot and chases mice",
            "material": "soft fur over muscle and bone",
            "size": "small enough to sit on your lap",
            "moving parts": "it has four legs, whiskers and a tail",
            "where you find it": "in homes, on sofas and in gardens",
        },
    },
    {
        "name": "elephant",
        "aliases": ["an elephant"],
        "living": True,
        "properties": {
            "category": "the largest land mammal",
            "use": "it uses its long trunk to drink, smell and grab food",
            "material": "thick grey skin",
            "size": "taller than a doorway and heavier than a truck",
            "moving parts": "it has four thick legs, big ears and tusks",
            "where you find it": "in African and Asian grasslands and forests",
        },
    },
    {
        "name": "goldfish",
        "aliases": ["a goldfish"],
        "living": True,
        "properties": {
            "category": "a small pet that lives underwater",
            "use": "it swims in circles and breathes through gills",
            "material": "shiny orange scales",
            "size": "small enough to fit in your palm",
            "moving parts": "it has fins and a tail",
            "where you find it": "in bowls, tanks and garden ponds",
        },
    },
    {
        "name": "sunflower",
        "aliases": ["a sunflower"],
        "living": True,
        "properties": {
            "category": "a plant that grows from a seed",
            "use": "its seeds are eaten by people and birds",
            "material": "a green stem with yellow petals",
            "size": "can grow taller than a person",
            "moving parts": "its head slowly turns to follow daylight",
            "where you find it": "in fields and gardens in summer",
        },
    },
    {
        "name": "butterfly",
        "aliases": ["a butterfly"],
        "living": True,
        "properties": {
            "category": "an insect",
            "use": "it drinks nectar and spreads pollen",
            "material": "a thin body with colorful scaly wings",
            "size": "smaller than your hand",
            "moving parts": "it has four wings and six legs",
            "where you find it": "in meadows and gardens, after starting life as a caterpillar",
        },
    },
    {
        "name": "cactus",
        "aliases": ["a cactus"],
        "living": True,
        "properties": {
            "category": "a plant that stores water",
            "use": "it survives for months without rain",
            "material": "a thick green body covered in spines",
            "size": "from thumb-sized to taller than a house",
            "moving parts": "it has none",
            "where you find it": "in deserts and on sunny windowsills",
        },
    },
    # --- More easy things ---
    {
        "name": "cheese",
        "aliases": [],
        "properties": {
            "category": "a food made from milk",
            "use": "people slice, melt or grate it onto meals",
            "material": "pressed milk curds, often yellow or white",
            "size": "from a small cube to a large wheel",
            "moving parts": "it has none",
            "where you find it": "in the fridge, on pizza and in sandwiches",
        },
    },
    {
        "name": "apple",
        "aliases": ["an apple"],
        "living": False,
        "properties": {
            "category": "a fruit that grows on trees",
            "use": "people eat it raw or bake it into pies",
            "material": "crisp flesh under red, green or yellow skin",
            "size": "about the size of a fist",
            "moving parts": "it has none",
            "where you find it": "in orchards, lunch boxes and fruit bowls",
        },
    },
    # --- Hard things: less common, or a specific kind of a common thing ---
    {
        "name": "sphinx",
        "aliases": ["a sphinx", "sphynx", "a sphynx"],
        "living": True,
        "properties": {
            "category": "a rare breed of cat",
            "use": "it is kept as a pet and craves warmth",
            "material": "wrinkled skin with almost no fur",
            "size": "about as big as a regular house pet",
            "moving parts": "it has four legs, a tail and oversized ears",
            "where you find it": "in homes, usually near a heater or under a blanket",
        },
    },
    {
        "name": "gouda",
        "aliases": ["a gouda"],
        "properties": {
            "category": "a cheese from the Netherlands",
            "use": "people slice it, and it melts well",
            "material": "firm and creamy, often coated in wax",
            "size": "usually sold as a wheel or a wedge",
            "moving parts": "it has none",
            "where you find it": "in delis and shops, often with a red or yellow rind",
        },
    },
    {
        "name": "axolotl",
        "aliases": ["an axolotl"],
        "living": True,
        "properties": {
            "category": "a salamander that never grows up",
            "use": "it can regrow lost limbs, which scientists study",
            "material": "soft pink or grey skin with feathery gills",
            "size": "about as long as a pencil",
            "moving parts": "it has four legs, a tail and frilly gills",
            "where you find it": "in freshwater tanks and a few lakes near Mexico City",
        },
    },
    {
        "name": "metronome",
        "aliases": ["a metronome"],
        "properties": {
            "category": "a tool for musicians",
            "use": "it ticks a steady beat to keep players in time",
            "material": "wood or plastic with a metal weight inside",
            "size": "small enough to sit on a piano",
            "moving parts": "it has a swinging arm or a blinking light",
            "where you find it": "on pianos and music stands",
        },
    },
    {
        "name": "stethoscope",
        "aliases": ["a stethoscope"],
        "properties": {
            "category": "a medical tool",
            "use": "doctors press it to your chest to hear your heartbeat",
            "material": "rubber tubing, metal and plastic",
            "size": "light enough to hang around a neck",
            "moving parts": "it has none",
            "where you find it": "in clinics and hospitals",
        },
    },
    {
        "name": "hourglass",
        "aliases": ["an hourglass"],
        "properties": {
            "category": "a very old timekeeping device",
            "use": "sand trickles through it to measure a set amount of time",
            "material": "two clear bulbs joined by a narrow neck, filled with sand",
            "size": "from palm-sized to as tall as a bottle",
            "moving parts": "the sand flows, and you flip it over to restart",
            "where you find it": "on desks, in board games and on old ships",
        },
    },
    {
        "name": "kaleidoscope",
        "aliases": ["a kaleidoscope"],
        "properties": {
            "category": "a toy tube",
            "use": "you twist it to see colorful patterns that keep changing",
            "material": "a cardboard or metal tube with mirrors and colored beads inside",
            "size": "about as long as a flashlight",
            "moving parts": "twisting the end shifts the pieces inside",
            "where you find it": "in toy shops and craft stores",
        },
    },
    {
        "name": "chameleon",
        "aliases": ["a chameleon"],
        "living": True,
        "properties": {
            "category": "a reptile",
            "use": "it changes color to show mood and to hide",
            "material": "scaly skin",
            "size": "from a thumb to about the length of a forearm",
            "moving parts": "its eyes swivel in different directions and its tail curls",
            "where you find it": "in rainforests and warm pet shops",
        },
    },
    {
        "name": "platypus",
        "aliases": ["a platypus"],
        "living": True,
        "properties": {
            "category": "an egg-laying mammal",
            "use": "it hunts underwater using electric signals from its bill",
            "material": "brown fur, a flat tail and webbed feet",
            "size": "about as long as a loaf of bread",
            "moving parts": "it has four webbed feet and a rubbery bill",
            "where you find it": "in rivers and streams in eastern Australia",
        },
    },
    {
        "name": "pangolin",
        "aliases": ["a pangolin"],
        "living": True,
        "properties": {
            "category": "a mammal covered in scales",
            "use": "it curls into a ball to protect itself and eats ants",
            "material": "overlapping hard scales like armor",
            "size": "about as long as a small dog",
            "moving parts": "it has a long sticky tongue and strong claws",
            "where you find it": "in forests and grasslands in Africa and Asia",
        },
    },
    {
        "name": "abacus",
        "aliases": ["an abacus"],
        "properties": {
            "category": "an ancient counting tool",
            "use": "people slide beads along rods to do arithmetic",
            "material": "a wooden frame with strung beads",
            "size": "about as wide as a keyboard",
            "moving parts": "the beads slide back and forth",
            "where you find it": "in classrooms and museums, and still in some shops in Asia",
        },
    },
    {
        "name": "typewriter",
        "aliases": ["a typewriter"],
        "properties": {
            "category": "a machine from before computers",
            "use": "keys strike ink onto paper, one letter at a time",
            "material": "metal and plastic keys with an inked ribbon",
            "size": "about as big as a bread box",
            "moving parts": "keys, a carriage that slides, and a bell that dings",
            "where you find it": "in offices long ago and in antique shops",
        },
    },
    {
        "name": "periscope",
        "aliases": ["a periscope"],
        "properties": {
            "category": "an optical device",
            "use": "it lets submarine crews look above the waves",
            "material": "a tube with two mirrors",
            "size": "as long as a ladder or as short as a toy",
            "moving parts": "it can rotate and extend upward",
            "where you find it": "on submarines and in trenches",
        },
    },
    {
        "name": "pomegranate",
        "aliases": ["a pomegranate"],
        "properties": {
            "category": "a fruit full of ruby seeds",
            "use": "people eat the seeds or press them into juice",
            "material": "a tough red skin around juicy seeds",
            "size": "about as big as a softball",
            "moving parts": "it has none",
            "where you find it": "in grocery stores in autumn and in Mediterranean gardens",
        },
    },
    {
        "name": "venus flytrap",
        "aliases": ["a venus flytrap", "flytrap", "venus fly trap"],
        "living": True,
        "properties": {
            "category": "a carnivorous plant",
            "use": "it eats insects",
            "material": "green leaves with fringed edges",
            "size": "about as wide as your palm",
            "moving parts": "its leaves snap shut when touched",
            "where you find it": "in wetlands of the Carolinas and in plant shops",
        },
    },
]

# Difficulty tiers. Easy things are everyday and familiar. Hard things are rarer, or a
# specific kind of something common (gouda vs. cheese, sphinx vs. cat).
TIERS = {
    "Easy": ["cat", "cheese", "apple", "umbrella", "clock"],
    "Normal": [
        "bicycle", "guitar", "refrigerator", "backpack", "sunflower",
        "butterfly", "telescope", "cactus", "goldfish", "elephant",
    ],
    "Hard": [
        "sphinx", "gouda", "axolotl", "metronome", "stethoscope",
        "hourglass", "kaleidoscope", "chameleon", "platypus", "pangolin",
        "abacus", "typewriter", "periscope", "pomegranate", "venus flytrap",
    ],
}
for _tier, _names in TIERS.items():
    for _obj in OBJECTS:
        if _obj["name"] in _names:
            _obj["difficulty"] = _tier

# Add one shared property so the player can always learn living vs. non-living.
# Hint wording must not contain the name or part of it; tests/test_game_logic.py checks this.
for _obj in OBJECTS:
    _obj["properties"]["alive"] = (
        "yes, it is a living thing" if _obj.get("living") else "no, it is not a living thing"
    )


def pick_object(
    rng: random.Random | None = None,
    exclude: str | None = None,
    difficulty: str | None = None,
    avoid: set[str] | None = None,
) -> dict:
    """
    Pick a random object for the given difficulty ("Easy", "Normal" or "Hard"; any if None).

    `exclude` is the previous secret. `avoid` is the set of words the player has already
    beaten: those are skipped so the player can finish the whole tier, and only come back
    once every word in the tier has been beaten. Both are best effort, never an error.
    """
    rng = rng or random
    avoid = avoid or set()
    pool = [o for o in OBJECTS if difficulty is None or o["difficulty"] == difficulty]
    fresh = [o for o in pool if o["name"] not in avoid and o["name"] != exclude]
    not_previous = [o for o in pool if o["name"] != exclude]
    return rng.choice(fresh or not_previous or pool)
