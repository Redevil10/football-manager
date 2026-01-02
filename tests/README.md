# Tests

This directory contains unit tests for the football-manager application.

## Running Tests

### Run all tests
```bash
pytest
```

### Run with coverage report
```bash
pytest --cov=. --cov-report=html
```

### Run specific test file
```bash
pytest tests/test_scoring.py
```

### Run specific test class or function
```bash
pytest tests/test_scoring.py::TestCalculateOverallScore
pytest tests/test_scoring.py::TestCalculateOverallScore::test_minimum_overall_score
```

### Run with verbose output
```bash
pytest -v
```

### Run tests matching a pattern
```bash
pytest -k "test_calculate"
```

## Test Structure

### Core Logic Tests
- `test_scoring.py` - Tests for scoring calculation logic
- `test_allocation.py` - Tests for team allocation logic
- `test_import_logic.py` - Tests for player import logic (parse_signup_text, import_players)

### Authentication Tests
- `test_auth.py` - Tests for authentication functions (password hashing, verification)
- `test_auth_extended.py` - Extended authentication tests (login, logout, session management, permissions)

### Database Tests
- `test_db_players.py` - Tests for player database operations
- `test_db_clubs_leagues.py` - Tests for club and league database operations
- `test_db_club_leagues.py` - Tests for club-league relationship operations
- `test_db_users.py` - Tests for user database operations
- `test_db_matches.py` - Tests for match database operations
- `test_db_match_players.py` - Tests for match player database operations
- `test_db_match_teams.py` - Tests for match team database operations
- `test_db_match_events.py` - Tests for match event database operations

### Render Tests
- `test_render_common.py` - Tests for common rendering functions
- `test_render_players.py` - Tests for player rendering functions

### Configuration
- `conftest.py` - Pytest fixtures and configuration

## Test Coverage

Current test coverage is approximately **88%+** and includes:

1. **Scoring Logic** (`test_scoring.py`)
   - Category score calculations
   - Overall score calculations with weights
   - Score setting and attribute redistribution
   - Attribute adjustment functions

2. **Import Logic** (`test_import_logic.py`)
   - Parsing signup text from numbered lists
   - Importing players from text
   - Handling existing vs new players

3. **Authentication** (`test_auth.py`, `test_auth_extended.py`)
   - Password hashing and verification
   - Edge cases (empty passwords, special characters, unicode)
   - Session management (get_session_from_request, login_user, logout_user)
   - User access control (get_current_user, get_user_accessible_club_ids)
   - Permission checking (check_club_access, check_club_permission)
   - Match and league edit permissions

4. **Allocation Logic** (`test_allocation.py`)
   - Team balancing algorithms
   - Position distribution
   - Single and two-team allocation logic

5. **Player Database Operations** (`test_db_players.py`)
   - Random attribute generation
   - Player CRUD operations (create, read, update, delete)
   - Finding players by name or alias
   - Team and position updates
   - Attribute updates
   - Player swapping and team reset

6. **Club and League Database Operations** (`test_db_clubs_leagues.py`, `test_db_club_leagues.py`)
   - Club CRUD operations
   - League CRUD operations
   - Club-league relationships (many-to-many)
   - Friendly league creation
   - League filtering by club participation

7. **User Database Operations** (`test_db_users.py`)
   - User CRUD operations
   - User-club relationships with roles
   - Password updates
   - Superuser status management
   - User filtering by clubs

8. **Match Database Operations** (`test_db_matches.py`)
   - Match CRUD operations
   - Match filtering by league and club
   - Next match queries
   - Completed match queries
   - Recent matches queries

9. **Match Player Operations** (`test_db_match_players.py`)
   - Adding players to matches
   - Updating match player assignments
   - Signup player management
   - Player swapping in matches

10. **Match Team Operations** (`test_db_match_teams.py`)
    - Team creation and updates
    - Team captain assignment
    - Score tracking
    - Team deletion

11. **Match Event Operations** (`test_db_match_events.py`)
    - Event creation (goals, assists, etc.)
    - Event retrieval and ordering
    - Event deletion

12. **Rendering Functions** (`test_render_common.py`, `test_render_players.py`)
    - Match name formatting
    - Match completion detection
    - Score display
    - Navigation bar rendering
    - Player table rendering
    - Player detail form rendering
    - Permission-based UI rendering

## Adding New Tests

When adding new tests:

1. Follow the naming convention: `test_*.py` for test files, `test_*` for test functions
2. Use descriptive test names that explain what is being tested
3. Group related tests in test classes
4. Use fixtures from `conftest.py` when appropriate
5. Mock database calls for unit tests (use integration tests for database operations)

## Test Markers

Tests can be marked with:
- `@pytest.mark.unit` - Unit tests (fast, no external dependencies)
- `@pytest.mark.integration` - Integration tests (may use database)
- `@pytest.mark.slow` - Slow running tests

Run only unit tests:
```bash
pytest -m unit
```
