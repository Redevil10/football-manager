---
title: Football Manager
emoji: ⚽
colorFrom: indigo
colorTo: red
sdk: docker
app_port: 7860
pinned: false
license: mit
short_description: Manage football teams, allocate players, track matches
---

# ⚽ Football Manager

[![lint](https://github.com/Redevil10/football-manager/actions/workflows/lint.yml/badge.svg)](https://github.com/Redevil10/football-manager/actions/workflows/lint.yml)
[![tests](https://github.com/Redevil10/football-manager/actions/workflows/test.yml/badge.svg)](https://github.com/Redevil10/football-manager/actions/workflows/test.yml)
[![codecov](https://codecov.io/github/Redevil10/football-manager/graph/badge.svg?token=WNC4Z8DSH0)](https://codecov.io/gh/Redevil10/football-manager)
[![python](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/downloads/)

A comprehensive web application for managing amateur football team rosters, allocating players into balanced teams, and tracking match history.

## Features

- **Player Management** - Add, edit, and manage players with detailed attributes (Technical, Mental, Physical, Goalkeeper)
- **Team Allocation** - Intelligently balance players across teams based on overall scores
- **Match Management** - Create and manage matches with leagues, teams, rosters, and scores
- **League System** - Organize matches into leagues (including "Friendly" matches)
- **Player Attributes** - Detailed scoring system with 1-20 scale attributes and 1-100 category scores
- **Match Events** - Track goals, assists, and other match events
- **Persistent Storage** - Data automatically backed up to Hugging Face Datasets

## Tech Stack

- **Backend**: FastHTML (Python)
- **Database**: SQLite with automatic backup via `fasthtml-hf`
- **Frontend**: HTML + HTMX
- **Deployment**: Docker on Hugging Face Spaces

## Quick Start

### Local Development

**Requirements**: Python 3.13+

### Using uv (recommended)

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies (including dev dependencies for testing)
uv sync --extra dev

# Run directly
uv run python main.py
```

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=. --cov-report=html

# Run specific test file
uv run pytest tests/test_scoring.py
```

See [tests/README.md](tests/README.md) for more testing information.

## Usage

### Player Management

- **Add Players**: Navigate to Players page and click "Add Player"
- **Edit Attributes**: Click on a player to edit their technical, mental, physical, and goalkeeper attributes
- **Overall Score**: Adjust overall score (10-200) and all attributes will scale proportionally
- **Category Scores**: Modify category scores (5-100) to adjust all attributes in that category

### Match Management

- **Create Match**: Go to Matches page and click "Create Match"
- **Import Players**: Import players from signup text for a specific match
- **Allocate Teams**: Automatically balance players into teams based on overall scores
- **Track Events**: Add goals, assists, and other match events
- **View History**: Browse past matches by league

### League System

- **Create Leagues**: Organize matches into leagues
- **Friendly Matches**: Default league for casual matches
- **Match History**: View all matches within a league

## How Team Allocation Works

- Players are sorted by overall score (10-200 range)
- Teams are balanced to minimize score difference
- Supports 1 or 2 team matches
- Players exceeding team capacity are designated as substitutes
- Substitutes are evenly distributed between teams

## Data Persistence

This application uses `fasthtml-hf` for automatic database backup:
- Database is automatically backed up to Hugging Face Datasets every 15 minutes
- Data is restored on application startup
- **Required**: Set `HF_TOKEN` as a Secret in your Hugging Face Space settings

## Configuration

The app runs on:
- **Local**: `http://localhost:7860`
- **Hugging Face Spaces**: `http://yourspace.hf.space` (port 7860)

## Testing

The project includes comprehensive unit tests:

- **Scoring Logic** - Tests for player score calculations
- **Authentication** - Tests for password hashing and verification
- **Team Allocation** - Tests for team balancing algorithms

Tests run automatically on GitHub Actions for all pushes and pull requests.

## CI/CD

GitHub Actions workflows are configured to:
- Run tests on Python 3.13
- Generate coverage reports
- Upload coverage artifacts

See [.github/workflows/README.md](.github/workflows/README.md) for workflow details.

## File Structure

```
football-manager/
├── main.py          # Main FastHTML application
├── db/              # Database operations
├── logic/           # Business logic (team allocation, scoring)
├── render/          # HTML rendering functions
├── core/            # Core utilities (auth, config, styles)
├── routes/          # Route handlers
├── tests/           # Unit tests
├── pyproject.toml   # Project configuration and dependencies
├── Dockerfile       # Docker configuration
├── config.ini       # fasthtml-hf configuration
└── README.md        # This file
```

## License

MIT License - feel free to use and modify
