# styles.py - CSS styles

STYLE = """
body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    max-width: 1400px;
    margin: 0 auto;
    padding: 0;
    background: #f5f5f5;
}

.navbar {
    background: #0066cc;
    color: white;
    padding: 15px 20px;
    display: flex;
    gap: 20px;
    align-items: center;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.navbar h1 {
    margin: 0;
    font-size: 24px;
}

.navbar a {
    color: white;
    text-decoration: none;
    padding: 8px 16px;
    border-radius: 4px;
    transition: background 0.2s;
}

.navbar a:hover {
    background: rgba(255,255,255,0.2);
}

.navbar a.active {
    background: rgba(255,255,255,0.3);
}

.container {
    padding: 20px;
}

.container-white {
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

.btn-success { background: #28a745; }
.btn-success:hover { background: #218838; }

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
    background: #f9f9f9;
    padding: 12px;
    text-align: left;
    border-bottom: 2px solid #ddd;
    font-weight: bold;
}

.player-table td {
    padding: 12px;
    border-bottom: 1px solid #eee;
}

.player-table tr:hover {
    background: #f9f9f9;
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
    background: #0066cc;
    transition: background 0.2s;
}

.player-row-actions a:hover {
    background: #0052a3;
}

.player-row-actions a.delete {
    background: #dc3545;
}

.player-row-actions a.delete:hover {
    background: #c82333;
}

.attr-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 20px;
    margin-top: 20px;
}

.attr-section {
    background: #f9f9f9;
    padding: 15px;
    border-radius: 4px;
    border-left: 4px solid #0066cc;
}

.attr-section-title {
    font-weight: bold;
    font-size: 14px;
    color: #0066cc;
    margin-bottom: 12px;
    text-transform: uppercase;
}

.attr-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 10px;
    padding-bottom: 8px;
    border-bottom: 1px solid #eee;
}

.attr-row:last-child {
    margin-bottom: 0;
    padding-bottom: 0;
    border-bottom: none;
}

.attr-label {
    font-size: 13px;
    color: #666;
}

.attr-input {
    width: 60px;
    padding: 4px 8px;
    border: 1px solid #ddd;
    border-radius: 3px;
    text-align: center;
}

.attr-input:focus {
    outline: none;
    border-color: #0066cc;
}

.attr-input.invalid {
    border-color: #dc3545;
}

.player-overall {
    font-size: 32px;
    font-weight: bold;
    color: #0066cc;
    text-align: center;
    margin: 20px 0;
}

.empty-state {
    text-align: center;
    color: #999;
    padding: 40px 20px;
}

.match-info {
    background: #e7f3ff;
    padding: 12px 20px;
    margin-bottom: 10px;
    color: #0066cc;
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
    cursor: move;
    user-select: none;
}

.player-item.team2 { border-left-color: #dc3545; }

.player-item.dragging {
    opacity: 0.5;
    background: #f0f0f0;
}

.player-item.drag-over {
    background: #e7f3ff;
    border: 2px dashed #0066cc;
}

.captain-badge {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 18px;
    height: 18px;
    border-radius: 50%;
    border: 2px solid #000;
    background: #ffd700;
    color: #000;
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
    background: #f5f5f5;
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
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
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
    background: #f5f5f5;
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
    background: rgba(255, 255, 0, 0.3) !important;
    transform: scale(1.1);
    box-shadow: 0 0 10px rgba(255, 255, 0, 0.8);
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
    border-radius: 8px;
    overflow: hidden;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.team-table-header {
    background: #f8f9fa;
    padding: 15px 20px;
    font-weight: bold;
    font-size: 16px;
    color: #333;
}

.player-table {
    width: 100%;
    border-collapse: collapse;
}

.player-table thead {
    background: #e9ecef;
    border-bottom: 2px solid #dee2e6;
}

.player-table th {
    padding: 10px 15px;
    text-align: left;
    font-weight: 600;
    font-size: 13px;
    color: #495057;
    text-transform: uppercase;
}

.player-table td {
    padding: 10px 15px;
    border-bottom: 1px solid #f1f3f5;
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
    background: #f8f9fa;
}

.player-table .substitute-row {
    background: #fff9e6;
}

.player-table .substitute-row:hover {
    background: #fff3cd;
}

.player-table .substitutes-section {
    background: #fff9e6;
    padding: 8px 15px;
    font-weight: 600;
    color: #856404;
    border-top: 2px solid #ffc107;
    border-bottom: 1px solid #ffc107;
}

.player-table .substitutes-header {
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.player-number {
    font-weight: bold;
    color: #6c757d;
}

.player-name {
    color: #212529;
}

.player-position {
    font-weight: 600;
    color: #495057;
    font-size: 12px;
}

.player-score {
    font-weight: 600;
    color: #28a745;
}

/* Display mode toggle */
.display-mode-toggle {
    display: flex;
    gap: 10px;
    margin-bottom: 20px;
    padding: 10px;
    background: #f8f9fa;
    border-radius: 8px;
    justify-content: center;
}

.mode-btn {
    padding: 8px 20px;
    border: 2px solid #dee2e6;
    background: white;
    border-radius: 6px;
    cursor: pointer;
    font-weight: 500;
    font-size: 14px;
    color: #495057;
    transition: all 0.2s ease;
}

.mode-btn:hover {
    background: #e9ecef;
    border-color: #adb5bd;
}

.mode-btn.active {
    background: #0066cc;
    color: white;
    border-color: #0066cc;
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
    background: rgba(255,255,255,0.15);
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
    color: #333;
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
