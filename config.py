# config.py - Configuration and attribute definitions

DB_PATH = "/tmp/data/football_manager.db"

# Technical Attributes
TECHNICAL_ATTRS = {
    "pace": "Pace",
    "shooting": "Shooting",
    "passing": "Passing",
    "dribbling": "Dribbling",
    "tackling": "Tackling",
    "heading": "Heading",
    "first_touch": "First Touch",
    "finishing": "Finishing",
    "technique": "Technique",
    "long_shots": "Long Shots",
}

# Mental Attributes
MENTAL_ATTRS = {
    "decisions": "Decisions",
    "aggression": "Aggression",
    "teamwork": "Teamwork",
    "work_rate": "Work Rate",
    "anticipation": "Anticipation",
    "composure": "Composure",
    "vision": "Vision",
    "flair": "Flair",
    "positioning": "Positioning",
}

# Physical Attributes
PHYSICAL_ATTRS = {
    "strength": "Strength",
    "stamina": "Stamina",
    "acceleration": "Acceleration",
    "jumping_reach": "Jumping Reach",
    "agility": "Agility",
    "balance": "Balance",
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
    "overall": (10, 200),  # 综合总分 (min when all attributes=1: (1*5*3 + 1*5*2 + 1*5*3 + 1*5*2)/5 = 10)
    "technical": (5, 100),  # 进攻和防守 (min when all attributes=1: 1*5 = 5)
    "mental": (5, 100),  # 精神 (min when all attributes=1: 1*5 = 5)
    "physical": (5, 100),  # 身体 (min when all attributes=1: 1*5 = 5)
    "gk": (5, 100),  # 守门 (min when all attributes=1: 1*5 = 5)
    "attribute": (1, 20),  # 单个属性
}

# Score calculation constants
ATTRIBUTE_TO_CATEGORY_SCALE = 5  # Scale factor: 1-20 attribute to 1-100 category (20 * 5 = 100)
CATEGORY_TO_ATTRIBUTE_SCALE = 5  # Scale factor: 1-100 category to 1-20 attribute (100 / 5 = 20)

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
