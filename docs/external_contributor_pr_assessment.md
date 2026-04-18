# External contributor PR assessment
This document summarises current assessments of open external PRs so we can play them back to the contributor, gather their views, and collaborate effectively on final design and merge decisions.

## Scope
- PR #2: `feat: extend assert_parameter with attribute checking`
- PR #3: `feat: enable dry_run for shebang and script recipes`
- PR #5: `feat: add module support to JustfileFixture`

## PR #2 assessment
### Summary
- Feasibility: **High**
- Alignment with project goals: **High**
- Risk profile: **Low**

### What is good
- Small, localised change to `assert_parameter`.
- Backwards compatible for existing callers.
- Useful extension for contract-level testing.
- Includes targeted tests for success and failure cases.

### Concerns
- Method scope grows from existence checking into attribute verification.
- Assertion failures can expose expected/actual values in logs if users assert sensitive values.

### Collaboration questions for the contributor
1. Should attribute checks stay in `assert_parameter`, or should a dedicated assertion method be introduced for clarity?
2. Can we add docs guidance to avoid asserting secret-like values directly?

## PR #3 assessment
### Summary
- Feasibility: **High**
- Alignment with project goals: **Medium–High**
- Risk profile: **Medium**

### What is good
- Removes an explicit restriction that may be overly conservative.
- Improves practical utility of `dry_run`.
- Includes broad tests across linewise, shebang, script, and args cases.

### Concerns
- Changes current safety posture by removing a defence-in-depth guard.
- Safety now depends on `just --dry-run` semantics remaining stable across versions.
- Dry-run output may still include interpolated values in logs.

### Collaboration questions for the contributor
1. Can we codify minimum supported `just` behaviour/version assumptions for this change?
2. Should this behaviour be default, or guarded by an explicit opt-in setting?
3. Can we add regression tests that explicitly assert non-execution expectations?

## PR #5 assessment
### Summary
- Feasibility: **Medium–High**
- Alignment with project goals: **High strategic value**
- Risk profile: **Low–Medium** (mainly correctness/integrity)

### What is good
- Adds important module support for larger real-world justfile structures.
- Keeps existing API surface mostly intact.
- Strong test intent across flattening, module discovery, and recipe lookups.

### Concerns
- Flattening strategy may overwrite entries if duplicate/ambiguous namepaths occur.
- Some malformed module payloads are skipped rather than failing fast.
- Dependency naming remains module-local, which can be ambiguous across modules.
- Small naming mismatch between PR description and implementation (`all_modules` vs `module_namepaths`).

### Collaboration questions for the contributor
1. Can we add explicit collision detection when flattening namepaths?
2. Should malformed module payloads raise format errors rather than being skipped?
3. Should dependency APIs return fully qualified namepaths, local names, or both?

## Aggregate assessment
### Overall view
- No obvious high-severity direct exploit path across the three PRs.
- PR #2 is low-risk and straightforward to progress.
- PR #3 is the main policy/safety decision due to changed dry-run guard behaviour.
- PR #5 is high-value but needs semantic decisions to avoid ambiguity and edge-case drift.

### Suggested staged collaboration path
1. Align and likely progress PR #2 first.
2. Align safety guardrails and assumptions for PR #3.
3. Resolve module semantics and integrity guardrails for PR #5.

## Suggested contributor playback message
Thanks for the thoughtful PRs. They are directionally strong and add meaningful capability. Before merge, we want to align on a few design and safety details:

- PR #2: whether attribute assertions should remain in `assert_parameter` or move to a dedicated method.
- PR #3: how to codify dry-run safety assumptions (version/behaviour guardrails and tests).
- PR #5: collision handling, malformed module strictness, and dependency namepath semantics.

If we align on those points, we can merge in a staged order with confidence and keep behaviour predictable for users.
