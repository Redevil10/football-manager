# config.py - Configuration and attribute definitions

import os

os.makedirs("data", exist_ok=True)
DB_PATH = "data/football_manager.db"

# Technical Attributes (ordered as in screenshot)
TECHNICAL_ATTRS = {
    "corners": "Corners",
    "crossing": "Crossing",
    "dribbling": "Dribbling",
    "finishing": "Finishing",
    "first_touch": "First Touch",
    "free_kick_taking": "Free Kick Taking",
    "heading": "Heading",
    "long_shots": "Long Shots",
    "long_throws": "Long Throws",
    "marking": "Marking",
    "passing": "Passing",
    "penalty_taking": "Penalty Taking",
    "tackling": "Tackling",
    "technique": "Technique",
}

# Mental Attributes (ordered as in screenshot)
MENTAL_ATTRS = {
    "aggression": "Aggression",
    "anticipation": "Anticipation",
    "bravery": "Bravery",
    "composure": "Composure",
    "concentration": "Concentration",
    "decisions": "Decisions",
    "determination": "Determination",
    "flair": "Flair",
    "leadership": "Leadership",
    "off_the_ball": "Off The Ball",
    "positioning": "Positioning",
    "teamwork": "Teamwork",
    "vision": "Vision",
    "work_rate": "Work Rate",
}

# Physical Attributes (ordered as in screenshot)
PHYSICAL_ATTRS = {
    "acceleration": "Acceleration",
    "agility": "Agility",
    "balance": "Balance",
    "jumping_reach": "Jumping Reach",
    "natural_fitness": "Natural Fitness",
    "pace": "Pace",
    "stamina": "Stamina",
    "strength": "Strength",
}

# Goalkeeper Attributes
GK_ATTRS = {
    "handling": "Handling",
    "reflexes": "Reflexes",
    "one_on_ones": "One-on-Ones",
    "diving": "Diving",
    "rushing_out": "Rushing Out",
}

# Scoring ranges
SCORE_RANGES = {
    "overall": (
        10,
        200,
    ),  # 综合总分 (min when all attributes=1: (1*5*3 + 1*5*2 + 1*5*3 + 1*5*2)/5 = 10)
    "technical": (5, 100),  # 进攻和防守 (min when all attributes=1: 1*5 = 5)
    "mental": (5, 100),  # 精神 (min when all attributes=1: 1*5 = 5)
    "physical": (5, 100),  # 身体 (min when all attributes=1: 1*5 = 5)
    "gk": (5, 100),  # 守门 (min when all attributes=1: 1*5 = 5)
    "attribute": (1, 20),  # 单个属性
}

# Score calculation constants
ATTRIBUTE_TO_CATEGORY_SCALE = (
    5  # Scale factor: 1-20 attribute to 1-100 category (20 * 5 = 100)
)
CATEGORY_TO_ATTRIBUTE_SCALE = (
    5  # Scale factor: 1-100 category to 1-20 attribute (100 / 5 = 20)
)

# Overall score calculation weights
OVERALL_SCORE_WEIGHTS = {
    "technical": 3,
    "mental": 2,
    "physical": 3,
    "gk": 2,
}

# Overall score calculation divisor
# When all category scores are 100: weighted_sum = 100*3 + 100*2 + 100*3 + 100*2 = 1000
# We want this to map to 200, so divide by OVERALL_SCORE_DIVISOR
OVERALL_SCORE_DIVISOR = 5

# Team allocation constants
ALLOCATION_MAX_ITERATIONS = 100  # Maximum iterations for team balancing optimization

# Candidate generation: the allocator builds many balanced splits, keeps the ones
# that are within tolerance of the best score difference, and picks among those.
# This is what makes repeated allocations of the same squad produce different teams.
ALLOCATION_ENUMERATION_LIMIT = (
    50000  # Enumerate every split when the search space is at most this many
)
ALLOCATION_RANDOM_RESTARTS = 400  # Randomized restarts when the space is bigger
# Candidates within best_diff + this share of the total score stay eligible.
# Most of the variety comes from the many splits that are *equally* optimal, not
# from loosening this -- measured on a 14-player squad, 0% tolerance already gives
# 115 distinct splits and 0.5% gives 186, while 2% only reaches 241 and triples the
# average score gap. Raise it only if a squad needs more shuffling than it gets.
ALLOCATION_BALANCE_TOLERANCE = 0.005
ALLOCATION_CANDIDATE_CAP = 2000  # Cap eligible candidates before scoring history
ALLOCATION_SUB_BAND = (
    3  # Players within 3 points of the starter cutoff compete for the last spots
)

# Captains are picked at random from the players at or above this share of their
# team's average score, so the armband moves around but never lands on the
# weakest player on the pitch.
CAPTAIN_MIN_SCORE_RATIO = 1.00

# Teammate history: players who were recently on the same team are pulled apart.
ALLOCATION_HISTORY_LOOKBACK = 10  # Past matches to consider (perf guard; decay
# already makes anything beyond ~4 matches negligible)
ALLOCATION_HISTORY_DECAY = 0.5  # Weight of each older match: 1, 0.5, 0.25, ...

POSITION_DISTRIBUTION = {
    "defender_ratio": 0.36,  # 36% of team should be defenders (4 players in 11-man team)
    "midfielder_ratio": 0.36,  # 36% of team should be midfielders (4 players in 11-man team)
    "goalkeeper_count": 1,  # Always 1 goalkeeper per team
    "substitute_gk_ratio": 0.1,  # 10% of substitutes can be goalkeepers
}  # This gives 4-4-2 formation: 1 GK + 4 defenders + 4 midfielders + 2 forwards

# All tactical positions available for position ratings
ALL_TACTICAL_POSITIONS = [
    ("GK", "GK – Goalkeeper"),
    ("LB", "LB – Left Back"),
    ("LCB", "LCB – Left Center Back"),
    ("CB", "CB – Center Back"),
    ("RCB", "RCB – Right Center Back"),
    ("RB", "RB – Right Back"),
    ("CDM", "CDM – Defensive Midfielder"),
    ("LM", "LM – Left Midfielder"),
    ("LCM", "LCM – Left Center Mid"),
    ("CM", "CM – Central Midfielder"),
    ("RCM", "RCM – Right Center Mid"),
    ("RM", "RM – Right Midfielder"),
    ("LW", "LW – Left Winger"),
    ("CF", "CF – Centre Forward"),
    ("RW", "RW – Right Winger"),
    ("LST", "LST – Left Striker"),
    ("RST", "RST – Right Striker"),
]

FIT_TIERS = [
    ("natural", "Natural"),
    ("competent", "Competent"),
]

# Most position ratings one player can hold -- the rows on the detail form.
MAX_POSITION_RATINGS = 6

# Tier weights for attribute profile blending
FIT_TIER_WEIGHTS = {"natural": 1.0, "competent": 0.5}

# Profile groups close enough to count as the same role when matching players
# to slots: a natural winger is natural on the wing of a midfield four too. They
# stay separate groups because their attribute profiles differ.
ADJACENT_POSITION_GROUPS = {
    "W": {"WM"},
    "WM": {"W"},
    "CDM": {"CM"},
    "CM": {"CDM"},
}

# Tier scores for allocation preference matching
FIT_TIER_SCORES = {"natural": 4, "competent": 2}

# Broad position_pref fallback score during allocation
POSITION_PREF_FALLBACK_SCORE = 1

# The position tables from here to `fmt: on` are laid out as grids to be read,
# not one entry a line, so the formatter is kept off them.
# fmt: off

# Tactical position → profile group key
TACTICAL_POS_TO_GROUP = {
    "GK": "GK",
    "LB": "FB", "RB": "FB",
    "LCB": "CB", "CB": "CB", "RCB": "CB",
    "CDM": "CDM",
    "LCM": "CM", "CM": "CM", "RCM": "CM",
    "LM": "WM", "RM": "WM",
    "LW": "W", "RW": "W",
    "CF": "ST", "LST": "ST", "RST": "ST",
    # Broad fallback from position_pref field
    "Goalkeeper": "GK",
    "Defender": "CB",
    "Midfielder": "CM",
    "Forward": "ST",
}

# Broad position_pref → position groups it covers (for fallback allocation)
BROAD_PREF_TO_GROUPS = {
    "Goalkeeper": {"GK"},
    "Defender": {"CB", "FB"},
    "Midfielder": {"CDM", "CM", "WM"},
    "Forward": {"ST", "W"},
}

# Weight scale: 1.8=key, 1.4=important, 1.0=neutral, 0.6=less relevant, 0.3=rarely
# Within each category, unequal weights cause redistribution; equal weights = no change.
# GK attrs for all outfield positions are set equal (0.3) → no redistribution within GK cat.
_LOW = 0.3
_MED_LOW = 0.6
_NEU = 1.0
_MED_HIGH = 1.4
_HIGH = 1.8

POSITION_PROFILES = {
    "GK": {
        "technical": {
            "corners": _LOW, "crossing": _LOW, "dribbling": _LOW,
            "finishing": _LOW, "first_touch": _NEU, "free_kick_taking": _LOW,
            "heading": _MED_HIGH, "long_shots": _LOW, "long_throws": _MED_HIGH,
            "marking": _LOW, "passing": _NEU, "penalty_taking": _LOW,
            "tackling": _LOW, "technique": _MED_LOW,
        },
        "mental": {
            "aggression": _MED_LOW, "anticipation": _MED_HIGH, "bravery": _HIGH,
            "composure": _HIGH, "concentration": _HIGH, "decisions": _HIGH,
            "determination": _NEU, "flair": _LOW, "leadership": _NEU,
            "off_the_ball": _LOW, "positioning": _HIGH, "teamwork": _NEU,
            "vision": _MED_LOW, "work_rate": _NEU,
        },
        "physical": {
            "acceleration": _MED_LOW, "agility": _HIGH, "balance": _NEU,
            "jumping_reach": _HIGH, "natural_fitness": _NEU, "pace": _MED_LOW,
            "stamina": _MED_LOW, "strength": _NEU,
        },
        "gk": {
            "handling": _HIGH, "reflexes": _HIGH, "one_on_ones": _HIGH,
            "diving": _HIGH, "rushing_out": _MED_HIGH,
        },
    },
    "CB": {
        "technical": {
            "corners": _LOW, "crossing": _MED_LOW, "dribbling": _MED_LOW,
            "finishing": _LOW, "first_touch": _MED_HIGH, "free_kick_taking": _LOW,
            "heading": _HIGH, "long_shots": _LOW, "long_throws": _MED_LOW,
            "marking": _HIGH, "passing": _MED_HIGH, "penalty_taking": _LOW,
            "tackling": _HIGH, "technique": _NEU,
        },
        "mental": {
            "aggression": _NEU, "anticipation": _HIGH, "bravery": _MED_HIGH,
            "composure": _MED_HIGH, "concentration": _HIGH, "decisions": _MED_HIGH,
            "determination": _MED_HIGH, "flair": _LOW, "leadership": _NEU,
            "off_the_ball": _LOW, "positioning": _HIGH, "teamwork": _NEU,
            "vision": _MED_LOW, "work_rate": _NEU,
        },
        "physical": {
            "acceleration": _NEU, "agility": _MED_LOW, "balance": _MED_LOW,
            "jumping_reach": _HIGH, "natural_fitness": _NEU, "pace": _NEU,
            "stamina": _MED_HIGH, "strength": _HIGH,
        },
        "gk": {
            "handling": _LOW, "reflexes": _LOW, "one_on_ones": _LOW,
            "diving": _LOW, "rushing_out": _LOW,
        },
    },
    "FB": {
        "technical": {
            "corners": _MED_LOW, "crossing": _HIGH, "dribbling": _NEU,
            "finishing": _LOW, "first_touch": _MED_HIGH, "free_kick_taking": _MED_LOW,
            "heading": _MED_LOW, "long_shots": _LOW, "long_throws": _MED_LOW,
            "marking": _MED_HIGH, "passing": _MED_HIGH, "penalty_taking": _LOW,
            "tackling": _HIGH, "technique": _NEU,
        },
        "mental": {
            "aggression": _MED_LOW, "anticipation": _MED_HIGH, "bravery": _NEU,
            "composure": _NEU, "concentration": _MED_HIGH, "decisions": _NEU,
            "determination": _MED_HIGH, "flair": _MED_LOW, "leadership": _MED_LOW,
            "off_the_ball": _NEU, "positioning": _MED_HIGH, "teamwork": _HIGH,
            "vision": _MED_LOW, "work_rate": _HIGH,
        },
        "physical": {
            "acceleration": _HIGH, "agility": _MED_HIGH, "balance": _HIGH,
            "jumping_reach": _MED_LOW, "natural_fitness": _NEU, "pace": _HIGH,
            "stamina": _HIGH, "strength": _NEU,
        },
        "gk": {
            "handling": _LOW, "reflexes": _LOW, "one_on_ones": _LOW,
            "diving": _LOW, "rushing_out": _LOW,
        },
    },
    "CDM": {
        "technical": {
            "corners": _MED_LOW, "crossing": _MED_LOW, "dribbling": _NEU,
            "finishing": _LOW, "first_touch": _MED_HIGH, "free_kick_taking": _MED_LOW,
            "heading": _NEU, "long_shots": _MED_LOW, "long_throws": _MED_LOW,
            "marking": _HIGH, "passing": _HIGH, "penalty_taking": _LOW,
            "tackling": _HIGH, "technique": _NEU,
        },
        "mental": {
            "aggression": _NEU, "anticipation": _MED_HIGH, "bravery": _NEU,
            "composure": _MED_HIGH, "concentration": _HIGH, "decisions": _MED_HIGH,
            "determination": _MED_HIGH, "flair": _LOW, "leadership": _NEU,
            "off_the_ball": _MED_LOW, "positioning": _HIGH, "teamwork": _HIGH,
            "vision": _NEU, "work_rate": _HIGH,
        },
        "physical": {
            "acceleration": _NEU, "agility": _NEU, "balance": _MED_LOW,
            "jumping_reach": _NEU, "natural_fitness": _NEU, "pace": _NEU,
            "stamina": _HIGH, "strength": _MED_HIGH,
        },
        "gk": {
            "handling": _LOW, "reflexes": _LOW, "one_on_ones": _LOW,
            "diving": _LOW, "rushing_out": _LOW,
        },
    },
    "CM": {
        "technical": {
            "corners": _MED_LOW, "crossing": _MED_LOW, "dribbling": _NEU,
            "finishing": _MED_LOW, "first_touch": _HIGH, "free_kick_taking": _MED_LOW,
            "heading": _MED_LOW, "long_shots": _NEU, "long_throws": _LOW,
            "marking": _MED_LOW, "passing": _HIGH, "penalty_taking": _MED_LOW,
            "tackling": _MED_LOW, "technique": _HIGH,
        },
        "mental": {
            "aggression": _MED_LOW, "anticipation": _MED_HIGH, "bravery": _NEU,
            "composure": _MED_HIGH, "concentration": _MED_HIGH, "decisions": _HIGH,
            "determination": _MED_HIGH, "flair": _NEU, "leadership": _NEU,
            "off_the_ball": _MED_HIGH, "positioning": _NEU, "teamwork": _HIGH,
            "vision": _HIGH, "work_rate": _MED_HIGH,
        },
        "physical": {
            "acceleration": _NEU, "agility": _MED_HIGH, "balance": _NEU,
            "jumping_reach": _MED_LOW, "natural_fitness": _NEU, "pace": _NEU,
            "stamina": _HIGH, "strength": _MED_LOW,
        },
        "gk": {
            "handling": _LOW, "reflexes": _LOW, "one_on_ones": _LOW,
            "diving": _LOW, "rushing_out": _LOW,
        },
    },
    "WM": {
        "technical": {
            "corners": _NEU, "crossing": _HIGH, "dribbling": _HIGH,
            "finishing": _MED_LOW, "first_touch": _MED_HIGH, "free_kick_taking": _MED_LOW,
            "heading": _MED_LOW, "long_shots": _MED_LOW, "long_throws": _LOW,
            "marking": _MED_LOW, "passing": _MED_HIGH, "penalty_taking": _LOW,
            "tackling": _MED_LOW, "technique": _MED_HIGH,
        },
        "mental": {
            "aggression": _MED_LOW, "anticipation": _MED_HIGH, "bravery": _MED_LOW,
            "composure": _NEU, "concentration": _NEU, "decisions": _NEU,
            "determination": _MED_HIGH, "flair": _MED_HIGH, "leadership": _MED_LOW,
            "off_the_ball": _HIGH, "positioning": _MED_LOW, "teamwork": _MED_HIGH,
            "vision": _NEU, "work_rate": _HIGH,
        },
        "physical": {
            "acceleration": _HIGH, "agility": _MED_HIGH, "balance": _MED_HIGH,
            "jumping_reach": _MED_LOW, "natural_fitness": _NEU, "pace": _HIGH,
            "stamina": _HIGH, "strength": _MED_LOW,
        },
        "gk": {
            "handling": _LOW, "reflexes": _LOW, "one_on_ones": _LOW,
            "diving": _LOW, "rushing_out": _LOW,
        },
    },
    "W": {
        "technical": {
            "corners": _MED_LOW, "crossing": _MED_HIGH, "dribbling": _HIGH,
            "finishing": _MED_HIGH, "first_touch": _MED_HIGH, "free_kick_taking": _MED_LOW,
            "heading": _LOW, "long_shots": _MED_LOW, "long_throws": _LOW,
            "marking": _LOW, "passing": _NEU, "penalty_taking": _MED_LOW,
            "tackling": _LOW, "technique": _HIGH,
        },
        "mental": {
            "aggression": _MED_LOW, "anticipation": _HIGH, "bravery": _MED_LOW,
            "composure": _MED_HIGH, "concentration": _NEU, "decisions": _NEU,
            "determination": _NEU, "flair": _HIGH, "leadership": _LOW,
            "off_the_ball": _HIGH, "positioning": _MED_LOW, "teamwork": _MED_LOW,
            "vision": _NEU, "work_rate": _NEU,
        },
        "physical": {
            "acceleration": _HIGH, "agility": _HIGH, "balance": _MED_HIGH,
            "jumping_reach": _LOW, "natural_fitness": _NEU, "pace": _HIGH,
            "stamina": _MED_HIGH, "strength": _MED_LOW,
        },
        "gk": {
            "handling": _LOW, "reflexes": _LOW, "one_on_ones": _LOW,
            "diving": _LOW, "rushing_out": _LOW,
        },
    },
    "ST": {
        "technical": {
            "corners": _LOW, "crossing": _LOW, "dribbling": _MED_HIGH,
            "finishing": _HIGH, "first_touch": _HIGH, "free_kick_taking": _MED_LOW,
            "heading": _MED_HIGH, "long_shots": _MED_HIGH, "long_throws": _LOW,
            "marking": _LOW, "passing": _MED_LOW, "penalty_taking": _MED_HIGH,
            "tackling": _LOW, "technique": _HIGH,
        },
        "mental": {
            "aggression": _MED_LOW, "anticipation": _HIGH, "bravery": _NEU,
            "composure": _HIGH, "concentration": _MED_HIGH, "decisions": _MED_HIGH,
            "determination": _MED_HIGH, "flair": _MED_HIGH, "leadership": _MED_LOW,
            "off_the_ball": _HIGH, "positioning": _MED_LOW, "teamwork": _MED_LOW,
            "vision": _NEU, "work_rate": _NEU,
        },
        "physical": {
            "acceleration": _HIGH, "agility": _MED_HIGH, "balance": _HIGH,
            "jumping_reach": _MED_HIGH, "natural_fitness": _NEU, "pace": _HIGH,
            "stamina": _NEU, "strength": _MED_HIGH,
        },
        "gk": {
            "handling": _LOW, "reflexes": _LOW, "one_on_ones": _LOW,
            "diving": _LOW, "rushing_out": _LOW,
        },
    },
}

# How each position weighs the four categories against one another. Applying a
# profile keeps the overall score and moves the category averages in
# proportion to these, then shapes each category with the profile above: a
# centre back trades goalkeeping for physique, a keeper the reverse.
#
# A table of its own because the profiles cannot answer this -- they are only
# comparable within a category, and technical's many rarely-used attributes
# would drag its average down for every position, strikers included.
POSITION_CATEGORY_EMPHASIS = {
    "GK":  {"technical": 0.6, "mental": 1.0, "physical": 1.0, "gk": 1.8},
    "CB":  {"technical": 0.9, "mental": 1.0, "physical": 1.2, "gk": 0.3},
    "FB":  {"technical": 1.0, "mental": 1.0, "physical": 1.2, "gk": 0.3},
    "CDM": {"technical": 1.0, "mental": 1.1, "physical": 1.1, "gk": 0.3},
    "CM":  {"technical": 1.1, "mental": 1.1, "physical": 1.0, "gk": 0.3},
    "WM":  {"technical": 1.1, "mental": 1.0, "physical": 1.1, "gk": 0.3},
    "W":   {"technical": 1.2, "mental": 1.0, "physical": 1.1, "gk": 0.3},
    "ST":  {"technical": 1.2, "mental": 1.0, "physical": 1.1, "gk": 0.3},
}

# fmt: on

# User role constants
USER_ROLES = {
    "VIEWER": "viewer",
    "MANAGER": "manager",
    "ADMIN": "admin",
}
VALID_ROLES = [USER_ROLES["VIEWER"], USER_ROLES["MANAGER"], USER_ROLES["ADMIN"]]

# Role hierarchy for permission checks (higher index = more privilege)
ROLE_HIERARCHY = {
    USER_ROLES["VIEWER"]: 0,
    USER_ROLES["MANAGER"]: 1,
    USER_ROLES["ADMIN"]: 2,
}
