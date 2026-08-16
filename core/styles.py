# styles.py - CSS styles

STYLE = """
:root {
    --navy: #12233F;
    --navy-dark: #0B1728;
    --navy-tint: #E8ECF3;
    --amber: #C8873C;
    --amber-tint: #F9F0E3;
    /* Captain's mark only. The amber accent turns brown against the green
       pitch; an armband reads as gold, so this stays a plain yellow. */
    --captain: #F5C518;
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
.mode-btn, button, .login-card h2, .team-table-header,
a.btn-danger, a.btn-secondary, a.btn-success, a.btn-outline {
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
    /* The forms pair `width: 100%` with padding all over the app. Without this
       the padding is added on top of the 100% and the field overflows whatever
       box it sits in -- and it makes the max-widths below mean what they say. */
    box-sizing: border-box;
}

/* Field width should hint at how much you are expected to type. The forms set
   `width: 100%` inline all over the app, which on a wide card handed a "18:30"
   field several hundred pixels; a max-width caps that without having to touch
   every call site, since the two properties are independent and the smaller
   one wins. Anything with its own narrower width (score boxes, the navbar club
   picker) is already below these and is unaffected. */
input[type="date"],
input[type="time"] {
    max-width: 190px;
}

input[type="number"] {
    max-width: 140px;
}

input[type="text"],
input[type="password"],
input[type="email"],
input[type="url"],
select {
    max-width: 420px;
}

textarea {
    max-width: 640px;
}

/* Controls inside a column grid are already sized by their column and are
   meant to fill it -- the captain pickers line up under their own team's
   table. Capping them there would leave each one adrift in a wider column and
   break the symmetry the layout exists for. */
.teams-grid-table input,
.teams-grid-table select,
.teams-grid input,
.teams-grid select {
    max-width: none;
}

input:focus, select:focus, textarea:focus {
    outline: none;
    border-color: var(--navy);
    box-shadow: 0 0 0 3px rgba(18,35,63,0.14);
}

/* Shape only, shared by real buttons and the links dressed as buttons. Colour
   lives in the variant rules below: putting it here too would out-specify
   them, since `a.btn-outline` beats a bare `.btn-outline`. */
button,
a.btn-danger,
a.btn-secondary,
a.btn-success,
a.btn-outline,
a.btn-delete {
    display: inline-block;
    padding: 9px 18px;
    border-radius: 5px;
    cursor: pointer;
    font-size: 13px;
    font-weight: 600;
    letter-spacing: 0.4px;
    text-transform: uppercase;
    text-decoration: none;
    text-align: center;
    transition: background 0.15s ease;
}

/* Default colour is for real buttons; an anchor always carries a variant.
   `border` belongs here rather than in the shape rule above: there it would
   out-specify .btn-outline's own border and flatten it. */
button { background: var(--navy); color: white; border: none; }
button:hover { background: var(--navy-dark); }

.btn-danger { background: var(--danger); color: white; }
.btn-danger:hover { background: var(--danger-dark); color: white; }

.btn-secondary { background: var(--muted); color: white; }
.btn-secondary:hover { background: #545967; color: white; }

.btn-success { background: var(--success); color: white; }
.btn-success:hover { background: var(--success-dark); color: white; }

.btn-outline {
    background: transparent;
    color: var(--navy);
    border: 1px solid var(--navy);
}

.btn-outline:hover { background: var(--navy-tint); color: var(--navy); }

/* Deleting is irreversible and is never why anyone opened the page, so it does
   not get a filled red button sitting next to the action they came for. It is
   grey until you reach for it, and it lives alone in a .danger-zone at the foot
   of the page rather than in the button group up top. The element selectors are
   needed to out-specify the bare `button` colour rule above. */
a.btn-delete,
button.btn-delete {
    background: transparent;
    color: var(--muted);
    border: 1px solid var(--line);
    transition: color 0.15s ease, border-color 0.15s ease;
}

a.btn-delete:hover,
button.btn-delete:hover {
    background: transparent;
    color: var(--danger);
    border-color: var(--danger);
}

/* Separates the delete from whatever the page's real content was. */
.danger-zone {
    margin-top: 24px;
    padding-top: 16px;
    border-top: 1px solid var(--line);
}

/* For deletes that sit in a row rather than at the foot of a page (a match
   event, a recording link). Same idea as .btn-delete without the box. */
a.link-delete,
button.link-delete {
    display: inline;
    padding: 0;
    border: none;
    background: none;
    color: var(--muted);
    font-size: 13px;
    font-weight: 500;
    letter-spacing: 0;
    text-transform: none;
    text-decoration: underline;
    cursor: pointer;
}

a.link-delete:hover,
button.link-delete:hover {
    background: none;
    color: var(--danger);
}

/* The confirmation page. Deliberately plain: the name of the thing is the only
   thing worth reading, and Cancel comes first because it is the likelier
   answer. */
.confirm-delete {
    max-width: 520px;
}

.confirm-delete-name {
    font-size: 18px;
    font-weight: 600;
    color: var(--ink);
    margin: 0 0 4px;
}

.confirm-delete-context {
    color: var(--muted);
    margin: 0 0 4px;
}

.confirm-delete-warning {
    color: var(--danger);
    font-weight: 600;
    margin: 16px 0 20px;
}

/* Same slot as the warning above, for the one action here that is reversible.
   Archiving a player does not deserve red. */
.confirm-delete-note {
    color: var(--muted);
    margin: 16px 0 20px;
}

/* A state a page is in, said once at the top -- not an error and not an
   action. Amber because it is a condition to notice, not a problem. */
.notice {
    background: var(--amber-tint);
    border-left: 3px solid var(--amber);
    border-radius: 4px;
    padding: 12px 16px;
    margin-bottom: 20px;
    color: var(--ink);
}

.btn-group {
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
}

/* Groups short related fields onto one row instead of a long single column.
   auto-fit means the count follows the width, so it collapses to one per row
   on a phone without a breakpoint of its own. */
.form-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
    gap: 0 20px;
    align-items: start;
}

/* Match detail header: the meta line and the actions share a row rather than
   stacking, which is most of the height of that card. */
.match-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 10px 20px;
}

.match-header .btn-group {
    margin: 0;
}

/* Title inside the header row: the page heading margins would push the
   actions beside it out of line. */
.match-title {
    margin: 0 0 4px;
    font-size: 22px;
}

/* A section heading with its controls on the same row, so short actions do not
   each cost a line of their own above the content. */
.section-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 10px 20px;
    margin-bottom: 15px;
}

/* Sits above a table it filters. */
.table-toolbar {
    display: flex;
    align-items: center;
    gap: 12px;
    flex-wrap: wrap;
}

.table-toolbar input {
    flex: 1 1 220px;
}

.table-toolbar-count {
    margin: 0;
    color: var(--muted);
    font-size: 13px;
    white-space: nowrap;
}

/* Recent matches: a row per match inside one card, not a card per match. */
.match-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px 20px;
    flex-wrap: wrap;
    padding: 12px 0;
    border-bottom: 1px solid var(--line);
    text-decoration: none;
    color: inherit;
}

.match-row:last-child {
    border-bottom: none;
    padding-bottom: 0;
}

.match-row:first-child {
    padding-top: 0;
}

.match-row:hover {
    color: inherit;
}

.match-row:hover .match-row-name {
    text-decoration: underline;
}

.match-row-name {
    margin: 0 0 2px;
    font-weight: 600;
    color: var(--navy);
}

/* League name above the fixture: context, so it sits back from the title. */
.match-league {
    margin: 0;
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 0.5px;
    text-transform: uppercase;
    color: var(--muted);
}

/* When and where, sitting with the formation rather than up in the card header,
   so a screenshot of the pitch carries the fixture details with it. */
.match-fixture {
    margin: 0 0 12px;
    font-weight: 600;
    color: var(--ink);
    /* Centred over the pitch it captions, so the screenshot reads as one
       composed image rather than a line of text with a picture under it. */
    text-align: center;
}

/* The line-up sits in the same card as the fixture it belongs to, separated by
   a rule rather than by being a card of its own. */
.match-lineup {
    margin-top: 16px;
    padding-top: 16px;
    border-top: 1px solid var(--line);
}

.player-table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 15px;
}

/* A table with several columns of real text will not fit a phone. Let it
   scroll inside its own box rather than pushing the whole page sideways. */
.table-scroll {
    overflow-x: auto;
}

/* A checkbox column. The header has to be centred too, or it sits over the
   left edge of the column while the tick sits in the middle of it. */
.player-table .col-tick {
    width: 90px;
    text-align: center;
}

/* One line of guidance above a form, in the muted voice of the rest of the
   page rather than as another paragraph of body text. */
.form-hint {
    color: var(--muted);
    margin: 0 0 15px;
}

/* Times and places are context, not what you scan a fixture list for. */
.player-table .col-quiet {
    color: var(--muted);
    white-space: nowrap;
}

/* The score is the one number in the row, so it gets the weight and stays on
   one line -- "3 : 2" wrapping mid-colon reads as two separate cells. */
.player-table .col-score-line {
    white-space: nowrap;
    font-weight: 600;
    color: var(--navy);
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

/* A name in a table is the row's identifier and its way in; underlining every
   one of them turns the column into a wall of rules. */
.player-table td a {
    text-decoration: none;
    font-weight: bold;
}

.player-table td a:hover {
    text-decoration: underline;
}

.player-row-actions {
    display: flex;
    align-items: center;
    gap: 8px;
}

/* Row actions are compact controls. Links and the real submit button share one
   shape here, otherwise a row mixes a small flat link with a full-size
   uppercase button and reads as two different control styles. Scoped off
   .link-delete, which is deliberately not a button shape. */
.player-row-actions a:not(.link-delete),
.player-row-actions button:not(.link-delete) {
    /* The display face is for full-size buttons; at this size it would set the
       row's one real <button> apart from the links beside it. */
    font-family: var(--font-body);
    padding: 4px 10px;
    border-radius: 3px;
    border: none;
    text-decoration: none;
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 0;
    text-transform: none;
    color: white;
    background: var(--navy);
    transition: background 0.2s;
}

.player-row-actions a:not(.link-delete):hover,
.player-row-actions button:not(.link-delete):hover {
    background: var(--navy-dark);
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

/* Date, kick-off and place on one line, so the line-up starts higher up. */
.match-meta {
    margin: 0;
    color: var(--muted);
    font-size: 14px;
}

.match-score {
    margin: 6px 0 0;
    font-family: var(--font-display);
    font-size: 20px;
    font-weight: 600;
    color: var(--navy);
}

/* Sections that are filled in after a match, if at all. They stay collapsed
   while empty so they cost one line instead of a whole card. */
.section-collapsible > .section-summary {
    cursor: pointer;
    font-family: var(--font-display);
    font-size: 17px;
    font-weight: 600;
    color: var(--ink);
    list-style: none;
    display: flex;
    align-items: center;
    gap: 8px;
}

/* Safari still paints the default triangle without this. */
.section-collapsible > .section-summary::-webkit-details-marker {
    display: none;
}

/* Own marker, so it can rotate with the open state. */
.section-collapsible > .section-summary::before {
    content: "";
    border: solid var(--muted);
    border-width: 0 2px 2px 0;
    padding: 3px;
    transform: rotate(-45deg);
    transition: transform 0.15s ease;
}

.section-collapsible[open] > .section-summary::before {
    transform: rotate(45deg);
}

.section-collapsible[open] > .section-summary {
    margin-bottom: 12px;
}

.section-collapsible > .section-summary:focus-visible {
    outline: 2px solid var(--navy);
    outline-offset: 2px;
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
    background: var(--captain);
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

/* The two halves butt together into one pitch, so there is never a gap between
   them. Narrow screens stack them (team A defending the top edge); from 760px
   they sit side by side instead, turning the pair into a landscape pitch that
   uses the width a desktop actually has. */
.pitch-formations-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0;
    max-width: 460px;
    margin: 20px auto;
}

.single-pitch-container {
    width: 100%;
}

/* Interactive pitch: a fluid box the SVG sizes from its own viewBox, with the
   player markers laid over it in percentages. Nothing here is in pixels, so the
   formation stays intact from a 320px phone up to the full desktop width. */
.interactive-pitch-container {
    position: relative;
    width: 100%;
    /* Lets the marker text size itself against the pitch rather than the
       viewport -- two pitches share a row on desktop. */
    container-type: inline-size;
}

.interactive-pitch-container .pitch-svg {
    display: block;
    width: 100%;
    height: auto;
}

/* Stacked: only the outer edges are rounded, so the join in the middle reads as
   a halfway line rather than as two stacked cards. */
.pitch-a .pitch-svg { border-radius: 8px 8px 0 0; }
.pitch-b .pitch-svg { border-radius: 0 0 8px 8px; }

/* Only the orientation matching the current layout is shown. Both are inert
   decoration, so hiding one costs nothing and duplicates no interactive node.
   Scoped to the container to outrank the `.pitch-svg { display: block }` rule
   above -- a bare class would lose to it and both would stack up. */
.interactive-pitch-container .pitch-svg-h { display: none; }

/* Team name sits over its own half, in the corner by that side's goal, so a
   caption never splits the two halves apart. */
.pitch-team-label {
    position: absolute;
    left: 10px;
    margin: 0;
    z-index: 2;
    font-size: 14px;
    font-weight: 600;
    color: white;
    background: rgba(0,0,0,0.45);
    padding: 3px 10px;
    border-radius: 4px;
    pointer-events: none;
}

.pitch-a .pitch-team-label { top: 8px; }
.pitch-b .pitch-team-label { bottom: 8px; }

/* Slots carry their pitch coordinates as --along (own goal to halfway) and
   --across (touchline to touchline). Mapping those onto screen axes is a
   layout decision, so it lives here rather than in the markup.
   Stacked: A defends the top, B the bottom, each turned to face the other. */
.pitch-a .position-slot {
    left: calc((100 - var(--across)) * 1%);
    top: calc(var(--along) * 1%);
}

.pitch-b .position-slot {
    left: calc(var(--across) * 1%);
    top: calc((100 - var(--along)) * 1%);
}


.position-slots-container {
    position: absolute;
    inset: 0;
}

/* Position slots for drag-and-drop */
.position-slot {
    position: absolute;
    /* Marker diameter as a share of pitch width. Capped by the tightest pair in
       the formation grid -- the keeper sits 12% of the width off each centre
       back -- so that no two hit boxes overlap and a drop always resolves to
       the slot under the cursor. */
    width: 12%;
    aspect-ratio: 1;
    /* left/top are the slot's centre, set inline from the formation
       coordinates; this pulls the box back onto that point. */
    transform: translate(-50%, -50%);
    transition: box-shadow 0.2s ease, background 0.2s ease;
}

.position-slot-marker {
    width: 100%;
    height: 100%;
    border-radius: 50%;
    border: 2px solid white;
    display: flex;
    align-items: center;
    justify-content: center;
    /* Tracks the marker, which is 12% of the pitch width here -- the desktop
       rule re-states this because the marker grows to 15% there and a shared
       value would leave the name looking shrunken inside a bigger circle. */
    font-size: clamp(6px, 1.9cqw, 11px);
    font-weight: bold;
    text-align: center;
    line-height: 1.1;
    overflow: hidden;
    position: relative;
    box-shadow: 0 2px 4px rgba(0,0,0,0.3);
    pointer-events: none;
}

/* Captain's mark, pinned to the edge of the marker. It is a sibling of the
   marker rather than a child, because the marker clips its own overflow. Sized
   in percentages so it tracks the marker at every pitch size. */
.captain-mark {
    position: absolute;
    bottom: -2%;
    left: -2%;
    width: 30%;
    aspect-ratio: 1;
    border-radius: 50%;
    background: var(--captain);
    border: 2px solid white;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: clamp(6px, 1.2cqw, 11px);
    font-weight: bold;
    color: var(--ink);
    line-height: 1;
    pointer-events: none;
}

.position-slot.drag-over {
    background: rgba(200, 135, 60, 0.35) !important;
    /* Keeps the centring translate above -- a bare scale() would drop it and
       jump the marker down-right by half its own size. */
    transform: translate(-50%, -50%) scale(1.1);
    box-shadow: 0 0 10px rgba(200, 135, 60, 0.8);
}

@media (min-width: 760px) {
    .pitch-formations-container {
        flex-direction: row;
        max-width: 900px;
    }

    .single-pitch-container { width: 50%; }

    .interactive-pitch-container .pitch-svg-v { display: none; }
    .interactive-pitch-container .pitch-svg-h { display: block; }

    /* Side by side: the rounded corners move to the outer ends. */
    .pitch-a .pitch-svg { border-radius: 8px 0 0 8px; }
    .pitch-b .pitch-svg { border-radius: 0 8px 8px 0; }

    .pitch-a .pitch-team-label,
    .pitch-b .pitch-team-label { top: 8px; bottom: auto; }
    .pitch-b .pitch-team-label { left: auto; right: 10px; }

    /* Quarter turn: along-the-pitch now runs left-right, A defending the left
       edge and B the right, still a half turn apart. */
    .pitch-a .position-slot {
        left: calc(var(--along) * 1%);
        top: calc(var(--across) * 1%);
    }

    .pitch-b .position-slot {
        left: calc((100 - var(--along)) * 1%);
        top: calc((100 - var(--across)) * 1%);
    }

    /* Each half is now the narrow axis of the pair, so the same marker needs a
       bigger share of it to come out the same size on screen. */
    .position-slot { width: 15%; }

    /* Marker is 15% of the pitch width here rather than 12%, so the text has to
       grow by the same factor to keep the same proportion inside the circle. */
    .position-slot-marker { font-size: clamp(8px, 2.4cqw, 13px); }
    .captain-mark { font-size: clamp(7px, 1.7cqw, 12px); }
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

.auth-success {
    color: var(--success-dark);
    margin-bottom: 15px;
    padding: 10px 12px;
    background: #E9F3EE;
    border: 1px solid #C4DFD1;
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
