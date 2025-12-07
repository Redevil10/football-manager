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
    "overall": (1, 200),  # 综合总分
    "technical": (1, 60),  # 进攻和防守
    "mental": (1, 40),  # 精神
    "physical": (1, 60),  # 身体
    "gk": (1, 40),  # 守门
    "attribute": (1, 20),  # 单个属性
}
