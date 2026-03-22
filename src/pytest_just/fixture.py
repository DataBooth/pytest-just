from __future__ import annotations

import json
import os
import subprocess
from functools import cached_property
from pathlib import Path
from typing import Any, Iterator
from loguru import logger

from .errors import JustCommandError, JustJsonFormatError, UnknownRecipeError


class JustfileFixture:
    def __init__(self, root: Path, just_bin: str = "just") -> None:
        self._root = Path(root)
        self._just_bin = just_bin
        self._show_cache: dict[str, str] = {}

    @cached_property
    def _dump(self) -> dict[str, Any]:
        logger.debug("Loading justfile JSON dump from {}", self._root)
        result = self._run("--dump", "--dump-format", "json")
        if result.returncode != 0:
            raise JustCommandError(
                "Failed to parse justfile via `just --dump --dump-format json`. "
                "Ensure just >= 1.13.\n"
                f"{result.stderr}"
            )
        try:
            loaded = json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            raise JustJsonFormatError(
                "Unable to parse JSON returned by `just --dump --dump-format json`."
            ) from exc
        if not isinstance(loaded, dict):
            raise JustJsonFormatError("Unexpected just JSON format: top-level value must be an object.")
        return loaded

    @property
    def _recipes(self) -> dict[str, dict[str, Any]]:
        recipes = self._dump.get("recipes", {})
        if not isinstance(recipes, dict):
            raise JustJsonFormatError("Unexpected just JSON format: `recipes` must be a mapping.")
        if not all(isinstance(value, dict) for value in recipes.values()):
            raise JustJsonFormatError("Unexpected just JSON format: each recipe payload must be an object.")
        return recipes

    def recipe_names(self, *, include_private: bool = False) -> list[str]:
        names: list[str] = []
        for name, payload in self._recipes.items():
            is_private = bool(payload.get("private", False))
            if include_private or not is_private:
                names.append(name)
        return sorted(names)

    def dependencies(self, recipe: str) -> list[str]:
        payload = self._require(recipe)
        deps: list[str] = []
        for dep in payload.get("dependencies", []):
            dep_name = dep.get("recipe")
            if isinstance(dep_name, str):
                deps.append(dep_name)
        return deps

    def parameters(self, recipe: str) -> list[dict[str, Any]]:
        payload = self._require(recipe)
        params = payload.get("parameters", [])
        if not isinstance(params, list):
            return []
        return [p for p in params if isinstance(p, dict)]

    def parameter_names(self, recipe: str) -> list[str]:
        return [str(p["name"]) for p in self.parameters(recipe) if "name" in p]

    def is_shebang(self, recipe: str) -> bool:
        return bool(self._require(recipe).get("shebang", False))

    def is_private(self, recipe: str) -> bool:
        return bool(self._require(recipe).get("private", False))

    def doc(self, recipe: str) -> str | None:
        raw = self._require(recipe).get("doc")
        return str(raw) if raw is not None else None

    def body(self, recipe: str) -> list[Any]:
        raw = self._require(recipe).get("body", [])
        return raw if isinstance(raw, list) else []

    def show(self, recipe: str) -> str:
        self._require(recipe)
        if recipe not in self._show_cache:
            result = self._run("--show", recipe)
            if result.returncode != 0:
                raise JustCommandError(f"Failed to show recipe `{recipe}`.\n{result.stderr}")
            self._show_cache[recipe] = result.stdout
        return self._show_cache[recipe]

    def assignments(self) -> dict[str, str]:
        raw = self._dump.get("assignments", {})
        if not isinstance(raw, dict):
            raise JustJsonFormatError("Unexpected just JSON format: `assignments` must be a mapping.")

        values: dict[str, str] = {}
        for key, payload in raw.items():
            if isinstance(key, str) and isinstance(payload, dict) and "value" in payload:
                values[key] = str(payload["value"])
        return values

    def aliases(self) -> dict[str, str]:
        raw = self._dump.get("aliases", {})
        if not isinstance(raw, dict):
            raise JustJsonFormatError("Unexpected just JSON format: `aliases` must be a mapping.")

        values: dict[str, str] = {}
        for key, payload in raw.items():
            if isinstance(key, str) and isinstance(payload, dict):
                target = payload.get("target")
                if isinstance(target, str):
                    values[key] = target
        return values

    def assert_exists(self, recipe: str) -> None:
        self._require(recipe)

    def assert_depends_on(
        self,
        recipe: str,
        expected: list[str],
        transitive: bool = False,
        exact: bool = False,
    ) -> None:
        self._require(recipe)
        if transitive:
            deps = self._walk_dependencies(recipe)
        else:
            deps = set(self.dependencies(recipe))
        expected_set = set(expected)
        missing = [dep for dep in expected if dep not in deps]
        assert not missing, (
            f"Recipe `{recipe}` is missing expected dependencies: {missing}. "
            f"Actual dependencies: {sorted(deps)}"
        )
        if exact:
            unexpected = sorted(deps - expected_set)
            assert not unexpected, (
                f"Recipe `{recipe}` has unexpected dependencies: {unexpected}. "
                f"Expected exactly: {sorted(expected_set)}"
            )

    def assert_parameter(self, recipe: str, parameter: str) -> None:
        params = self.parameter_names(recipe)
        assert parameter in params, (
            f"Recipe `{recipe}` is missing parameter `{parameter}`. "
            f"Available parameters: {params}"
        )

    def assert_body_contains(self, recipe: str, text: str) -> None:
        content = self.show(recipe)
        assert text in content, (
            f"Expected to find {text!r} in recipe `{recipe}` body rendered by `just --show`."
        )

    def assert_not_shebang(self, recipe: str) -> None:
        assert not self.is_shebang(recipe), f"Recipe `{recipe}` uses a shebang and is not dry-run safe."

    def assert_variable_referenced(self, recipe: str, variable: str) -> None:
        for fragment in self._iter_body_fragments(self.body(recipe)):
            if (
                isinstance(fragment, list)
                and len(fragment) == 2
                and isinstance(fragment[0], str)
                and fragment[0].lower() == "variable"
                and fragment[1] == variable
            ):
                return
        raise AssertionError(
            f"Variable `{variable}` is not structurally referenced in recipe `{recipe}` body."
        )

    def dry_run(
        self,
        recipe: str,
        *args: str,
        env: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        self.assert_not_shebang(recipe)
        merged_env = dict(os.environ)
        if env:
            merged_env.update(env)
        return self._run("--dry-run", recipe, *args, env=merged_env)

    def assert_dry_run_contains(
        self,
        recipe: str,
        text: str,
        *args: str,
        env: dict[str, str] | None = None,
    ) -> None:
        result = self.dry_run(recipe, *args, env=env)
        combined_output = result.stdout + result.stderr
        assert result.returncode == 0, (
            f"Expected dry-run for `{recipe}` to succeed but got {result.returncode}.\n"
            f"{combined_output}"
        )
        assert text in combined_output, (
            f"Expected to find {text!r} in dry-run output for `{recipe}`.\n"
            f"Output:\n{combined_output}"
        )

    def _run(
        self,
        *args: str,
        env: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        command = [self._just_bin, *args]
        logger.debug("Running command: {}", " ".join(command))
        return subprocess.run(
            command,
            cwd=self._root,
            capture_output=True,
            text=True,
            check=False,
            env=env,
        )

    def _require(self, recipe: str) -> dict[str, Any]:
        payload = self._recipes.get(recipe)
        if isinstance(payload, dict):
            return payload
        available = ", ".join(self.recipe_names(include_private=True))
        raise UnknownRecipeError(f"Unknown recipe `{recipe}`. Available recipes: {available}")

    def _walk_dependencies(self, recipe: str, seen: set[str] | None = None) -> set[str]:
        if seen is None:
            seen = set()
        for dep in self.dependencies(recipe):
            if dep == recipe:
                continue
            if dep in seen:
                continue
            seen.add(dep)
            self._walk_dependencies(dep, seen=seen)
        return seen

    def _iter_body_fragments(self, node: Any) -> Iterator[Any]:
        if isinstance(node, list):
            yield node
            for item in node:
                yield from self._iter_body_fragments(item)
