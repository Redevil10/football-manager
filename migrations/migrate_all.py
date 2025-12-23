#!/usr/bin/env python3
"""
Comprehensive migration script that runs all migrations in the correct order.
This script:
1. Adds authentication and club support (users, clubs, user_clubs tables)
2. Adds club_id to players and leagues tables
3. Creates default club "Concord FC" and assigns existing data
4. Removes league_id from players table (redundant)
5. Converts leagues to many-to-many relationship with clubs

Run this script once to migrate your database to the new schema.
"""

import os
import sys

# Add parent directory to path so we can import config and other modules
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

# Import migration modules from the same directory
# These are in the same directory, so we can import directly
# noqa: E402 - sys.path must be modified before these imports
from migrations.migrate_auth import migrate_db as migrate_auth  # noqa: E402
from migrations.migrate_club_leagues_many_to_many import (  # noqa: E402
    migrate_db as migrate_club_leagues_many_to_many,
)
from migrations.migrate_remove_league_id import (  # noqa: E402
    migrate_db as migrate_remove_league_id,
)


def migrate_all():
    """Run all migrations in the correct order

    Returns:
        tuple: (success: bool, messages: list)
    """
    all_messages = []

    print("=" * 70)
    print("COMPREHENSIVE DATABASE MIGRATION")
    print("=" * 70)
    print()

    # Step 1: Authentication and club support
    print("Step 1/3: Adding authentication and club support...")
    print("-" * 70)
    try:
        messages = migrate_auth()
        all_messages.extend(messages)
        print("✓ Step 1 completed successfully")
    except Exception as e:
        print(f"✗ Step 1 failed: {e}")
        print("\nMigration aborted. Please fix the error and try again.")
        return False, all_messages
    print()

    # Step 2: Remove league_id from players
    print("Step 2/3: Removing league_id from players table...")
    print("-" * 70)
    try:
        messages = migrate_remove_league_id()
        all_messages.extend(messages)
        print("✓ Step 2 completed successfully")
    except Exception as e:
        print(f"✗ Step 2 failed: {e}")
        print("\nMigration aborted. Please fix the error and try again.")
        return False, all_messages
    print()

    # Step 3: Convert leagues to many-to-many
    print("Step 3/3: Converting leagues to many-to-many relationship...")
    print("-" * 70)
    try:
        messages = migrate_club_leagues_many_to_many()
        all_messages.extend(messages)
        print("✓ Step 3 completed successfully")
    except Exception as e:
        print(f"✗ Step 3 failed: {e}")
        print("\nMigration aborted. Please fix the error and try again.")
        return False, all_messages
    print()

    # Summary
    print("=" * 70)
    print("MIGRATION SUMMARY")
    print("=" * 70)
    for msg in all_messages:
        print(f"  • {msg}")
    print()
    print("=" * 70)
    print("✓ All migrations completed successfully!")
    print("=" * 70)
    print()
    print("Next steps:")
    print("  1. Create your first superuser by visiting /register")
    print("  2. Log in and start using the system")
    print("  3. Create additional clubs and assign users to them")
    print()

    return True, all_messages


if __name__ == "__main__":
    success, messages = migrate_all()
    sys.exit(0 if success else 1)
