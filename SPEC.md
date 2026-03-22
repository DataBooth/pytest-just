# pytest-just: Specification for LLM Implementation
A pytest plugin for testing justfiles. No such tool exists (as of March 2026). This spec is derived from a working hand-rolled implementation in a real project and a detailed design sketch. The goal is a reusable, publishable package.

---

## 1. Problem Statement
Justfiles (used by [just](https://just.systems), a command runner) have failure modes that are easy to miss:

- A recipe is silently renamed or deleted, breaking CI scripts and documentation.
- A dependency chain breaks (e.g. `dev` stops calling `lint`).
- Variable substitution breaks (a variable stops threading through recipes).
- A parameter is renamed, silently changing behaviour and no longer matching expected invocation/docs. (Source text partially truncated.)
- A multi-step recipe with embedded bash has a logic error.

The interesting behaviour lives in the tools justfiles delegate to (pytest, ruff, cargo, etc.), which have their own tests. But the **justfile itself** — its recipe graph, parameter contracts, and variable threading — is untested infrastructure.

No off-the-shelf tool addresses this. `pytest-just` fills the gap.

---

## 2. Key Insight: `just --dump --dump-format json`
`just` (>= 1.13) can emit the full justfile as structured JSON:

```bash
just --dump --dump-format json
```

This gives structured access to recipes, dependencies, parameters, attributes, and body content — without string-parsing `just --show` output.

### 2.1 JSON Schema (observed from just 1.47.x)
The top-level object has at least these keys:

```json
{
  "aliases": { "<alias_name>": { "target": "<recipe_name>" } },
  "assignments": { "<var_name>": { "value": "...", "export": false } },
  "recipes": { "...": {} },
  "settings": { "...": "..." },
  "warnings": ["..."]
}
```

Each recipe in `"recipes"` has this shape:

```json
{
  "<recipe_name>": {
    "body": [["<line_fragment>"]],
    "dependencies": [
      { "arguments": [], "recipe": "<dep_name>" }
    ],
    "doc": "Recipe doc comment or null",
    "name": "<recipe_name>",
    "parameters": [
      {
        "default": null,
        "export": false,
        "kind": "singular | plus | star",
        "name": "<PARAM_NAME>"
      }
    ],
    "priors": 0,
    "private": true,
    "quiet": false,
    "shebang": false,
    "attributes": []
  }
}
```

**Body structure:** each line in `"body"` is an array of fragments. A fragment is either a plain string `"text"` or a structured reference like `["Variable", "var_name"]`. This means variable references can be checked structurally (not just via string matching), though string matching on `just --show` output is simpler for v1.

**Important:** the JSON dump includes recipes from all imported files (e.g. `import "just/utilities.just"`), so the full recipe graph is available in a single call.

---

## 3. Package Structure
Initial structure:

```text
pytest-just/
├── pyproject.toml
├── LICENSE                # MIT
├── README.md
└── src/
    └── pytest_just/
        ├── __init__.py    # Re-export JustfileFixture + version
        ├── fixture.py      # JustfileFixture class
        └── plugin.py       # Pytest plugin hooks and fixture registration
```

### 3.1 Implementation Standards (Mandatory)
- **Use `pathlib` for all filesystem handling.**
  - Public APIs accept/return `pathlib.Path` where path objects are appropriate.
  - Internal code must not use `os.path` for new implementation work.
- **Use `loguru` for clear, minimal, actionable logging.**
  - Log only meaningful lifecycle/debug information (discovery, parse/load, command invocation, failures).
  - Avoid noisy per-line logging of recipe bodies.
- **Use `uv` for Python project/dependency management and task execution.**
  - Local development commands, CI commands, and documentation examples should use `uv` (e.g. `uv run pytest`).
- **Use `ruff` for linting/format checks and `ty` for type checks.**
  - The project quality gate includes both tools.
  - Example expectation: lint/format via `ruff`, static checks via `ty check`.
- **If a CLI is required beyond pytest plugin options, use `Typer`.**
  - Keep CLI thin; delegate business logic to library modules.
- **If a database layer is required, use `DuckDB`.**
  - Prefer no database for v1 unless there is a clear requirement for persisted/queryable state.

---

## 4. Plugin Registration (`plugin.py`)
### 4.1 Entry Point
Register via the `pytest11` entry point so the plugin activates automatically when the package is installed:

```toml
[project.entry-points."pytest11"]
just = "pytest_just.plugin"
```

### 4.2 CLI Options
- `--justfile-root` (default: auto-detect): directory containing the justfile
- `--just-bin` (default: `"just"`): path to the `just` binary

Auto-detection: walk upward from `pytestconfig.rootdir` looking for a file named `justfile` or `Justfile`. Raise `FileNotFoundError` with a clear message if neither is found.

### 4.3 Session Fixture
Provide a **session-scoped** fixture named `just` that returns a `JustfileFixture` instance. Session scope ensures `just --dump` is called at most once per test run.

### 4.4 Marker
Register a `justfile` marker so users can run justfile tests independently:

```python
def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "justfile: marks tests as justfile recipe tests",
    )
```

---

## 5. JustfileFixture Class (`fixture.py`)
### 5.1 Constructor
```python
JustfileFixture(root: Path, just_bin: str = "just")
```

- `root`: directory containing the justfile. All subprocess calls use `cwd=root`.
- `just_bin`: path or name of the `just` binary.

### 5.2 Data Loading
Parse the justfile once per session via `just --dump --dump-format json`. Use `functools.cached_property` for lazy, one-time loading.

If the command fails (exit code != 0), raise `RuntimeError` with the stderr output and a note that just >= 1.13 is required.

Cache `just --show <recipe>` results per-recipe in a dict (recipe bodies don't change during a test session).

### 5.3 Public Accessors
All accessors raise `ValueError` with a clear message listing available recipes if the requested recipe doesn't exist.

Methods captured from source screenshots:

- `recipe_names(*, include_private: bool = False) -> list[str]`
  - Returns list of recipe names.
  - Includes private recipes only when `include_private=True`.
- `dependencies(recipe: str) -> list[str]`
  - Returns **direct** dependency recipe names (from JSON `dependencies`).
- `parameters(recipe: str) -> list[dict]`
  - Returns parameter dicts.
  - Each dict includes `name`, `default`, `kind`, `export`.
- `parameter_names(recipe: str) -> list[str]`
  - Returns parameter name strings.
  - Convenience shorthand.
- `is_shebang(recipe: str) -> bool`
  - Boolean.
  - Whether the recipe uses a shebang interpreter.
- `is_private(recipe: str) -> bool`
  - Boolean.
  - Whether the recipe is private.
- `doc(recipe: str) -> str | None`
  - Doc comment or `None`.
  - The `# comment` above the recipe.
- `body(recipe: str) -> list`
  - Raw body from JSON.
  - The structured body array (for advanced assertions).
- `show(recipe: str) -> str`
  - Full `just --show` output.
  - The interpolated recipe text (for string matching).
- `assignments() -> dict[str, str]`
  - Top-level variable assignments.
  - Variable name -> value.
- `aliases() -> dict[str, str]`
  - Alias mappings.
  - Alias name -> target recipe name.

### 5.4 Assertion Methods
All assertion methods raise assertion failures with clear messages.

Methods visible in provided screenshots:
- `assert_exists(recipe: str)`
  - Fails if recipe does not exist.
- `assert_depends_on(recipe: str, expected: list[str], transitive: bool = False)`
  - Asserts direct or transitive dependency relationships.
- `assert_parameter(recipe: str, parameter: str)`
  - Fails if a required parameter is missing.
- `assert_body_contains(recipe: str, text: str)`
  - Fails if expected text is not in the recipe body.
  - Useful for negative guards (e.g. recipe must not hard-code a path).

- `assert_not_shebang(recipe: str)`
  - Fails if the recipe uses shebang.
  - Useful as a guard before dry-run tests.
- `assert_variable_referenced(recipe: str, variable: str)`
  - Fails if the variable is not referenced in the recipe body.
  - Uses the structured JSON body (not string matching) to find `["Variable", "<name>"]` fragments.

### 5.5 Dry-Run Support
```python
def dry_run(
    self,
    recipe: str,
    *args: str,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]
```

- First asserts `not is_shebang(recipe)` — shebang recipes execute the interpreter even under `--dry-run`, which defeats the purpose.
- Runs `just --dry-run <recipe> <args>` with `cwd=self._root`.
- Merges `env` with `os.environ` (env overrides take precedence).
- Returns the `CompletedProcess` for the caller to inspect stdout and return code.

### 5.6 Internal Helpers
```python
def _run(
    self,
    *args: str,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]
```

Central subprocess runner. All calls go through this. Uses:

- `capture_output=True`
- `text=True`
- `check=False` (callers decide how to handle errors)
- `cwd=self._root`

```python
def _require(self, recipe: str) -> None
```
Raises `ValueError` if recipe is not in parsed data. Used internally by all accessors before accessing recipe fields.

```python
def _walk_dependencies(
    self,
    recipe: str,
    seen: set[str] | None = None,
) -> set[str]
```

Recursive helper for transitive dependency resolution. Tracks visited recipes to handle cycles gracefully (cycles shouldn't exist in valid justfiles, but defensive coding is appropriate here).

---

## 6. What Tests Look Like (User-Facing Examples)
These examples should appear in the README and drive the API design. If the API doesn't support writing tests this cleanly, the API is wrong.

### 6.1 Recipe Existence
```python
import pytest

REQUIRED_RECIPES = ["test", "build", "lint", "dev", "ci", "clean"]

@pytest.mark.justfile
@pytest.mark.parametrize("recipe", REQUIRED_RECIPES)
def test_recipe_exists(just, recipe):
    just.assert_exists(recipe)
```

### 6.2 Dependency Graph
```python
@pytest.mark.justfile
def test_dev_dependencies(just):
    just.assert_depends_on("dev", ["lint", "test"])

@pytest.mark.justfile
def test_ci_transitive(just):
    just.assert_depends_on("ci", ["test"], transitive=True)
```

### 6.3 Parameter Contracts
```python
RECIPE_PARAMS = [
    ("test-file", "FILE"),
    ("deploy", "ENVIRONMENT"),
    ("set-version", "VERSION"),
]

@pytest.mark.justfile
@pytest.mark.parametrize("recipe,param", RECIPE_PARAMS)
def test_recipe_parameters(just, recipe, param):
    just.assert_parameter(recipe, param)
```

### 6.4 Variable Threading
```python
UV_RECIPES = ["test", "lint", "check", "build"]

@pytest.mark.justfile
@pytest.mark.parametrize("recipe", UV_RECIPES)
def test_no_sync_threading(just, recipe):
    # Structural check: variable reference exists in body AST
    just.assert_variable_referenced(recipe, "no_sync")
```

### 6.5 Body Content
```python
@pytest.mark.justfile
def test_check_runs_all_tools(just):
    just.assert_body_contains("check", "ruff format --check")
    just.assert_body_contains("check", "ruff check")
    just.assert_body_contains("check", "ty check")
```

### 6.6 Shebang Classification
```python
SHEBANG_RECIPES = ["deploy", "release", "nb-publish"]
NON_SHEBANG_RECIPES = ["test", "lint", "build"]

@pytest.mark.justfile
@pytest.mark.parametrize("recipe", SHEBANG_RECIPES)
def test_shebang_recipes(just, recipe):
    ...
```

Note: remaining lines for section 6.6 are truncated in the provided screenshot.

---

## 10. What This Package Does NOT Do
- **Execute recipes.** All data comes from `--dump`, `--show`, and `--dry-run`. No recipe is ever run for real. This makes tests safe, fast, and free of side effects.
- **Parse justfile syntax.** We rely entirely on `just` itself for parsing. If `just` can't parse it, the tests fail at data-loading time with a clear error. We don't reimplement the justfile grammar.
- **Test the tools recipes delegate to.** If `just test` runs `pytest`, we don't re-test pytest. We test that the recipe exists, has the right parameters, and calls the right tool. The tool's own test suite handles the rest.
- **Support just versions < 1.13.** The `--dump --dump-format json` flag was added in 1.13. Older versions get a clear error message.
