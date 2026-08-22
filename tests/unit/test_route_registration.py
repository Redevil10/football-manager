"""Route handlers live at module level, not inside the register_* closure.

They used to be nested inside ``register_*_routes``, which made every one of
them unreachable: not importable, so not directly testable, and the module
could not be split up. These tests keep them out in the open -- the structural
ones would fail the moment a handler is written back inside the closure.
"""

import ast
import importlib
import pathlib

import pytest
from fasthtml.common import to_xml

ROUTES_DIR = pathlib.Path(__file__).resolve().parents[2] / "routes"
ROUTE_MODULES = sorted(p.stem for p in ROUTES_DIR.glob("*.py") if p.stem != "__init__")


def _register_fn(tree):
    # Match the full register_*_routes shape, not just the prefix: routes/auth.py
    # has a `register_page` handler that a prefix match picks up instead.
    for node in tree.body:
        if (
            isinstance(node, ast.FunctionDef)
            and node.name.startswith("register_")
            and node.name.endswith("_routes")
        ):
            return node
    return None


def _parse(module_name):
    return ast.parse((ROUTES_DIR / f"{module_name}.py").read_text(encoding="utf-8"))


@pytest.mark.unit
@pytest.mark.parametrize("module_name", ROUTE_MODULES)
class TestHandlersAreModuleLevel:
    def test_register_function_defines_no_handlers(self, module_name):
        """register_*_routes wires things up; it does not house them."""
        reg = _register_fn(_parse(module_name))
        assert reg is not None, f"routes/{module_name}.py has no register_* function"

        nested = [
            n.name
            for n in reg.body
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
        ]
        assert nested == [], (
            f"routes/{module_name}.py defines {nested} inside its register "
            "function; handlers belong at module level so they can be imported"
        )

    def test_every_registered_handler_exists_and_is_callable(self, module_name):
        """Each rt(...)(handler) names a real module-level function."""
        reg = _register_fn(_parse(module_name))
        module = importlib.import_module(f"routes.{module_name}")

        registered = [
            node.args[0].id
            for node in ast.walk(reg)
            if isinstance(node, ast.Call)
            and node.args
            and isinstance(node.args[0], ast.Name)
            and isinstance(node.func, ast.Call)
            and isinstance(node.func.func, ast.Name)
            and node.func.func.id == "rt"
        ]
        assert registered, f"routes/{module_name}.py registers nothing"

        for name in registered:
            handler = getattr(module, name, None)
            assert handler is not None, (
                f"routes/{module_name}.py registers {name}, "
                "which is not defined at module level"
            )
            assert callable(handler)


@pytest.mark.unit
def test_a_handler_can_be_called_without_a_server():
    """The point of the lift: reach a handler directly, with no app running."""
    from routes.public import public_leagues_index

    html = to_xml(public_leagues_index())

    assert "/public/league/" in html or "No public leagues" in html


@pytest.mark.unit
def test_the_whole_app_registers_every_route_exactly_once():
    """Guards against a handler being lifted but never wired back up."""
    from routes import app

    paths = [r.path for r in app.routes if hasattr(r, "path")]

    for expected in ("/login", "/public", "/public/match/{match_id}", "/matches"):
        assert expected in paths, f"{expected} is not registered"

    # /public/match is reachable by exactly one route; a stray duplicate
    # registration would shadow one of them unpredictably.
    assert paths.count("/public/match/{match_id}") == 1
