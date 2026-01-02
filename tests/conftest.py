"""Pytest configuration and fixtures"""

import os
import shutil
import tempfile

import pytest


@pytest.fixture
def temp_db_path():
    """Create a temporary database path for testing"""
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "test_football_manager.db")
    yield db_path
    # Cleanup
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)


@pytest.fixture
def temp_db(monkeypatch, temp_db_path):
    """Create a temporary database for testing"""
    import core.config
    import db.connection

    monkeypatch.setattr(core.config, "DB_PATH", temp_db_path)
    monkeypatch.setattr(db.connection, "DB_PATH", temp_db_path)

    from db.connection import init_db

    init_db()
    yield temp_db_path


@pytest.fixture
def sample_player():
    """Create a sample player dict for testing"""
    return {
        "id": 1,
        "name": "Test Player",
        "technical_attrs": {
            "passing": 15,
            "dribbling": 15,
            "finishing": 15,
        },
        "mental_attrs": {
            "composure": 12,
            "decisions": 12,
            "determination": 12,
        },
        "physical_attrs": {
            "pace": 10,
            "strength": 10,
            "stamina": 10,
        },
        "gk_attrs": {
            "handling": 8,
            "reflexes": 8,
            "diving": 8,
        },
    }


@pytest.fixture
def sample_players():
    """Create multiple sample players for testing"""
    return [
        {
            "id": 1,
            "name": "Player 1",
            "technical_attrs": {"passing": 20, "dribbling": 20},
            "mental_attrs": {"composure": 20, "decisions": 20},
            "physical_attrs": {"pace": 20, "strength": 20},
            "gk_attrs": {"handling": 20, "reflexes": 20},
        },
        {
            "id": 2,
            "name": "Player 2",
            "technical_attrs": {"passing": 15, "dribbling": 15},
            "mental_attrs": {"composure": 15, "decisions": 15},
            "physical_attrs": {"pace": 15, "strength": 15},
            "gk_attrs": {"handling": 15, "reflexes": 15},
        },
        {
            "id": 3,
            "name": "Player 3",
            "technical_attrs": {"passing": 10, "dribbling": 10},
            "mental_attrs": {"composure": 10, "decisions": 10},
            "physical_attrs": {"pace": 10, "strength": 10},
            "gk_attrs": {"handling": 10, "reflexes": 10},
        },
    ]
