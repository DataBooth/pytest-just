# Courtesy note to just maintainer (draft)
Hi Casey,

I wanted to share a small ecosystem project I’ve released: `pytest-just` (https://github.com/DataBooth/pytest-just).

It is a pytest plugin focused on testing `justfile` contracts by leaning on:

- `just --dump --dump-format json`
- `just --show`
- `just --dry-run` (for non-shebang smoke checks)

The goal is to help teams catch recipe drift and contract breakage earlier in CI without replacing full integration tests.

If you have a moment, I’d really welcome any feedback on:

1. assumptions this tool makes about stable `just` output contracts
2. edge cases I should account for in the JSON/show flows
3. anything that would make this more useful and less surprising for `just` users

Thanks for building and maintaining `just` — it has been excellent to work with.
