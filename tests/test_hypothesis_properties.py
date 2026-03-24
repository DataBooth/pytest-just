"""Property-based tests for stable invariants in pytest-just."""

from __future__ import annotations

import string
import tempfile
from pathlib import Path

from hypothesis import given, settings
from hypothesis import strategies as st
from pytest_just.fixture import JustfileFixture
from pytest_just.toolkit import recipe_db as builder

from pytest_just.plugin import _discover_justfile_root


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


@settings(max_examples=50)
@given(alias_map=st.dictionaries(keys=_NAME_STRATEGY, values=_NAME_STRATEGY, min_size=0, max_size=12))
def test_aliases_round_trip_for_valid_dump_payload(alias_map: dict[str, str]) -> None:
    """Ensure alias extraction preserves valid alias-target mappings."""
    just = JustfileFixture(root=Path("."))
    just.__dict__["_dump"] = {
        "recipes": {},
        "aliases": {name: {"target": target} for name, target in alias_map.items()},
    }

    assert just.aliases() == alias_map


@settings(max_examples=50)
@given(
    assignment_map=st.dictionaries(
        keys=_NAME_STRATEGY,
        values=st.one_of(
            st.text(alphabet=string.ascii_letters + string.digits + "-_ ", max_size=24),
            st.integers(min_value=-100_000, max_value=100_000),
            st.booleans(),
            st.none(),
        ),
        min_size=0,
        max_size=12,
    )
)
def test_assignments_stringify_values_for_valid_dump_payload(assignment_map: dict[str, object]) -> None:
    """Ensure assignment extraction stringifies assignment values consistently."""
    just = JustfileFixture(root=Path("."))
    just.__dict__["_dump"] = {
        "recipes": {},
        "assignments": {name: {"value": value, "export": False} for name, value in assignment_map.items()},
    }

    expected = {name: str(value) for name, value in assignment_map.items()}
    assert just.assignments() == expected
