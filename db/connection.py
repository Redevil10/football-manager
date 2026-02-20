# db/connection.py - Database connection and initialization

import logging
import os
import sqlite3
import uuid
from datetime import date, timedelta

from core.config import DB_PATH, USER_ROLES

logger = logging.getLogger(__name__)


def init_db():
    """Initialize database"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Users table
    c.execute(
        """CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT NOT NULL UNIQUE,
                  email TEXT,
                  password_hash TEXT NOT NULL,
                  password_salt TEXT NOT NULL,
                  is_superuser INTEGER DEFAULT 0,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  last_login TIMESTAMP)"""
    )

    # Clubs table
    c.execute(
        """CREATE TABLE IF NOT EXISTS clubs
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT NOT NULL UNIQUE,
                  description TEXT,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"""
    )

    # User-Club relationship (many-to-many with role)
    c.execute(
        """CREATE TABLE IF NOT EXISTS user_clubs
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER NOT NULL,
                  club_id INTEGER NOT NULL,
                  role TEXT NOT NULL CHECK(role IN ('viewer', 'manager', 'admin')),
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                  FOREIGN KEY (club_id) REFERENCES clubs(id) ON DELETE CASCADE,
                  UNIQUE(user_id, club_id))"""
    )

    c.execute(
        """CREATE TABLE IF NOT EXISTS players
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT NOT NULL,
                  alias TEXT,
                  height INTEGER,
                  weight INTEGER,
                  position_pref TEXT,
                  team INTEGER,
                  position TEXT,
                  club_id INTEGER,
                  technical_attrs TEXT DEFAULT '{}',
                  mental_attrs TEXT DEFAULT '{}',
                  physical_attrs TEXT DEFAULT '{}',
                  gk_attrs TEXT DEFAULT '{}',
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (club_id) REFERENCES clubs(id),
                  UNIQUE(name, club_id))"""
    )

    # Leagues table (independent entities, not tied to a single club)
    c.execute(
        """CREATE TABLE IF NOT EXISTS leagues
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT NOT NULL UNIQUE,
                  description TEXT,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"""
    )

    # Club-League relationship (many-to-many)
    c.execute(
        """CREATE TABLE IF NOT EXISTS club_leagues
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  club_id INTEGER NOT NULL,
                  league_id INTEGER NOT NULL,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (club_id) REFERENCES clubs(id) ON DELETE CASCADE,
                  FOREIGN KEY (league_id) REFERENCES leagues(id) ON DELETE CASCADE,
                  UNIQUE(club_id, league_id))"""
    )

    # Matches table (linked to leagues)
    c.execute(
        """CREATE TABLE IF NOT EXISTS matches
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  league_id INTEGER,
                  date TEXT,
                  start_time TEXT,
                  end_time TEXT,
                  location TEXT,
                  num_teams INTEGER DEFAULT 2,
                  max_players_per_team INTEGER,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (league_id) REFERENCES leagues(id))"""
    )

    # Match teams table
    c.execute(
        """CREATE TABLE IF NOT EXISTS match_teams
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  match_id INTEGER NOT NULL,
                  team_number INTEGER NOT NULL,
                  team_name TEXT,
                  jersey_color TEXT,
                  score INTEGER DEFAULT 0,
                  captain_id INTEGER,
                  should_allocate INTEGER DEFAULT 1,
                  FOREIGN KEY (match_id) REFERENCES matches(id) ON DELETE CASCADE,
                  FOREIGN KEY (captain_id) REFERENCES match_players(id),
                  UNIQUE(match_id, team_number))"""
    )

    # Match players table (players in a specific match)
    c.execute(
        """CREATE TABLE IF NOT EXISTS match_players
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  match_id INTEGER NOT NULL,
                  player_id INTEGER NOT NULL,
                  team_id INTEGER,
                  position TEXT,
                  tactical_position TEXT,
                  is_starter INTEGER DEFAULT 0,
                  rating REAL,
                  FOREIGN KEY (match_id) REFERENCES matches(id) ON DELETE CASCADE,
                  FOREIGN KEY (player_id) REFERENCES players(id),
                  FOREIGN KEY (team_id) REFERENCES match_teams(id),
                  UNIQUE(match_id, player_id))"""
    )

    # App settings table (key-value store)
    c.execute(
        """CREATE TABLE IF NOT EXISTS app_settings
                 (key TEXT PRIMARY KEY,
                  value TEXT NOT NULL)"""
    )

    # Match events table (goals, assists, etc.)
    c.execute(
        """CREATE TABLE IF NOT EXISTS match_events
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  match_id INTEGER NOT NULL,
                  event_type TEXT NOT NULL,
                  player_id INTEGER,
                  team_id INTEGER,
                  minute INTEGER,
                  description TEXT,
                  FOREIGN KEY (match_id) REFERENCES matches(id) ON DELETE CASCADE,
                  FOREIGN KEY (player_id) REFERENCES players(id),
                  FOREIGN KEY (team_id) REFERENCES match_teams(id))"""
    )

    conn.commit()
    conn.close()

    ensure_demo_user()


def ensure_demo_user():
    """Ensure the DemoUser and Demo Club exist for guest login."""
    from core.auth import hash_password
    from db.clubs import create_club, get_club_by_name
    from db.users import add_user_to_club, create_user, get_user_by_username

    # Create Demo Club if it doesn't exist
    demo_club = get_club_by_name("Demo Club")
    if not demo_club:
        club_id = create_club("Demo Club", "Demo club for guest visitors")
        if not club_id:
            logger.warning("Failed to create Demo Club")
            return
    else:
        club_id = demo_club["id"]

    # Create DemoUser if it doesn't exist
    demo_user = get_user_by_username("DemoUser")
    if not demo_user:
        random_password = uuid.uuid4().hex
        password_hash, password_salt = hash_password(random_password)
        user_id = create_user("DemoUser", password_hash, password_salt, None, False)
        if not user_id:
            logger.warning("Failed to create DemoUser")
            return
        add_user_to_club(user_id, club_id, USER_ROLES["VIEWER"])
        logger.info("Created DemoUser with viewer role for Demo Club")

    _setup_demo_data(club_id)


def _setup_demo_data(club_id):
    """Populate Demo Club with sample players, league, and match."""
    from db.club_leagues import add_club_to_league
    from db.leagues import create_league
    from db.match_players import add_match_player
    from db.match_teams import create_match_team
    from db.matches import create_match, delete_match, get_matches_by_league
    from db.players import add_player_with_score, get_all_players
    from examples.demo_players import DEMO_PLAYERS
    from logic.allocation import allocate_match_teams

    # a) Create "Demo League" if it doesn't exist
    conn = get_db()
    league_row = conn.execute(
        "SELECT id FROM leagues WHERE name = 'Demo League'"
    ).fetchone()
    conn.close()

    if league_row:
        league_id = league_row["id"]
    else:
        league_id = create_league("Demo League", "Demo league for guest visitors")
        if not league_id:
            logger.warning("Failed to create Demo League")
            return
        add_club_to_league(club_id, league_id)

    # b) Create 28 players (one-time)
    existing_players = get_all_players([club_id])
    if not existing_players:
        for name, score in DEMO_PLAYERS:
            add_player_with_score(name, club_id, score)

    # c) Ensure a future match exists
    matches = get_matches_by_league(league_id)
    today = date.today().isoformat()
    has_future_match = any(m.get("date", "") >= today for m in matches)

    if not has_future_match:
        # Delete old demo matches for this league
        for m in matches:
            delete_match(m["id"])

        # Create a match 1 year from today
        future_date = (date.today() + timedelta(days=365)).isoformat()
        match_id = create_match(
            league_id,
            date=future_date,
            start_time="14:00:00",
            end_time="16:00:00",
            location="Demo Stadium",
            num_teams=2,
            max_players_per_team=11,
        )

        create_match_team(match_id, 1, "Team A", "Red")
        create_match_team(match_id, 2, "Team B", "Blue")

        # Sign up all players
        players = get_all_players([club_id])
        for player in players:
            add_match_player(match_id, player["id"])

        # Auto-balance into teams
        allocate_match_teams(match_id)


def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn
