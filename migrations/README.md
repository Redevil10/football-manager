# Database Migrations

This directory contains database migration scripts for the Football Manager application.

## Migration Scripts

### `migrate_all.py`
**Comprehensive migration script** - Runs all migrations in the correct order:
1. Adds authentication and club support (users, clubs, user_clubs tables)
2. Removes league_id from players table (redundant)
3. Converts leagues to many-to-many relationship with clubs

**Usage:** Run this script once to migrate your database to the new schema.

### `migrate_auth.py`
Adds authentication and club support:
- Creates users, clubs, and user_clubs tables
- Adds club_id to players and leagues tables
- Creates default club "Concord FC" and assigns existing data
- Updates players table to have per-club unique names

**Status:** Idempotent - safe to run multiple times

### `migrate_remove_league_id.py`
Removes the redundant `league_id` column from the players table.

**Status:** Idempotent - safe to run multiple times

### `migrate_club_leagues_many_to_many.py`
Converts leagues from many-to-one (club_id) to many-to-many relationship:
- Creates club_leagues junction table
- Migrates existing league->club relationships
- Removes club_id from leagues table
- Updates league name uniqueness to be global

**Status:** Idempotent - safe to run multiple times

### `migration.py`
Adds `should_allocate` column to match_teams table.

**Status:** Idempotent - safe to run multiple times

## Running Migrations

### Via Web Interface
1. Log in as a superuser
2. Navigate to `/migration`
3. Click "Run Migration"

### Via Command Line
```bash
# From project root directory
# Run all migrations
python -m migrations.migrate_all

# Run individual migrations
python -m migrations.migrate_auth
python -m migrations.migrate_remove_league_id
python -m migrations.migrate_club_leagues_many_to_many
python -m migrations.migration
```

## Migration History

1. **Initial Schema** - Basic tables (players, leagues, matches, etc.)
2. **Auth Migration** - Added authentication and club support
3. **Remove League ID** - Removed redundant league_id from players
4. **Many-to-Many Leagues** - Converted leagues to many-to-many with clubs
5. **Match Teams Allocation** - Added should_allocate column to match_teams

## Notes

- All migrations are **idempotent** - safe to run multiple times
- Migrations check for existing columns/tables before making changes
- Always backup your database before running migrations in production
- The web interface (`/migration`) is only accessible to superusers

## Future Migrations

When adding new migrations:
1. Create a new file: `migrate_<description>.py`
2. Make it idempotent (check before making changes)
3. Add it to `migrate_all.py` if it should run automatically
4. Update this README with the migration details
