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

## Live Demo

Try the live demo at: **[https://redevil10-football-manager.hf.space/](https://redevil10-football-manager.hf.space/)**

**Test Account Credentials:**
- **Username**: `TestUser`
- **Password**: `TestUser`

Feel free to explore the application with this demo account. You can view matches, player rosters, and all other features in read-only mode.

## Features

- **Player Management** - Add, edit, and manage players with detailed attributes (Technical, Mental, Physical, Goalkeeper)
- **Team Allocation** - Intelligently balance players across teams based on overall scores
- **Match Management** - Create and manage matches with leagues, teams, rosters, and scores
- **League System** - Organize matches into leagues (including "Friendly" matches)
- **Player Attributes** - Detailed scoring system with 1-20 scale attributes and 1-100 category scores
- **Match Events** - Track goals, assists, and other match events
- **Multi-Club Support** - Organize players, matches, and leagues by club with role-based access control
- **Club Selector** - Switch between clubs from the navbar; superusers can view all clubs or filter by one
- **Smart Import (AI)** - Use Gemini API to intelligently parse free-text player signups into structured player data
- **Authentication & Authorization** - Secure user authentication with bcrypt password hashing and role-based permissions (viewer/manager)
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

### Managing Dependencies

Dependencies are managed in `pyproject.toml` (the source of truth). The `requirements.txt` file is auto-generated for compatibility with Docker and CI/CD systems.

**To update dependencies:**

1. Edit `pyproject.toml` to add/update/remove packages
2. Regenerate `requirements.txt`:
   ```bash
   uv export > requirements.txt
   ```
3. Install updated dependencies:
   ```bash
   uv sync --extra dev
   ```

**Note**: Never manually edit `requirements.txt` - it will be overwritten when regenerated.

## Usage

### Authentication

- **User Accounts**: Create user accounts with username and password
- **Role-Based Access**: Users can have different roles per club:
  - **Viewer**: Read-only access to club data
  - **Manager**: Full access to create, edit, and manage club data
- **Club Membership**: Users can belong to multiple clubs with different roles in each

### Club Management

- **Create Clubs**: Organize players, matches, and leagues by club
- **Multi-Tenant**: Each club has its own isolated data (players, matches, leagues)
- **User Assignment**: Assign users to clubs with appropriate roles

### Player Management

- **Add Players**: Navigate to Players page and click "Add Player" (players are club-specific)
- **Edit Attributes**: Click on a player to edit their technical, mental, physical, and goalkeeper attributes
- **Overall Score**: Adjust overall score (10-200) and all attributes will scale proportionally
- **Category Scores**: Modify category scores (5-100) to adjust all attributes in that category

### Match Management

- **Create Match**: Go to Matches page and click "Create Match" (matches are club-specific)
- **Import Players**: Import players from signup text for a specific match
- **Allocate Teams**: Automatically balance players into teams based on overall scores
- **Track Events**: Add goals, assists, and other match events
- **View History**: Browse past matches by league

### League System

- **Create Leagues**: Organize matches into leagues (leagues are club-specific)
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

### Application Configuration

Configuration constants are defined in `core/config.py`:
- Player attributes (Technical, Mental, Physical, Goalkeeper)
- Scoring ranges and calculation weights
- Team allocation parameters
- User roles and permissions

### Runtime Configuration

The app runs on:
- **Local**: `http://localhost:8000`

### Environment Variables

- `HF_TOKEN` - Required for Hugging Face Spaces backup (set as Secret in Space settings)
- `SECRET_KEY` - Optional session secret key (auto-generated if not set)
- `GEMINI_API_KEY` - Optional, enables Smart Import (AI-powered player signup parsing via Gemini API)

## Testing

The project includes comprehensive unit tests:

- **Scoring Logic** - Tests for player score calculations
- **Authentication** - Tests for password hashing, verification, and role-based access control
- **Team Allocation** - Tests for team balancing algorithms
- **Database Operations** - Tests for all database modules
- **Error Handling** - Tests for error handling and validation
- **Import Logic** - Tests for player import functionality

Tests run automatically on GitHub Actions for all pushes and pull requests.

See [tests/README.md](tests/README.md) for detailed testing information.

### Running Tests Locally

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=. --cov-report=html

# Run specific test file
uv run pytest tests/test_scoring.py
```

## CI/CD

GitHub Actions workflows are configured to:
- Run tests on Python 3.13
- Generate coverage reports
- Upload coverage artifacts

See [.github/workflows/README.md](.github/workflows/README.md) for workflow details.

## File Structure

```
football-manager/
├── main.py              # Main FastHTML application entry point
├── config.ini           # fasthtml-hf backup configuration
├── pyproject.toml       # Project configuration and dependencies
├── pytest.ini          # Pytest configuration
├── Dockerfile           # Docker configuration for deployment
├── requirements.txt     # Python dependencies (auto-generated by uv)
├── uv.lock              # Dependency lock file (uv)
├── core/                # Core utilities and configuration
│   ├── auth.py          # Authentication and authorization
│   ├── config.py        # Application configuration and constants
│   ├── error_handling.py # Error handling utilities
│   ├── exceptions.py    # Custom exceptions
│   ├── styles.py        # CSS styles
│   └── validation.py    # Input validation utilities
├── db/                  # Database operations
│   ├── connection.py    # Database connection and initialization
│   ├── clubs.py         # Club database operations
│   ├── players.py       # Player database operations
│   ├── matches.py       # Match database operations
│   ├── leagues.py       # League database operations
│   ├── users.py         # User database operations
│   └── ...              # Other database modules
├── logic/               # Business logic
│   ├── allocation.py    # Team allocation algorithms
│   ├── scoring.py       # Player scoring calculations
│   └── import_logic.py  # Player import logic
├── render/              # HTML rendering functions
│   ├── common.py        # Common rendering utilities
│   ├── players.py       # Player rendering
│   ├── matches.py       # Match rendering
│   └── leagues.py       # League rendering
├── routes/              # Route handlers
│   ├── __init__.py      # Route registration and app setup
│   ├── auth.py          # Authentication routes
│   ├── players.py       # Player routes
│   ├── matches.py       # Match routes
│   ├── leagues.py       # League routes
│   ├── clubs.py         # Club routes
│   └── users.py         # User management routes
├── migrations/          # Database migration scripts
│   └── ...              # Migration scripts
├── tests/               # Unit tests
│   ├── conftest.py      # Pytest configuration
│   └── test_*.py        # Test files
└── README.md           # This README file
```

## License

MIT License - feel free to use and modify
