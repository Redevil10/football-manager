# ⚽ Football Manager

A lightweight web application for managing amateur football team rosters and allocating players into balanced teams.

## Features

- **Import Players** - Paste signup lists and automatically extract player names and match info
- **Player Management** - Add, delete, and manage players with skill levels (Weak, Medium, Strong)
- **Auto Team Allocation** - Intelligently balance players across two teams based on skill levels
- **Position Assignment** - Automatically assign positions (Goalkeeper, Defender, Midfielder, Forward)
- **Match Info Display** - Shows match date, time, and location extracted from signup lists
- **Simple UI** - Clean, intuitive web interface with no complex setup

## Tech Stack

- **Backend**: FastHTML (Python)
- **Database**: SQLite
- **Frontend**: HTML + HTMX
- **Deployment**: Docker (Hugging Face Spaces / GitHub)

## Quick Start

### Local Development

**Requirements**: Python 3.13+

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/football-manager.git
cd football-manager
```

2. **Create virtual environment**
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Run the app**
```bash
python main.py
```

5. **Open in browser**
```
http://localhost:8000
```

### Using uv (recommended)

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Run directly
uv run python main.py
```

## Usage

### Import Players from Signup List

1. Go to "Import Players" section
2. Paste your signup text (e.g., group chat signup list)
3. The app will automatically extract:
   - Player names
   - Match location (if available)
   - Match time (if available)
4. Click "Import" - new players are added with random skill levels

**Example signup format:**
```
周五blackman park, Lane Cove. 730-930pm
1. JerryW
2. Danny
3. 俐作
4. Sam
...
```

### Add Players Manually

1. Enter player name
2. Select skill level (Weak, Medium, Strong)
3. Click "Add"

### Allocate Teams

1. Click "Allocate Teams" button
2. Players are automatically divided into two balanced teams
3. Positions are assigned based on team size

### Reset Teams

Click "Reset" to clear all team assignments and start over.

## How Team Allocation Works

- Players are sorted by skill level (Strong: 3pts, Medium: 2pts, Weak: 1pt)
- Teams are balanced by alternately assigning high-skill players
- Positions are assigned with these ratios:
  - 1 Goalkeeper
  - ~40% Defenders
  - ~35% Midfielders
  - ~25% Forwards

## Deployment

### Hugging Face Spaces (Docker)

1. Create a new Space at https://huggingface.co/spaces
2. Choose Docker SDK
3. Clone the repository into your Space

Or push directly:
```bash
git remote add hf https://huggingface.co/spaces/yourusername/football-manager
git push hf main
```

### GitHub Pages / Self-hosted

1. Push to GitHub
2. Deploy using your preferred hosting (Heroku, Railway, Render, etc.)

## File Structure

```
football-manager/
├── main.py                 # Main application
├── requirements.txt        # Python dependencies
├── Dockerfile             # Optional Docker configuration
├── .python-version        # Python version specification
├── .gitignore            # Git ignore rules
├── README.md             # This file
└── football_manager.db   # SQLite database (auto-generated)
```

## Data Persistence

**⚠️ Important**: SQLite database is stored in the container. On Hugging Face Spaces:
- Data persists during the session
- Data is lost when the Space restarts/redeploys
- For persistent storage, consider migrating to PostgreSQL or another external database

## Configuration

The app runs on:
- **Local**: `http://localhost:8000`
- **Hugging Face Spaces**: `http://yourspace.hf.space` (port 7860)

To change the port, edit `main.py`:
```python
uvicorn.run(app, host="0.0.0.0", port=8000)
```

## Future Enhancements

- [ ] Multi-language support (English/Chinese)
- [ ] Player statistics and history
- [ ] Match scheduling
- [ ] Export team lists to PDF/CSV
- [ ] Player ratings and feedback
- [ ] PostgreSQL support for persistent storage
- [ ] Web visualization (field diagram with player positions)

## License

MIT License - feel free to use and modify

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

For issues, questions, or suggestions, please open an issue on GitHub.