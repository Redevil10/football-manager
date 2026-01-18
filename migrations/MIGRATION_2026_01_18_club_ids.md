# Migration: Fix Orphaned Players (2026-01-18)

## Purpose
Fix players that have `club_id` values pointing to non-existent clubs in the `clubs` table.

## Background
During development, some players were assigned to `club_id = 1`, but club ID 1 doesn't exist in the production database. This causes these players to be filtered out when users try to view them.

## Changes
- Updates all players with non-existent `club_id` to belong to the first available club
- If no clubs exist, creates a default club first

## How to Run

### On Local Database
```bash
python migrations/migrate_club_ids.py
```

### On Production Database (Hugging Face)
```bash
python migrations/migrate_club_ids.py /path/to/production/data/football_manager.db
```

### From Hugging Face Space
If you need to run this directly on the Hugging Face space:

1. SSH into the space or use the terminal
2. Navigate to the app directory
3. Run:
```bash
python migrations/migrate_club_ids.py data/football_manager.db
```

## Verification
After running the migration:
- All players should belong to valid clubs
- Player detail pages should work correctly
- No "Player not found" errors for existing players

## Rollback
This migration doesn't delete any data, it only updates `club_id` values. If needed, you can manually update specific players back to their original club:
```sql
UPDATE players SET club_id = <original_club_id> WHERE id = <player_id>;
```

## Related Changes
This migration is part of the pitch visualization improvements that include:
- Realistic FIFA pitch ratio (1.54:1)
- Separate pitches for each team
- Team overall scores (sum of starters)
- Player score display
- Captain indicators
- Clickable player names
