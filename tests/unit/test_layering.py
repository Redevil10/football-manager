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
import subprocess
import sys
import textwrap

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
    """logic.balance imports cleanly with the db package unavailable.

    Runs in a fresh interpreter on purpose. An in-process guard proves nothing:
    by the time this test runs the suite has already imported db, so the import
    system answers from sys.modules and never consults the finder. The first
    version of this test also used find_module, which Python 3.12 removed, so
    the guard was never called either way and the test passed vacuously.
    """
    source = textwrap.dedent(
        """
        import sys

        class BlockDb:
            def find_spec(self, name, path=None, target=None):
                if name == "db" or name.startswith("db."):
                    raise ImportError("logic.balance reached for " + name)
                return None

        sys.meta_path.insert(0, BlockDb())
        import logic.balance
        assert logic.balance.pick_balanced_split
        assert logic.balance.select_starters
        print("ok")
        """
    )
    result = subprocess.run(
        [sys.executable, "-c", source],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )

    assert result.returncode == 0, (
        "importing logic.balance pulled in the database layer:\n"
        + result.stderr.strip()[-800:]
    )
    assert "ok" in result.stdout


@pytest.mark.unit
def test_the_balance_module_imports_nothing_from_db_transitively():
    """The static half of the same rule, with a clearer failure message."""
    first_party = set(LAYERS)

    def first_party_imports(module):
        path = ROOT / (module.replace(".", "/") + ".py")
        if not path.exists():
            return set()
        found = set()
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.ImportFrom) and node.module:
                if node.module.split(".")[0] in first_party:
                    found.add(node.module)
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.split(".")[0] in first_party:
                        found.add(alias.name)
        return found

    seen, stack = set(), ["logic.balance"]
    while stack:
        module = stack.pop()
        if module in seen:
            continue
        seen.add(module)
        stack.extend(first_party_imports(module) - seen)

    reached_db = sorted(m for m in seen if m.split(".")[0] == "db")
    assert reached_db == [], (
        f"logic.balance reaches the database layer through {reached_db}; "
        f"its import closure is {sorted(seen)}"
    )


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
