"""Property-based tests for stable invariants in pytest-just."""

from __future__ import annotations

import importlib.util
import string
import sys
import tempfile
from pathlib import Path

from hypothesis import given, settings
from hypothesis import strategies as st

from pytest_just.plugin import _discover_justfile_root

_BUILDER_SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "build_recipe_db.py"
_BUILDER_SPEC = importlib.util.spec_from_file_location("build_recipe_db_hypothesis", _BUILDER_SCRIPT_PATH)
assert _BUILDER_SPEC is not None
assert _BUILDER_SPEC.loader is not None
builder = importlib.util.module_from_spec(_BUILDER_SPEC)
sys.modules[_BUILDER_SPEC.name] = builder
_BUILDER_SPEC.loader.exec_module(builder)


@settings(max_examples=40)
@given(depth=st.integers(min_value=0, max_value=8))
def test_discover_root_finds_ancestor_justfile_for_any_depth(depth: int) -> None:
    """Ensure root discovery finds the justfile root for arbitrary nesting depths."""
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir) / "project"
        root.mkdir()
        (root / "justfile").write_text("default:\n    @echo ok\n", encoding="utf-8")

        nested = root
        for idx in range(depth):
            nested = nested / f"level-{idx}"
        nested.mkdir(parents=True, exist_ok=True)

        assert _discover_justfile_root(nested) == root


@settings(max_examples=60)
@given(
    body_text=st.text(
        alphabet=string.ascii_letters + string.digits + " \n\t-_/",
        min_size=0,
        max_size=240,
    )
)
def test_normalise_body_is_idempotent(body_text: str) -> None:
    """Ensure body normalisation is idempotent."""
    normalised_once = builder._normalise_body(body_text)
    normalised_twice = builder._normalise_body(normalised_once)
    assert normalised_once == normalised_twice


_NAME_STRATEGY = st.text(
    alphabet=string.ascii_lowercase + string.digits + "-_",
    min_size=1,
    max_size=12,
)


@settings(max_examples=40)
@given(
    recipe_name=_NAME_STRATEGY,
    dependencies=st.lists(_NAME_STRATEGY, min_size=0, max_size=8, unique=True),
    parameter_names=st.lists(_NAME_STRATEGY, min_size=0, max_size=8, unique=True),
    body_text=st.text(alphabet=string.ascii_letters + string.digits + " \n-_/", min_size=0, max_size=120),
    is_shebang=st.booleans(),
)
def test_recipe_signature_is_order_invariant_for_dependencies_and_parameters(
    recipe_name: str,
    dependencies: list[str],
    parameter_names: list[str],
    body_text: str,
    is_shebang: bool,
) -> None:
    """Ensure signature generation is stable across input ordering differences."""
    parameters = [
        {"name": name, "kind": "singular", "default": None, "export": False}
        for name in parameter_names
    ]
    reversed_parameters = list(reversed(parameters))

    signature_a = builder._recipe_signature(
        recipe_name=recipe_name,
        dependencies=dependencies,
        parameters=parameters,
        body_normalised=builder._normalise_body(body_text),
        is_shebang=is_shebang,
    )
    signature_b = builder._recipe_signature(
        recipe_name=recipe_name,
        dependencies=list(reversed(dependencies)),
        parameters=reversed_parameters,
        body_normalised=builder._normalise_body(body_text),
        is_shebang=is_shebang,
    )

    assert signature_a == signature_b
