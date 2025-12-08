#!/usr/bin/env python3
"""
Migration script to update player attributes:
1. Move 'pace' from technical_attrs to physical_attrs
2. Remove 'shooting' from technical_attrs
"""

import json
import sqlite3
from config import DB_PATH

def migrate_attributes():
    """Migrate player attributes"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    # Get all players
    players = c.execute("SELECT id, technical_attrs, physical_attrs FROM players").fetchall()
    
    migrated_count = 0
    pace_moved_count = 0
    shooting_removed_count = 0
    
    for player in players:
        player_id = player["id"]
        tech_attrs = json.loads(player["technical_attrs"] or "{}")
        phys_attrs = json.loads(player["physical_attrs"] or "{}")
        
        updated = False
        
        # Move 'pace' from technical to physical (only if not already in physical)
        if "pace" in tech_attrs and "pace" not in phys_attrs:
            pace_value = tech_attrs.pop("pace")
            phys_attrs["pace"] = pace_value
            updated = True
            pace_moved_count += 1
            print(f"Player {player_id}: Moved 'pace' ({pace_value}) from technical to physical", flush=True)
        elif "pace" in tech_attrs:
            # Already migrated, just remove from technical
            tech_attrs.pop("pace")
            updated = True
        
        # Remove 'shooting' from technical
        if "shooting" in tech_attrs:
            shooting_value = tech_attrs.pop("shooting")
            updated = True
            shooting_removed_count += 1
            print(f"Player {player_id}: Removed 'shooting' ({shooting_value}) from technical", flush=True)
        
        # Update database if changes were made
        if updated:
            c.execute(
                "UPDATE players SET technical_attrs = ?, physical_attrs = ? WHERE id = ?",
                (json.dumps(tech_attrs), json.dumps(phys_attrs), player_id)
            )
            migrated_count += 1
    
    conn.commit()
    conn.close()
    
    if migrated_count > 0:
        print(f"Migration: {migrated_count} players updated ({pace_moved_count} pace moved, {shooting_removed_count} shooting removed)", flush=True)
    
    return migrated_count, pace_moved_count, shooting_removed_count

if __name__ == "__main__":
    print("Starting attribute migration...")
    print("=" * 50)
    migrate_attributes()
    print("=" * 50)
    print("Migration finished!")

