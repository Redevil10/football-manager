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
POSITION_DISTRIBUTION = {
    "defender_ratio": 0.4,  # 40% of team should be defenders
    "midfielder_ratio": 0.35,  # 35% of team should be midfielders
    "goalkeeper_count": 1,  # Always 1 goalkeeper per team
    "substitute_gk_ratio": 0.1,  # 10% of substitutes can be goalkeepers
}

# User role constants
USER_ROLES = {
    "VIEWER": "viewer",
    "MANAGER": "manager",
}
VALID_ROLES = [USER_ROLES["VIEWER"], USER_ROLES["MANAGER"]]  # List of valid role values
