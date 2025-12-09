# db/connection.py - Database connection and initialization

import os
import sqlite3

from config import DB_PATH


def init_db():
    """Initialize database"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute(
        """CREATE TABLE IF NOT EXISTS players
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT NOT NULL UNIQUE,
                  alias TEXT,
                  height INTEGER,
                  weight INTEGER,
                  position_pref TEXT,
                  team INTEGER,
                  position TEXT,
                  league_id INTEGER,
                  technical_attrs TEXT DEFAULT '{}',
                  mental_attrs TEXT DEFAULT '{}',
                  physical_attrs TEXT DEFAULT '{}',
                  gk_attrs TEXT DEFAULT '{}',
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (league_id) REFERENCES leagues(id))"""
    )

    # Leagues table
    c.execute(
        """CREATE TABLE IF NOT EXISTS leagues
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT NOT NULL UNIQUE,
                  description TEXT,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"""
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
