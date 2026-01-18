# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Working Directory Convention

**IMPORTANT**: Always make code changes in the main repository directory:

```
/Users/qing.wan/Library/CloudStorage/OneDrive-Qantas/Desktop/Redevil10/football-manager
```

- Do NOT make changes in worktree directories (e.g., `~/.claude-worktrees/football-manager/*`) unless specifically requested
- This ensures consistency and avoids confusion about which files are canonical
- The main repository is the source of truth for all deployments

## Development Commands

### Running the Application
```bash
# Run locally (recommended with uv)
uv run python main.py

# Direct Python execution
python main.py
```

The app will be available at `http://localhost:8000`.

### Testing

```bash
# Run all tests
uv run pytest

# Run with coverage report
uv run pytest --cov=. --cov-report=html

# Run specific test file
uv run pytest tests/test_scoring.py

# Run specific test class or function
uv run pytest tests/test_scoring.py::TestCalculateOverallScore
uv run pytest tests/test_scoring.py::TestCalculateOverallScore::test_minimum_overall_score

# Run tests matching a pattern
uv run pytest -k "test_calculate"

# Run tests by marker
uv run pytest -m unit
```

### Dependency Management

Dependencies are managed in `pyproject.toml` (source of truth). The `requirements.txt` is auto-generated.

**To update dependencies:**
1. Edit `pyproject.toml` to add/update/remove packages
2. Regenerate `requirements.txt`: `uv export > requirements.txt`
3. Install updated dependencies: `uv sync --extra dev`

**Never manually edit `requirements.txt`** - it will be overwritten.

### Linting

The project uses Ruff for linting. Special configuration in `pyproject.toml`:
- F403 and F405 are ignored for FastHTML star imports
- FastHTML is designed to work with `from fasthtml.common import *`

## Architecture Overview

### Application Entry Point

- **main.py**: Minimal entry point that imports the FastHTML app from `routes/__init__.py`
- **routes/__init__.py**: App initialization, middleware configuration, HF Spaces backup setup, database initialization, and route registration

### Multi-Tenant Architecture

The application uses a **multi-club system**:
- Each **club** is an independent tenant with isolated data
- **Users** can belong to multiple clubs with different roles per club
- **Players**, **matches**, and **leagues** are scoped to clubs
- **Leagues** can be shared across multiple clubs (many-to-many via `club_leagues` table)

### Authentication & Authorization

Located in `core/auth.py`:
- **bcrypt** password hashing with SHA256 preprocessing for long passwords (>72 bytes)
- **Session-based authentication** via FastHTML's session middleware
- **Role-based access control**: Users have roles per club (viewer/manager)
  - **Viewer**: Read-only access to club data
  - **Manager**: Full CRUD access to club data
- **Superuser**: Can access all clubs and manage users

**Important session configuration**:
- HF Spaces deployment requires `same_site="none"` and `https_only=True` for iframe support
- Local development uses `same_site="lax"` and `https_only=False`
- Session middleware is manually configured in `routes/__init__.py` to support both environments

### Database Architecture

**SQLite database** (`data/football_manager.db`) with automatic HF Spaces backup.

**Core tables**:
- `users`: User accounts with password hashes
- `clubs`: Independent tenant organizations
- `user_clubs`: Many-to-many relationship with roles (viewer/manager)
- `players`: Player data scoped to clubs (name unique per club)
- `leagues`: Independent entities (can be shared across clubs)
- `club_leagues`: Many-to-many relationship between clubs and leagues
- `matches`: Match records linked to leagues
- `match_teams`: Teams within a match
- `match_players`: Player assignments within matches
- `match_events`: Goals, assists, and other match events

**Database operations** are organized in `db/` modules:
- Each table has its own module (e.g., `db/players.py`, `db/matches.py`)
- `db/connection.py`: Database initialization and connection
- `db/__init__.py`: Central export point for all database functions
- All database operations use **context managers** for transaction safety

### Player Scoring System

Located in `logic/scoring.py` and configured in `core/config.py`:

**Attribute categories** (1-20 scale each):
- **Technical**: 14 attributes (corners, crossing, dribbling, finishing, etc.)
- **Mental**: 14 attributes (aggression, anticipation, composure, etc.)
- **Physical**: 8 attributes (acceleration, agility, pace, stamina, etc.)
- **Goalkeeper**: 5 attributes (handling, reflexes, diving, etc.)

**Score calculations**:
- **Category scores** (5-100): Average of attributes × 5
- **Overall score** (10-200): Weighted sum of category scores ÷ 5
  - Weights: Technical×3 + Mental×2 + Physical×3 + GK×2
- Setting a category score redistributes all attributes proportionally
- Setting overall score redistributes all category scores proportionally

### Team Allocation Algorithm

Located in `logic/allocation.py`:

**Purpose**: Balance players across teams based on overall scores.

**Process**:
1. Sort players by overall score
2. Distribute by position (40% defenders, 35% midfielders, 1 GK per team)
3. Iteratively balance teams to minimize score difference
4. Excess players become substitutes (evenly distributed)
5. Maximum 100 iterations for optimization

### Route Organization

Routes are organized by feature in `routes/`:
- `auth.py`: Login, logout, session management
- `clubs.py`: Club CRUD and management
- `home.py`: Home page and navigation
- `leagues.py`: League CRUD
- `matches.py`: Match CRUD, team allocation, match events
- `players.py`: Player CRUD, attributes, import from text
- `users.py`: User CRUD, club assignments, role management
- `migration.py`: Database migration routes

**All routes register** in `routes/__init__.py` after app initialization to avoid circular dependencies.

### Rendering Functions

Located in `render/`:
- `common.py`: Shared utilities (navbar, match name formatting, completion detection)
- `players.py`: Player tables, forms, detail views
- `matches.py`: Match lists, team displays, event lists
- `leagues.py`: League displays

**Pattern**: Render functions accept permission parameters to conditionally show edit/delete buttons based on user role.

### Player Import Feature

Located in `logic/import_logic.py`:

**Parse signup text** from numbered lists:
```
1. John Doe
2. Jane Smith
```

- Automatically finds/creates players by name or alias
- Returns list of player IDs for match assignment
- Handles both existing players and new player creation

### Configuration & Validation

- `core/config.py`: All constants (attributes, score ranges, weights, DB path)
- `core/validation.py`: Input validation utilities
- `core/exceptions.py`: Custom exception classes
- `core/error_handling.py`: Error handling utilities
- `core/styles.py`: CSS styles for the application

### Hugging Face Spaces Deployment

The app is designed for HF Spaces deployment:
- **Dockerfile**: Container configuration
- **config.ini**: `fasthtml-hf` backup configuration
- **HF_TOKEN**: Required environment variable for database backup
- **SECRET_KEY**: Optional environment variable for session persistence
- Automatic database backup every 15 minutes
- Database restored on application startup

### Migration System

Located in `migrations/`:
- Manual migration scripts for schema changes
- `migration.py`: Base migration utilities
- Each migration is a separate file (e.g., `migrate_auth.py`)
- Migrations are run via `/migration` routes

## Testing Architecture

**88%+ test coverage** across:
- **Core logic**: Scoring, allocation, import
- **Authentication**: Password hashing, session management, permissions
- **Database operations**: All CRUD operations for all tables
- **Rendering**: Common utilities and permission-based rendering
- **Error handling**: Validation and error cases

**Test organization**:
- `conftest.py`: Shared fixtures (test database, test users, test clubs)
- `test_*.py`: Feature-specific test files
- Use `@pytest.mark.unit`, `@pytest.mark.integration`, `@pytest.mark.slow` markers

**Test database**:
- Tests use an in-memory SQLite database
- Isolated from production database
- Fixtures automatically set up and tear down test data

## Important Notes

### FastHTML Star Imports
The codebase uses `from fasthtml.common import *` extensively. This is the intended FastHTML pattern and linting rules are configured to allow it.

### Database Transactions
All database operations use context managers (`with get_db() as conn`) for automatic transaction management and rollback on errors.

### Role-Based Permissions
Always check user permissions before allowing modifications:
- Use `check_club_permission()` for club-level operations
- Use `check_match_edit_permission()` for match operations
- Use `check_league_edit_permission()` for league operations

### Player Names and Aliases
Players are identified by name (required) or alias (optional). When importing players from text, the system searches both fields to find existing players.

### League Sharing
A league can be shared across multiple clubs through the `club_leagues` many-to-many relationship. When filtering matches by club, use the league IDs associated with that club.
