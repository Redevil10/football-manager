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

- `test_scoring.py` - Tests for scoring calculation logic
- `test_auth.py` - Tests for authentication functions (password hashing, verification)
- `test_allocation.py` - Tests for team allocation logic
- `conftest.py` - Pytest fixtures and configuration

## Test Coverage

Current test coverage includes:

1. **Scoring Logic** (`test_scoring.py`)
   - Category score calculations
   - Overall score calculations with weights
   - Score setting and attribute redistribution
   - Attribute adjustment functions

2. **Authentication** (`test_auth.py`)
   - Password hashing
   - Password verification
   - Edge cases (empty passwords, special characters, unicode)

3. **Allocation Logic** (`test_allocation.py`)
   - Team balancing algorithms
   - Position distribution
   - Single and two-team allocation logic

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
