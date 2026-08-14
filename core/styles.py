# styles.py - CSS styles

STYLE = """
:root {
    --navy: #12233F;
    --navy-dark: #0B1728;
    --navy-tint: #E8ECF3;
    --amber: #C8873C;
    --amber-tint: #F9F0E3;
    --success: #2E7D57;
    --success-dark: #246344;
    --danger: #9B2C2C;
    --danger-dark: #7A2020;
    --ink: #1A1D23;
    --muted: #6A7080;
    --surface: #F4F5F7;
    --line: #E1E4EA;
    --font-display: 'Oswald', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    --font-body: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    --corner: 20px 6px 6px 6px;
}

body {
    font-family: var(--font-body);
    max-width: 1400px;
    margin: 0 auto;
    padding: 0;
    background: var(--surface);
    color: var(--ink);
}

h1, h2, .navbar h1, .team-header, .attr-section-title, .player-overall,
.mode-btn, button, .login-card h2, .team-table-header {
    font-family: var(--font-display);
}

.navbar {
    background: var(--navy);
    color: white;
    padding: 15px 20px;
    display: flex;
    gap: 20px;
    align-items: center;
    border-bottom: 3px solid var(--amber);
}

.navbar h1 {
    /* The bare `h1` rule below sets a dark ink colour, and that beats the white
       inherited from .navbar -- so the title has to claim white back explicitly. */
    color: white;
    margin: 0;
    /* Kept at sentence case: uppercase plus letter-spacing made the wordmark
       wide enough to crowd the nav links off the bar on smaller laptops. */
    font-size: 20px;
    font-weight: 600;
    white-space: nowrap;
    display: flex;
    align-items: center;
}

/* Navbar right-hand side: user name, superuser badge, log in/out */
.nav-user {
    margin-right: 15px;
    color: rgba(255,255,255,0.85);
    font-size: 14px;
    white-space: nowrap;
}

.nav-badge {
    margin-right: 15px;
    color: var(--amber);
    font-weight: 600;
    font-size: 13px;
    white-space: nowrap;
}

.nav-action {
    white-space: nowrap;
    padding: 6px 15px;
    border: 1px solid rgba(255,255,255,0.35);
    border-radius: 4px;
    background: transparent;
    color: white;
    text-decoration: none;
    font-size: 13px;
    transition: background 0.2s, border-color 0.2s;
}

.nav-action:hover {
    background: rgba(255,255,255,0.15);
    border-color: rgba(255,255,255,0.6);
    color: white;
}

.navbar a {
    color: white;
    text-decoration: none;
    padding: 8px 16px;
    border-radius: 4px;
    transition: background 0.2s;
    font-family: var(--font-body);
}

.navbar a:hover {
    background: rgba(255,255,255,0.15);
}

.navbar a.active {
    background: rgba(255,255,255,0.22);
}

.container {
    padding: 20px;
}

.container-white {
    background: white;
    border-radius: var(--corner);
    padding: 20px;
    margin-bottom: 20px;
    box-shadow: 0 2px 6px rgba(18,35,63,0.07);
    border: 1px solid var(--line);
}

h1 { margin-top: 0; color: var(--ink); font-weight: 600; }
h2 { color: var(--ink); margin-top: 0; font-weight: 600; letter-spacing: 0.2px; }

a { color: var(--navy); }
a:hover { color: var(--navy-dark); }

.input-group {
    display: flex;
    gap: 10px;
    margin-bottom: 15px;
}

input, select, textarea {
    padding: 8px 12px;
    border: 1px solid var(--line);
    border-radius: 4px;
    font-size: 14px;
    font-family: var(--font-body);
    background: white;
    color: var(--ink);
}

input:focus, select:focus, textarea:focus {
    outline: none;
    border-color: var(--navy);
    box-shadow: 0 0 0 3px rgba(18,35,63,0.14);
}

button {
    padding: 9px 18px;
    background: var(--navy);
    color: white;
    border: none;
    border-radius: 5px;
    cursor: pointer;
    font-size: 13px;
    font-weight: 600;
    letter-spacing: 0.4px;
    text-transform: uppercase;
    transition: background 0.15s ease;
}

button:hover { background: var(--navy-dark); }

.btn-danger { background: var(--danger); }
.btn-danger:hover { background: var(--danger-dark); }

.btn-secondary { background: var(--muted); }
.btn-secondary:hover { background: #545967; }

.btn-success { background: var(--success); }
.btn-success:hover { background: var(--success-dark); }

.btn-outline {
    display: inline-block;
    background: transparent;
    color: var(--navy);
    border: 1px solid var(--navy);
    text-decoration: none;
    text-align: center;
}

.btn-outline:hover { background: var(--navy-tint); }

.btn-group {
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
}

.player-table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 15px;
}

.player-table th {
    background: var(--surface);
    padding: 12px;
    text-align: left;
    border-bottom: 2px solid var(--line);
    font-weight: bold;
}

.player-table td {
    padding: 12px;
    border-bottom: 1px solid var(--line);
}

.player-table tr:hover {
    background: var(--surface);
}

.player-row-actions {
    display: flex;
    gap: 8px;
}

.player-row-actions a {
    padding: 4px 8px;
    border-radius: 3px;
    text-decoration: none;
    font-size: 12px;
    color: white;
    background: var(--navy);
    transition: background 0.2s;
}

.player-row-actions a:hover {
    background: var(--navy-dark);
}

.player-row-actions a.delete {
    background: var(--danger);
}

.player-row-actions a.delete:hover {
    background: var(--danger-dark);
}

.attr-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 20px;
    margin-top: 20px;
}

.attr-section {
    background: var(--surface);
    padding: 15px;
    border-radius: 4px;
    border-left: 4px solid var(--navy);
}

.attr-section-title {
    font-weight: 600;
    font-size: 13px;
    color: var(--navy);
    margin-bottom: 12px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.attr-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 10px;
    padding-bottom: 8px;
    border-bottom: 1px solid var(--line);
}

.attr-row:last-child {
    margin-bottom: 0;
    padding-bottom: 0;
    border-bottom: none;
}

.attr-label {
    font-size: 13px;
    color: var(--muted);
}

.attr-input {
    width: 60px;
    padding: 4px 8px;
    border: 1px solid var(--line);
    border-radius: 3px;
    text-align: center;
}

.attr-input:focus {
    outline: none;
    border-color: var(--navy);
}

.attr-input.invalid {
    border-color: var(--danger);
}

.player-overall {
    font-size: 34px;
    font-weight: 600;
    color: var(--navy);
    text-align: center;
    margin: 20px 0;
}

.empty-state {
    text-align: center;
    color: var(--muted);
    padding: 40px 20px;
}

.match-info {
    background: var(--navy-tint);
    padding: 12px 20px;
    margin-bottom: 10px;
    color: var(--navy-dark);
}

.match-info p {
    margin: 5px 0;
}

.teams-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 20px;
}

.team-section {
    border: 2px solid var(--navy);
    padding: 15px;
    border-radius: 4px;
    background: var(--surface);
}

.team-section.team2 { border-color: var(--danger); }

.team-header {
    font-size: 17px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.3px;
    margin-bottom: 15px;
    padding-bottom: 10px;
    border-bottom: 2px dashed currentColor;
}

.position-group { margin-bottom: 15px; }

.position-name {
    font-weight: bold;
    color: var(--muted);
    font-size: 13px;
    margin-bottom: 8px;
}

.player-item {
    background: white;
    padding: 8px 10px;
    margin-bottom: 5px;
    border-radius: 3px;
    border-left: 3px solid var(--navy);
    cursor: move;
    user-select: none;
}

.player-item.team2 { border-left-color: var(--danger); }

.player-item.dragging {
    opacity: 0.5;
    background: var(--surface);
}

.player-item.drag-over {
    background: var(--navy-tint);
    border: 2px dashed var(--navy);
}

.captain-badge {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 18px;
    height: 18px;
    border-radius: 50%;
    border: 2px solid var(--ink);
    background: var(--amber);
    color: var(--ink);
    font-weight: bold;
    font-size: 12px;
    line-height: 1;
    margin-left: 5px;
    flex-shrink: 0;
    padding: 0;
}

/* Football pitch visualization styles */

/* Dual pitch layout - two pitches side by side */
.dual-pitch-container {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 30px;
    margin: 20px 0;
    padding: 20px;
    background: var(--surface);
    border-radius: 8px;
}

.single-pitch-wrapper {
    display: flex;
    flex-direction: column;
    align-items: center;
}

.pitch-team-name {
    margin: 0 0 10px 0;
    font-size: 18px;
    font-weight: bold;
    text-align: center;
}

.pitch-container {
    width: 100%;
    max-width: 400px;
    margin: 0 auto;
}

.pitch-container svg {
    width: 100%;
    height: auto;
    display: block;
    border-radius: 8px;
    box-shadow: 0 4px 6px rgba(18,35,63,0.10);
}

.player-marker {
    cursor: pointer;
    transition: all 0.2s ease;
}

.player-marker:hover {
    filter: brightness(1.2);
    stroke-width: 3;
}

.player-name-label {
    pointer-events: none;
    text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.8);
}

.pitch-view-container {
    background: var(--surface);
    padding: 20px;
    border-radius: 8px;
    margin: 20px 0;
}

/* Interactive pitch container */
.interactive-pitch-container {
    position: relative;
    display: inline-block;
    margin: 0 auto;
}

/* Position slots for drag-and-drop */
.position-slot {
    transition: all 0.2s ease;
}

.position-slot.drag-over {
    background: rgba(200, 135, 60, 0.35) !important;
    transform: scale(1.1);
    box-shadow: 0 0 10px rgba(200, 135, 60, 0.8);
}

.draggable-player {
    cursor: move;
    user-select: none;
}

.draggable-player:active {
    opacity: 0.5;
}

/* Player table styles */
.teams-grid-table {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 30px;
    margin: 20px 0;
}

.team-table-container {
    background: white;
    border-radius: var(--corner);
    overflow: hidden;
    box-shadow: 0 2px 6px rgba(18,35,63,0.07);
    border: 1px solid var(--line);
}

.team-table-header {
    background: var(--surface);
    padding: 15px 20px;
    font-weight: 600;
    font-size: 15px;
    text-transform: uppercase;
    letter-spacing: 0.3px;
    color: var(--ink);
    border-bottom: 2px dashed var(--line);
}

.player-table {
    width: 100%;
    border-collapse: collapse;
}

.player-table thead {
    background: var(--surface);
    border-bottom: 2px solid var(--line);
}

.player-table th {
    padding: 10px 15px;
    text-align: left;
    font-weight: 600;
    font-size: 13px;
    color: var(--muted);
    text-transform: uppercase;
}

.player-table td {
    padding: 10px 15px;
    border-bottom: 1px solid var(--line);
    font-size: 14px;
}

.player-table .col-number {
    width: 40px;
    text-align: center;
}

.player-table .col-position {
    width: 60px;
    text-align: center;
}

.player-table .col-score {
    width: 70px;
    text-align: center;
}

.player-table .starter-row {
    background: white;
}

.player-table .starter-row:hover {
    background: var(--surface);
}

.player-table .substitute-row {
    background: var(--amber-tint);
}

.player-table .substitute-row:hover {
    background: #F2E3CB;
}

.player-table .substitutes-section {
    background: var(--amber-tint);
    padding: 8px 15px;
    font-weight: 600;
    color: #8A5D22;
    border-top: 2px solid var(--amber);
    border-bottom: 1px solid var(--amber);
}

.player-table .substitutes-header {
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.player-number {
    font-weight: bold;
    color: var(--muted);
}

.player-name {
    color: var(--ink);
}

.player-position {
    font-weight: 600;
    color: var(--muted);
    font-size: 12px;
}

.player-score {
    font-weight: 600;
    color: var(--success-dark);
}

/* Display mode toggle */
.display-mode-toggle {
    display: flex;
    gap: 10px;
    margin-bottom: 20px;
    padding: 10px;
    background: var(--surface);
    border-radius: 8px;
    justify-content: center;
}

.mode-btn {
    padding: 8px 20px;
    border: 2px solid var(--line);
    background: white;
    border-radius: 6px;
    cursor: pointer;
    font-weight: 500;
    font-size: 13px;
    letter-spacing: 0.3px;
    text-transform: uppercase;
    color: var(--muted);
    transition: all 0.2s ease;
}

.mode-btn:hover {
    background: var(--surface);
    border-color: var(--muted);
}

.mode-btn.active {
    background: var(--navy);
    color: white;
    border-color: var(--navy);
}

/* Club selector in navbar */
.club-selector-form {
    display: inline-flex;
    align-items: center;
    margin-right: 15px;
}

.club-selector-dropdown {
    padding: 4px 8px;
    border: 1px solid rgba(255,255,255,0.3);
    border-radius: 4px;
    background: rgba(255,255,255,0.12);
    color: white;
    font-size: 13px;
    cursor: pointer;
    max-width: 180px;
}

.club-selector-dropdown:focus {
    outline: none;
    border-color: rgba(255,255,255,0.6);
    box-shadow: 0 0 0 2px rgba(255,255,255,0.2);
}

.club-selector-dropdown option {
    background: white;
    color: var(--ink);
}

.club-selector-label {
    margin-right: 15px;
    color: rgba(255,255,255,0.9);
    font-size: 13px;
    font-weight: 500;
}

/* Hamburger menu toggle (hidden on desktop) */
.nav-toggle {
    display: none;
    background: none;
    border: none;
    color: white;
    font-size: 24px;
    cursor: pointer;
    padding: 4px 8px;
    line-height: 1;
}

.nav-links {
    display: flex;
    align-items: center;
    gap: 20px;
}

/* Auth pages (login / register) */
.auth-page {
    min-height: calc(100vh - 20px);
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 20px;
    background:
        radial-gradient(circle at 50% 0%, rgba(18,35,63,0.05) 0%, transparent 60%),
        var(--surface);
}

.login-card {
    width: 100%;
    max-width: 380px;
    background: white;
    border-radius: var(--corner);
    border: 1px solid var(--line);
    box-shadow: 0 10px 30px rgba(18,35,63,0.10);
    padding: 32px 30px 30px;
}

.login-crest {
    display: flex;
    justify-content: center;
    margin-bottom: 14px;
}

.login-crest img {
    height: 44px;
    width: 44px;
}

.login-card h2 {
    text-align: center;
    text-transform: uppercase;
    letter-spacing: 1px;
    font-size: 22px;
    margin-bottom: 22px;
}

.auth-error {
    color: var(--danger-dark);
    margin-bottom: 15px;
    padding: 10px 12px;
    background: #F9E9E9;
    border: 1px solid #EBC5C5;
    border-radius: 4px;
    font-size: 13px;
}

.auth-divider {
    display: flex;
    align-items: center;
    margin: 22px 0;
    gap: 10px;
    color: var(--muted);
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.auth-divider::before,
.auth-divider::after {
    content: "";
    flex: 1;
    border-top: 1px dashed var(--line);
}

/* Above the hamburger breakpoint every nav link is still on the bar, so on
   smaller laptops the links tighten up rather than push the right-hand side
   (user name, log out) off the edge. */
@media (max-width: 1100px) {
    .navbar { gap: 10px; }
    .nav-links { gap: 2px; }
    .navbar a { padding: 8px 8px; font-size: 13px; }
    .navbar-right { flex-shrink: 0; }
}

@media (max-width: 900px) {
    .nav-toggle { display: block; }
    .nav-links {
        display: none;
        flex-direction: column;
        align-items: flex-start;
        width: 100%;
        gap: 4px;
    }
    .nav-links.open { display: flex; }
    .navbar-right {
        display: none;
        flex-direction: row;
        flex-wrap: wrap;
        align-items: center;
        width: 100%;
        gap: 8px;
    }
    .navbar-right.open { display: flex; }
    .navbar {
        flex-wrap: wrap;
    }
    .navbar-top {
        display: flex;
        align-items: center;
        justify-content: space-between;
        width: 100%;
    }
    .teams-grid { grid-template-columns: 1fr; }
    .teams-grid-table { grid-template-columns: 1fr; }
    .attr-grid { grid-template-columns: 1fr; }

    /* Stack pitches vertically on mobile */
    .dual-pitch-container {
        grid-template-columns: 1fr;
        gap: 20px;
    }

    .pitch-container {
        max-width: 100%;
    }

    /* Scale interactive pitch to fit mobile screen */
    .pitch-formations-container {
        flex-direction: column;
        align-items: center;
    }
    .single-pitch-container {
        width: 100%;
        overflow-x: auto;
        -webkit-overflow-scrolling: touch;
    }
    .interactive-pitch-container {
        transform: scale(0.55);
        transform-origin: top left;
    }
    .single-pitch-container {
        /* Shrunk height: 390 * 0.55 ≈ 215, plus room for team name */
        height: 245px;
    }

    .display-mode-toggle {
        flex-wrap: wrap;
    }

    .mode-btn {
        flex: 1 1 auto;
        min-width: 80px;
        font-size: 12px;
        padding: 6px 12px;
    }
}
"""
