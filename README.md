---
title: Football Manager
emoji: ⚽
colorFrom: indigo
colorTo: red
sdk: docker
app_port: 7860
pinned: false
license: agpl-3.0
short_description: Manage football teams, allocate players, track matches
---

<p align="center">
  <img src="static/logo.svg" width="120" alt="Football Manager logo">
</p>

<h1 align="center">Football Manager</h1>

[![lint](https://github.com/Redevil10/football-manager/actions/workflows/lint.yml/badge.svg)](https://github.com/Redevil10/football-manager/actions/workflows/lint.yml)
[![unit tests](https://github.com/Redevil10/football-manager/actions/workflows/unit-test.yml/badge.svg)](https://github.com/Redevil10/football-manager/actions/workflows/unit-test.yml)
[![e2e tests](https://github.com/Redevil10/football-manager/actions/workflows/e2e-test.yml/badge.svg)](https://github.com/Redevil10/football-manager/actions/workflows/e2e-test.yml)
[![codecov](https://codecov.io/github/Redevil10/football-manager/graph/badge.svg?token=WNC4Z8DSH0)](https://codecov.io/gh/Redevil10/football-manager)
[![python](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/downloads/)

A web app for managing amateur football rosters, balancing teams, and tracking matches.

**Live Demo**: [redevil10-football-manager.hf.space](https://redevil10-football-manager.hf.space/) — click **Browse Public Leagues** to explore (no sign-in needed)

## Features

- **Player Management** — Add/edit players with 41 attributes across Technical, Mental, Physical, and Goalkeeper categories
- **Team Allocation** — Auto-balance players into teams based on overall scores, with a visual formation pitch
- **Match Tracking** — Create matches, import signups, record scores, goals/assists/events, and recording links
- **Signup Name Matching** — People sign up under nicknames and misspellings; hand-match one once and it is remembered as an alias, so the same spelling matches by itself next time
- **Leagues & Clubs** — Multi-club support with role-based access (viewer/manager/admin/superuser)
- **Public Sharing** — Share a league read-only with anyone, no account needed; player ratings are never exposed
- **Smart Import** — AI-powered signup parsing via Gemini API (optional)
- **Persistent Storage** — Auto-backup to Hugging Face Datasets every 15 minutes

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastHTML (Python 3.13+) |
| Database | SQLite + HF Datasets backup |
| Frontend | HTML + HTMX |
| Deployment | Docker on Hugging Face Spaces |
| Package Manager | uv |

## Quick Start

```bash
# Install dependencies
uv sync --extra dev

# Run locally (http://localhost:8000)
uv run python main.py

# Same, reloading on every save
uv run uvicorn main:app --reload

# Unit tests (e2e are excluded by default -- see pytest.ini)
uv run pytest

# End-to-end tests (needs `uv run playwright install chromium` once)
uv run pytest -m e2e

# Lint & format
uv run ruff check . --fix && uv run ruff format .
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `HF_TOKEN` | On HF Spaces | Hugging Face backup token |
| `SECRET_KEY` | No | Session secret (auto-generated if unset) |
| `GEMINI_API_KEY` | No | Enables AI-powered Smart Import |

## Project Structure

```
├── main.py              # Entry point
├── core/                # Config, styles, auth utilities
├── db/                  # Database operations (SQLite)
├── logic/               # Business logic (scoring, allocation, import)
├── render/              # HTML rendering functions
├── routes/              # HTTP route handlers
├── migrations/          # Database migrations
├── static/              # Logo, favicon, social preview
└── tests/               # pytest test suite
```

## Deploying

The app is a Docker Space on Hugging Face. Pushing to `main` does not deploy on
its own — trigger the **deploy-hf** workflow by hand.

**After any deploy that adds a column, open `/migration` on the running Space.**
`CREATE TABLE IF NOT EXISTS` never alters a table that already exists, so a
live database keeps its old shape until that page is opened; pages that read a
new column error until it is. The migration steps are in
[migrations/migrate_all.py](migrations/migrate_all.py) and every one of them is
safe to re-run.

## How Team Allocation Works

Players are sorted by overall score (10–200), then distributed to minimize the score gap between teams. Players beyond the team capacity become substitutes, split evenly.

## Deleting Things

Nothing is deleted from the page you are reading. Every delete is a link to a
confirmation page that names what is about to go, and that page holds the only
button that does it.

- **Players** who have played are **archived**, not deleted — `match_players`
  stores only an id, so deleting the row would take their name out of every
  line-up they were ever on. Archived players leave the squad, the signup
  lookup and team allocation, keep the matches they played, and can be
  restored. A player with no appearances is deleted outright.
- **Leagues with matches** and **clubs with players** cannot be deleted at all
  until they are empty: their contents have no ON DELETE clause behind them and
  would be left stranded. The confirmation page says so instead of offering a
  button.
- Removing a player from the club is an admin/superuser action; managers run
  the team but do not take people off the books.

## License

AGPL-3.0 — see [LICENSE](LICENSE) for details.
