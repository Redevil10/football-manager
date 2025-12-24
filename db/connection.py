# db/connection.py - Database connection and initialization

import os
import sqlite3

from core.config import DB_PATH


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
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"""
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
                  role TEXT NOT NULL CHECK(role IN ('viewer', 'manager')),
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
                  is_starter INTEGER DEFAULT 0,
                  rating REAL,
                  FOREIGN KEY (match_id) REFERENCES matches(id) ON DELETE CASCADE,
                  FOREIGN KEY (player_id) REFERENCES players(id),
                  FOREIGN KEY (team_id) REFERENCES match_teams(id),
                  UNIQUE(match_id, player_id))"""
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


def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn
