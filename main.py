from fasthtml.common import *
import sqlite3
import random
import os

# ============ CONFIG ============

DB_PATH = '/tmp/data/football_manager.db'


# ============ DATABASE ============

def init_db():
    """Initialize database"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS players
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT NOT NULL UNIQUE,
                  skill TEXT DEFAULT 'medium',
                  team INTEGER,
                  position TEXT,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')

    c.execute('''CREATE TABLE IF NOT EXISTS match
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  date TEXT,
                  time TEXT,
                  location TEXT,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')

    conn.commit()
    conn.close()


init_db()


def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ============ DATABASE - PLAYERS ============

def get_all_players():
    """Get all players"""
    conn = get_db()
    players = conn.execute('SELECT * FROM players ORDER BY created_at DESC').fetchall()
    conn.close()
    return [dict(p) for p in players]


def add_player(name, skill='medium'):
    """Add single player"""
    conn = get_db()
    try:
        conn.execute('INSERT INTO players (name, skill) VALUES (?, ?)', (name, skill))
        conn.commit()
    except sqlite3.IntegrityError:
        pass  # Player already exists
    conn.close()


def delete_player(player_id):
    """Delete player"""
    conn = get_db()
    conn.execute('DELETE FROM players WHERE id = ?', (player_id,))
    conn.commit()
    conn.close()


def update_player_team(player_id, team, position):
    """Update player team and position"""
    conn = get_db()
    conn.execute('UPDATE players SET team = ?, position = ? WHERE id = ?',
                 (team, position, player_id))
    conn.commit()
    conn.close()


def reset_teams():
    """Reset all team assignments"""
    conn = get_db()
    conn.execute('UPDATE players SET team = NULL, position = NULL')
    conn.commit()
    conn.close()


# ============ DATABASE - MATCH ============

def get_match_info():
    """Get match info"""
    conn = get_db()
    match = conn.execute('SELECT * FROM match ORDER BY id DESC LIMIT 1').fetchone()
    conn.close()
    return dict(match) if match else None


def save_match_info(date, time, location):
    """Save match info"""
    conn = get_db()
    conn.execute('DELETE FROM match')
    conn.execute('INSERT INTO match (date, time, location) VALUES (?, ?, ?)',
                 (date, time, location))
    conn.commit()
    conn.close()


# ============ IMPORT LOGIC ============

def parse_signup_text(text):
    """Parse signup text and extract match info and player names"""
    lines = text.strip().split('\n')

    match_info = {'date': '', 'time': '', 'location': ''}
    player_names = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Extract time
        if any(t in line for t in ['730', '930', '7:30', '9:30']):
            match_info['time'] = line

        # Extract location
        if any(l in line.lower() for l in ['park', 'lane', 'cove']):
            match_info['location'] = line

        # Extract player names (lines starting with number)
        if line[0].isdigit():
            name = line.split('.', 1)[-1].strip()
            if name:
                player_names.append(name)

    return match_info, player_names


def import_players(text):
    """Import players from signup text"""
    match_info, player_names = parse_signup_text(text)

    # Save match info
    if match_info['location'] or match_info['time']:
        save_match_info(match_info['date'], match_info['time'], match_info['location'])

    # Import players
    existing = {p['name'] for p in get_all_players()}
    imported = 0

    for name in player_names:
        if name not in existing:
            skill = random.choice(['weak', 'medium', 'strong'])
            add_player(name, skill)
            imported += 1

    return imported


# ============ TEAM ALLOCATION ============

SKILL_WEIGHT = {'strong': 3, 'medium': 2, 'weak': 1}


def allocate_teams():
    """Allocate players into two balanced teams"""
    players = get_all_players()

    if len(players) < 2:
        return False, "Need at least 2 players"

    # Sort by skill level
    sorted_players = sorted(
        players,
        key=lambda x: SKILL_WEIGHT.get(x['skill'], 2),
        reverse=True
    )

    # Balance teams
    team1, team2 = [], []
    team1_score, team2_score = 0, 0
    max_per_team = (len(players) + 1) // 2

    for player in sorted_players:
        score = SKILL_WEIGHT.get(player['skill'], 2)

        if len(team1) < max_per_team and (len(team2) >= max_per_team or team1_score <= team2_score):
            team1.append(player)
            team1_score += score
        else:
            team2.append(player)
            team2_score += score

    # Assign positions
    assign_positions(team1, 1)
    assign_positions(team2, 2)

    return True, "Teams allocated"


def assign_positions(team, team_num):
    """Assign positions to team members"""
    random.shuffle(team)
    team_size = len(team)

    # Allocate positions by ratio
    positions = []
    positions.extend(['Goalkeeper'] * 1)
    positions.extend(['Defender'] * max(1, int(team_size * 0.4)))
    positions.extend(['Midfielder'] * max(1, int(team_size * 0.35)))
    positions.extend(['Forward'] * max(1, team_size - len(positions)))

    positions = positions[:team_size]

    # Update database
    for player, position in zip(team, positions):
        update_player_team(player['id'], team_num, position)


# ============ STYLES ============

STYLE = """
body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    max-width: 1200px;
    margin: 0 auto;
    padding: 20px;
    background: #f5f5f5;
}

.container {
    background: white;
    border-radius: 8px;
    padding: 20px;
    margin-bottom: 20px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

h1 { margin-top: 0; color: #333; }
h2 { color: #333; margin-top: 0; }

.input-group {
    display: flex;
    gap: 10px;
    margin-bottom: 15px;
}

input, select, textarea {
    padding: 8px 12px;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-size: 14px;
    font-family: inherit;
}

input:focus, select:focus, textarea:focus {
    outline: none;
    border-color: #0066cc;
    box-shadow: 0 0 0 3px rgba(0,102,204,0.1);
}

button {
    padding: 8px 16px;
    background: #0066cc;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 14px;
    transition: background 0.2s;
}

button:hover { background: #0052a3; }

.btn-danger { background: #dc3545; }
.btn-danger:hover { background: #c82333; }

.btn-secondary { background: #6c757d; }
.btn-secondary:hover { background: #5a6268; }

.btn-group {
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
}

.player-list {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 10px;
}

.player-card {
    border: 1px solid #ddd;
    padding: 12px;
    border-radius: 4px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: #fafafa;
}

.player-name {
    font-weight: bold;
    margin-bottom: 5px;
    color: #333;
}

.skill-badge {
    display: inline-block;
    padding: 3px 8px;
    border-radius: 3px;
    font-size: 12px;
    margin-right: 8px;
}

.skill-strong { background: #d4edda; color: #155724; }
.skill-medium { background: #fff3cd; color: #856404; }
.skill-weak { background: #f8d7da; color: #721c24; }

.teams-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 20px;
}

.team-section {
    border: 2px solid #0066cc;
    padding: 15px;
    border-radius: 4px;
    background: #f9f9f9;
}

.team-section.team2 { border-color: #dc3545; }

.team-header {
    font-size: 18px;
    font-weight: bold;
    margin-bottom: 15px;
    padding-bottom: 10px;
    border-bottom: 2px solid currentColor;
}

.position-group { margin-bottom: 15px; }

.position-name {
    font-weight: bold;
    color: #666;
    font-size: 13px;
    margin-bottom: 8px;
}

.player-item {
    background: white;
    padding: 8px 10px;
    margin-bottom: 5px;
    border-radius: 3px;
    border-left: 3px solid #0066cc;
}

.player-item.team2 { border-left-color: #dc3545; }

.empty-state {
    text-align: center;
    color: #999;
    padding: 20px;
}

.match-info {
    background: #e7f3ff;
    padding: 12px;
    border-radius: 4px;
    margin-bottom: 10px;
}

.match-info p {
    margin: 5px 0;
    color: #0066cc;
}

@media (max-width: 900px) {
    .teams-grid { grid-template-columns: 1fr; }
    .input-group { flex-direction: column; }
}
"""


# ============ RENDERING ============

def render_match_info(match):
    """Render match info"""
    if not match:
        return ""

    return Div(cls="match-info")(
        (P(f"📍 {match['location']}") if match['location'] else ""),
        (P(f"🕐 {match['time']}") if match['time'] else ""),
    )


def render_player_list(players):
    """Render player list"""
    if not players:
        return P("No players yet", cls="empty-state")

    cards = []
    for p in players:
        skill_text = {'strong': 'Strong', 'medium': 'Medium', 'weak': 'Weak'}.get(p['skill'], 'Medium')

        meta = Div(cls="player-meta")(
            Span(f"Skill: {skill_text}", cls=f"skill-badge skill-{p['skill']}"),
            (Span(f"Position: {p['position']}") if p['position'] else ""),
            (Span(f" | Team: {p['team']}") if p['team'] else ""),
        )

        card = Div(cls="player-card")(
            Div(
                Div(p['name'], cls="player-name"),
                meta,
            ),
            Form(
                Button("Delete", type="submit", cls="btn-danger"),
                method="post",
                action=f"/delete_player/{p['id']}",
                onsubmit="return confirm('Confirm delete?');",
                style="margin: 0;"
            ),
        )
        cards.append(card)

    return Div(cls="player-list")(*cards)


def render_teams(players):
    """Render team allocation"""
    team1 = [p for p in players if p['team'] == 1]
    team2 = [p for p in players if p['team'] == 2]

    if not team1 or not team2:
        return Div(cls="container")(
            P("No teams allocated. Click 'Allocate Teams' to start.", cls="empty-state")
        )

    def render_team(team, team_num):
        positions_order = ['Goalkeeper', 'Defender', 'Midfielder', 'Forward']
        grouped = {pos: [] for pos in positions_order}

        for player in team:
            if player['position']:
                # Skip invalid positions
                if player['position'] in grouped:
                    grouped[player['position']].append(player)

        team_color = "team2" if team_num == 2 else ""
        team_name = f"Team {team_num}"

        position_groups = []
        for pos in positions_order:
            if grouped[pos]:
                position_groups.append(
                    Div(cls="position-group")(
                        Div(f"{pos} ({len(grouped[pos])})", cls="position-name"),
                        *[Div(p['name'], cls=f"player-item {team_color}") for p in grouped[pos]]
                    )
                )

        return Div(cls=f"team-section {team_color}")(
            Div(team_name, cls="team-header"),
            *position_groups
        )

    return Div(cls="container")(
        Div(cls="teams-grid")(
            render_team(team1, 1),
            render_team(team2, 2),
        )
    )


# ============ ROUTES ============

app, rt = fast_app()


@rt("/")
def home():
    """Home page"""
    players = get_all_players()
    match = get_match_info()

    return Html(
        Head(
            Title("Football Manager"),
            Style(STYLE),
            Script(src="https://unpkg.com/htmx.org@1.9.10"),
        ),
        Body(
            H1("⚽ Football Manager"),

            render_match_info(match),

            # Import section
            Div(cls="container")(
                H2("Import Players"),
                Form(
                    Textarea(
                        placeholder="Paste signup list here...",
                        name="signup_text",
                        style="width: 100%; min-height: 150px; padding: 10px; border: 1px solid #ddd; border-radius: 4px; font-family: monospace;",
                        required=True
                    ),
                    Div(style="margin-top: 10px;")(
                        Button("Import", type="submit"),
                    ),
                    method="post",
                    action="/import_players"
                ),
            ),

            # Add player section
            Div(cls="container")(
                H2("Add Player"),
                Form(
                    Div(cls="input-group")(
                        Input(name="name", placeholder="Player name", required=True),
                        Select(
                            Option("Weak", value="weak"),
                            Option("Medium", value="medium", selected=True),
                            Option("Strong", value="strong"),
                            name="skill"
                        ),
                        Button("Add", type="submit"),
                    ),
                    method="post",
                    action="/add_player"
                ),
            ),

            # Players list
            Div(cls="container")(
                H2(f"Players ({len(players)})"),
                render_player_list(players),
            ),

            # Action buttons
            Div(cls="container")(
                Div(cls="btn-group")(
                    Button("Allocate Teams", cls="btn-success",
                           **{"hx-post": "/allocate", "hx-target": "#teams-result", "hx-swap": "innerHTML"}),
                    Button("Reset", cls="btn-secondary",
                           **{"hx-post": "/reset", "hx-target": "#teams-result", "hx-swap": "innerHTML"}),
                ),
            ),

            # Teams result
            Div(id="teams-result")(
                render_teams(players)
            ),
        )
    )


@rt("/add_player", methods=["POST"])
def route_add_player(name: str, skill: str = "medium"):
    """Add single player"""
    add_player(name, skill)
    return RedirectResponse("/", status_code=303)


@rt("/import_players", methods=["POST"])
def route_import_players(signup_text: str):
    """Import players from signup text"""
    import_players(signup_text)
    return RedirectResponse("/", status_code=303)


@rt("/delete_player/{player_id}", methods=["POST"])
def route_delete_player(player_id: int):
    """Delete player"""
    delete_player(player_id)
    return RedirectResponse("/", status_code=303)


@rt("/allocate", methods=["POST"])
def route_allocate():
    """Allocate teams"""
    success, message = allocate_teams()

    if not success:
        return Div(cls="container")(
            P(message, style="text-align: center; color: #dc3545; font-weight: bold;")
        )

    return render_teams(get_all_players())


@rt("/reset", methods=["POST"])
def route_reset():
    """Reset teams"""
    reset_teams()
    return Div(cls="container")(
        P("Teams reset successfully", style="text-align: center; color: #666;")
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
