# Examples appendix
This appendix catalogues the current example corpus and highlights high-value fixtures to use when developing and testing `pytest-just`.

## Corpus summary
- `examples/public/`: curated public examples with known feature diversity
- `examples/local/`: copied from sibling repositories (`../*/justfile` and `../*/Justfile`)
- Local snapshot details are recorded in `examples/local/MANIFEST.tsv`
- Aggregate ingestion counts and reuse statistics are recorded in `docs/recipe_reuse_report.md`

## Why this corpus matters
Using many real justfiles improves confidence that:
- JSON dump loading remains compatible across varied syntax
- dependency and parameter checks behave correctly in practical projects
- shebang-heavy recipes are classified correctly for dry-run safety
- command-body assertions remain useful across shell styles and tooling ecosystems

## Recommended high-value local examples
Use these first when adding or changing fixture behaviour:

- `examples/local/camino-stjames-app/justfile`
  - large, realistic, many specialist shell recipes
  - strong coverage for shebang scripts, env handling, and command-text assertions
- `examples/local/duckdb-extensions-analysis/justfile`
  - data-engineering workflow style with script and Python orchestration
- `examples/local/model-risk/justfile`
  - structured data/analytics automation patterns
- `examples/local/py-run-mojo/justfile`
  - mixed Python/Mojo command orchestration patterns
- `examples/local/db_public/justfile`
  - includes container-oriented workflows and shell-heavy tasks
- `examples/local/just-compose/justfile`
  - local import/mod usage (good for imported-graph checks)
- `examples/local/mojo-data-star/justfile`
  - alias usage (good for alias mapping checks)

## Public examples to keep
These should remain as compact, intentionally curated fixtures:

- `examples/public/async-compression/justfile`
  - parameters + grouped workflow patterns
- `examples/public/actix-web/justfile`
  - richer dependency graph and workspace command patterns
- `examples/public/martin/justfile`
  - imports/modules and shebang-heavy recipes

## Suggested test matrix
When extending `pytest-just`, run at least:

1. **Core fixture contracts**
   - `assert_exists`, `assert_depends_on`, `assert_parameter`
2. **Recipe-type checks**
   - non-shebang dry-run checks
   - shebang classification checks
3. **Body/variable checks**
   - `assert_body_contains`
   - `assert_variable_referenced`
4. **Cross-file checks**
   - imported recipe visibility
   - alias mapping behaviour

## Candidate future additions
Areas worth adding to examples if encountered:
- justfiles using `[private]` attributes
- justfiles using `[group(\"...\")]` attributes
- intentionally invalid justfiles for negative-path error tests
- nested import trees with duplicate recipe names to stress conflict handling
