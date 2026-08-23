"""The import graph stays acyclic, and the balancing algorithm stays pure.

db and logic used to import each other -- only a function-local import inside
db.players kept that from being a cycle at import time. And the algorithm that
splits a squad into two sides, which is the part of this app most worth getting
right, could not be exercised without a database behind it.

These tests are structural on purpose: they read the imports rather than the
behaviour, so they fail the moment an edge is added back.
"""

import ast
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[2]
LAYERS = ("core", "db", "logic", "services", "render", "routes")


def _imports_of(layer):
    """Which other layers this one imports, module-level and function-local."""
    found = set()
    for path in (ROOT / layer).glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                top = node.module.split(".")[0]
                if top in LAYERS and top != layer:
                    found.add(top)
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    top = alias.name.split(".")[0]
                    if top in LAYERS and top != layer:
                        found.add(top)
    return found


@pytest.mark.unit
def test_db_does_not_import_logic():
    """The edge that closed the cycle. Deriving attributes from a score is
    scoring logic and belongs in logic.players, not inside a db write."""
    assert "logic" not in _imports_of("db"), (
        "db imports logic again -- that recreates the import cycle that "
        "logic.players.add_player_with_score was written to break"
    )


@pytest.mark.unit
def test_core_depends_on_nothing_else():
    """core is the bottom: config, exceptions, styles, small helpers. Anything
    that reaches for stored data belongs in services."""
    assert _imports_of("core") <= {"db"} - {"db"}, (
        f"core imports {sorted(_imports_of('core'))}; move whatever needs them "
        "into services/"
    )


@pytest.mark.unit
def test_the_layer_graph_has_no_cycles():
    graph = {layer: _imports_of(layer) for layer in LAYERS}

    visiting, done = set(), set()
    cycles = []

    def walk(node, trail):
        if node in visiting:
            cycles.append(" -> ".join(trail + [node]))
            return
        if node in done:
            return
        visiting.add(node)
        for nxt in sorted(graph.get(node, ())):
            walk(nxt, trail + [node])
        visiting.discard(node)
        done.add(node)

    for layer in LAYERS:
        walk(layer, [])

    assert cycles == [], "import cycles between layers:\n  " + "\n  ".join(cycles)


@pytest.mark.unit
def test_the_balancing_algorithm_needs_no_database():
    """logic.balance must import cleanly with the db package unavailable."""
    import sys

    class BlockDb:
        def find_module(self, name, path=None):
            if name == "db" or name.startswith("db."):
                raise ImportError(f"logic.balance reached for {name}")
            return None

    for mod in [m for m in sys.modules if m == "logic.balance"]:
        del sys.modules[mod]

    guard = BlockDb()
    sys.meta_path.insert(0, guard)
    try:
        import logic.balance as balance
    finally:
        sys.meta_path.remove(guard)

    # And it really is the algorithm, not an empty module.
    for name in (
        "repeat_penalty",
        "random_balanced_split",
        "generate_split_candidates",
        "pick_balanced_split",
        "select_starters",
    ):
        assert callable(getattr(balance, name)), f"{name} missing from logic.balance"


@pytest.mark.unit
def test_render_does_not_query_in_the_modules_that_were_cleaned():
    """leagues, matches, players and public render from what they are given."""
    for name in ("leagues.py", "matches.py", "players.py", "public.py"):
        tree = ast.parse((ROOT / "render" / name).read_text(encoding="utf-8"))
        db_imports = [
            ast.unparse(n)
            for n in ast.walk(tree)
            if isinstance(n, ast.ImportFrom)
            and n.module
            and n.module.split(".")[0] == "db"
        ]
        assert db_imports == [], f"render/{name} queries the database: {db_imports}"
