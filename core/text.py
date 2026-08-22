# core/text.py - Small text helpers shared across layers

"""Text handling that both the database layer and the render layer need.

It lives in core so neither has to import the other: a rendering function
reaching into db/ for a string helper was the one thing making the render
layer depend on persistence.
"""

from typing import Optional


def split_aliases(alias: Optional[str]) -> list[str]:
    """Split the alias field into the individual names it holds.

    One player often answers to several names -- a nickname, a spelling in
    another script, what the group chat calls them -- so the column holds them
    semicolon-separated. Blanks and stray spacing are dropped.

    Args:
        alias: Raw alias column, e.g. "Ken; 小谢".

    Returns:
        list[str]: The names, in the order written.
    """
    if not alias:
        return []
    return [part.strip() for part in alias.split(";") if part.strip()]
