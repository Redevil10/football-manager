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

# Run directly
uv run python main.py
```

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

## File Structure

```
football-manager/
├── main.py          # Main FastHTML application
├── db.py            # Database operations
├── logic.py         # Business logic (team allocation, scoring)
├── render.py        # HTML rendering functions
├── config.py        # Configuration and constants
├── styles.py        # CSS styles
├── requirements.txt # Python dependencies
├── Dockerfile       # Docker configuration
├── config.ini       # fasthtml-hf configuration
└── README.md        # This file
```

## License

MIT License - feel free to use and modify
