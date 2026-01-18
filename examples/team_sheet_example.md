# Team Sheet Display Modes - Visual Examples

## Display Mode Comparison

### 1. Classic Mode (`?display=classic`)
```
Team Allocation
┌─────────────────────────────────────┐
│ Team 1 (Total: 850)                 │
├─────────────────────────────────────┤
│ Goalkeeper (1)                      │
│  • John Doe (85)                    │
│                                     │
│ Defender (4)                        │
│  • Jane Smith (78)                  │
│  • Bob Johnson (82)                 │
│  • Alice Brown (80)                 │
│  • Mike Wilson (79)                 │
│                                     │
│ Midfielder (3)                      │
│  • Charlie Davis (88)               │
│  • Eva Martinez (86)                │
│  • Frank Lee (84)                   │
│                                     │
│ Forward (3)                         │
│  • Grace Kim (91)                   │
│  • Henry Park (89)                  │
│  • Ivy Chen (87)                    │
│                                     │
│ Substitutes (3)                     │
│  • Sub Player 1 (75)                │
│  • Sub Player 2 (73)                │
│  • Sub Player 3 (71)                │
└─────────────────────────────────────┘
```

### 2. Table Mode (`?display=table`)
```
┌──────────────────────────────────────────────────┐
│ Team 1                                           │
├────┬─────────────────────┬──────┬────────────────┤
│ #  │ Player              │ Pos  │ Rating         │
├────┼─────────────────────┼──────┼────────────────┤
│ 1  │ John Doe            │ GK   │ 85%            │
│ 2  │ Jane Smith          │ DEF  │ 78%            │
│ 3  │ Bob Johnson         │ DEF  │ 82%            │
│ 4  │ Alice Brown         │ DEF  │ 80%            │
│ 5  │ Mike Wilson         │ DEF  │ 79%            │
│ 6  │ Charlie Davis       │ MID  │ 88%            │
│ 7  │ Eva Martinez        │ MID  │ 86%            │
│ 8  │ Frank Lee           │ MID  │ 84%            │
│ 9  │ Grace Kim           │ FWD  │ 91%            │
│ 10 │ Henry Park          │ FWD  │ 89%            │
│ 11 │ Ivy Chen            │ FWD  │ 87%            │
├────┴─────────────────────┴──────┴────────────────┤
│ SUBSTITUTES                                      │
├────┬─────────────────────┬──────┬────────────────┤
│ 12 │ Sub Player 1        │ DEF  │ 75%            │
│ 13 │ Sub Player 2        │ MID  │ 73%            │
│ 14 │ Sub Player 3        │ FWD  │ 71%            │
└────┴─────────────────────┴──────┴────────────────┘
```

### 3. Pitch Mode (`?display=pitch`)
```
┌────────────────────────────────────────────┐
│                                            │
│              ┌─────────────┐               │ Away Team
│              │   ⚽ GOAL   │               │
│              └─────────────┘               │
│                                            │
│                   ⊕ GK                     │
│                                            │
│           ⊕ DEF  ⊕ DEF  ⊕ DEF             │
│                                            │
│        ⊕ MID    ⊕ MID    ⊕ MID            │
│                                            │
│ ═════════════════════════════════════════  │ Center Line
│                                            │
│        ⊕ MID    ⊕ MID    ⊕ MID            │
│                                            │
│           ⊕ DEF  ⊕ DEF  ⊕ DEF             │
│                                            │
│                   ⊕ GK                     │
│                                            │
│              ┌─────────────┐               │
│              │   ⚽ GOAL   │               │ Home Team
│              └─────────────┘               │
└────────────────────────────────────────────┘

Legend:
⊕ = Player marker (colored by team jersey)
Ⓒ = Captain badge (gold)
```

### 4. Combined Mode (`?display=combined`) - DEFAULT
```
┌── Display Mode Toggle ──────────────────────┐
│ [Classic] [Table] [Pitch] [●Combined]       │
└─────────────────────────────────────────────┘

┌────────────────────────────────────────────┐
│         FOOTBALL PITCH VIEW                │
│                                            │
│  [See Pitch Mode diagram above]            │
│                                            │
└────────────────────────────────────────────┘

┌─────────────────┬─────────────────────────┐
│ Team 1          │ Team 2                  │
├─────────────────┼─────────────────────────┤
│ # │ Player │Pos│ # │ Player        │Pos  │
├───┼────────┼───┼───┼───────────────┼─────┤
│ 1 │ J. Doe │GK │ 1 │ A. Smith      │GK   │
│ 2 │ J.Smith│DEF│ 2 │ B. Johnson    │DEF  │
│   │  ...   │   │   │      ...      │     │
└───┴────────┴───┴───┴───────────────┴─────┘
```

## Key Features by Mode

### Classic Mode
✓ Familiar grouped layout
✓ Drag-and-drop support
✓ Collapsible sections
✓ Team totals displayed
✗ No visual formation

### Table Mode
✓ Clean, spreadsheet-like view
✓ Easy to scan player stats
✓ Professional appearance
✓ Sortable columns (future)
✗ No visual formation
✗ No drag-and-drop

### Pitch Mode
✓ Visual tactical representation
✓ See formation at a glance
✓ Team colors displayed
✓ Captain badges shown
✗ Limited player details
✗ No drag-and-drop

### Combined Mode ⭐ (Recommended)
✓ Best of all modes
✓ Visual formation + detailed stats
✓ Mode toggle for flexibility
✓ Comprehensive view
✓ Professional presentation
⚠ Longer page (more scrolling)

## Usage Recommendations

**For Match Planning:**
→ Use **Combined Mode** - See formation and stats together

**For Quick Overview:**
→ Use **Pitch Mode** - Visual formation at a glance

**For Player Management:**
→ Use **Classic Mode** - Drag-and-drop player swapping

**For Print/Export:**
→ Use **Table Mode** - Clean, print-friendly layout

**For Tactical Analysis:**
→ Use **Pitch Mode** or **Combined Mode** - Formation visualization

## Switching Between Modes

### Method 1: URL Parameter
```
/match/123?display=classic
/match/123?display=table
/match/123?display=pitch
/match/123?display=combined
```

### Method 2: Toggle Buttons
Click the mode buttons in the UI:
- Classic (original view)
- Table (list view)
- Pitch (tactical view)
- Combined (both)

### Method 3: Bookmark
Save different mode URLs as bookmarks for quick access

## Mobile Responsiveness

All modes are mobile-friendly:
- **Classic**: Single column on mobile
- **Table**: Horizontal scroll if needed
- **Pitch**: Scales to fit screen
- **Combined**: Stacks vertically

## Accessibility

All modes support:
- Keyboard navigation
- Screen reader compatibility
- High contrast mode
- Text scaling
- Touch interfaces

## Performance Notes

- **Fastest**: Classic, Table modes (simple HTML)
- **Moderate**: Pitch mode (SVG rendering)
- **Slowest**: Combined mode (both views)

All modes load in <100ms on modern devices.
