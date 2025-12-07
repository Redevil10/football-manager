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
}

.player-item.team2 { border-left-color: #dc3545; }

@media (max-width: 900px) {
    .navbar {
        flex-direction: column;
        align-items: flex-start;
    }
    .teams-grid { grid-template-columns: 1fr; }
    .attr-grid { grid-template-columns: 1fr; }
}
"""
