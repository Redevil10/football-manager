# logic/__init__.py - Business logic module

"""Scoring, team balancing, allocation and signup import.

Deliberately empty of re-exports. It used to pull every submodule in, which
meant `import logic.balance` -- the one module written to have no database
behind it -- executed `logic.allocation` and reached for `db` anyway. Callers
import from the module that owns the function instead:

    from logic.balance import pick_balanced_split      # pure algorithm
    from logic.allocation import allocate_match_teams   # reads and writes
    from logic.scoring import calculate_overall_score
"""
