# Local sibling justfile copies
This directory contains copied `justfile`/`Justfile` files from sibling repositories under `../*`.

## Purpose
- build a broad compatibility corpus for fixture and parser tests
- catch behavioural regressions against real-world usage patterns
- provide a stable snapshot for deterministic testing

## Provenance
- source inventory is recorded in `examples/local/MANIFEST.tsv`
- each row records repository name, source filename, source path, and destination path

## Regeneration
Recreate the corpus from sibling repositories:

```bash
python3 - <<'PY'
from pathlib import Path
import shutil
from datetime import datetime, timezone

root = Path('/Users/mjboothaus/code/github/databooth')
dest_root = Path('/Users/mjboothaus/code/github/databooth/pytest-just/examples/local')
dest_root.mkdir(parents=True, exist_ok=True)

rows = []
for repo in sorted(root.iterdir()):
    if not repo.is_dir() or repo.name == 'pytest-just':
        continue
    for name in ('justfile', 'Justfile'):
        src = repo / name
        if src.is_file():
            target_dir = dest_root / repo.name
            target_dir.mkdir(parents=True, exist_ok=True)
            dst = target_dir / name
            shutil.copy2(src, dst)
            rows.append((repo.name, name, str(src), str(dst)))

manifest = dest_root / 'MANIFEST.tsv'
with manifest.open('w', encoding='utf-8') as f:
    f.write('generated_utc\t' + datetime.now(timezone.utc).isoformat() + '\n')
    f.write('repo\tsource_name\tsource_path\tdestination_path\n')
    for repo_name, source_name, src, dst in rows:
        f.write(f'{repo_name}\t{source_name}\t{src}\t{dst}\n')
PY
```
