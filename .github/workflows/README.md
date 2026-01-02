# GitHub Actions Workflows

This directory contains GitHub Actions workflows for CI/CD.

## Available Workflows

### `test.yml`
Main test workflow that:
- Runs on push/PR to main/master/develop branches
- Tests on Python 3.13
- Uses `uv` for dependency management
- Runs pytest with coverage
- Uploads coverage to Codecov (optional)

## Usage

The workflows will automatically run when:
- Code is pushed to `main`, `master`, or `develop` branches
- Pull requests are opened/updated to these branches
- Manually triggered via GitHub Actions UI (workflow_dispatch)

## Requirements

- Python 3.13
- `uv` package manager
- Dependencies defined in `pyproject.toml`

## Coverage Reports

Coverage reports are generated in multiple formats:
- Terminal output (always)
- XML format (`coverage.xml`) for Codecov
- HTML format (`htmlcov/`) for detailed browsing

HTML reports are uploaded as artifacts and can be downloaded from the workflow run page.
