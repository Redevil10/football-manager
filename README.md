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

A web app for managing amateur football rosters, balancing teams, and tracking matches. Installable as a PWA on mobile devices.

**Live Demo**: [redevil10-football-manager.hf.space](https://redevil10-football-manager.hf.space/) — login with `TestUser` / `TestUser`

## Features

- **Player Management** — Add/edit players with 41 attributes across Technical, Mental, Physical, and Goalkeeper categories
- **Team Allocation** — Auto-balance players into teams based on overall scores
- **Match Tracking** — Create matches, import signups, record goals/assists/events
- **Leagues & Clubs** — Multi-club support with role-based access (viewer/manager/admin)
- **Smart Import** — AI-powered signup parsing via Gemini API (optional)
- **PWA Support** — Installable on mobile with offline caching for static assets
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

# Run tests
uv run pytest

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
├── static/              # PWA manifest, service worker, icons
├── migrations/          # Database migrations
└── tests/               # pytest test suite
```

## How Team Allocation Works

Players are sorted by overall score (10–200), then distributed to minimize the score gap between teams. Players beyond the team capacity become substitutes, split evenly.

## License

MIT
