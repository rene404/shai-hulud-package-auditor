# Shai-Hulud Package Auditor

FastAPI service and Python library that crawls a directory tree, finds `package.json` / `package-lock.json` files, and flags packages that appear in a Shai-Hulud watchlist (newline-delimited text file).

## Plan and Roadmap
- Build a FastAPI endpoint to submit a root path and watchlist file, returning any matches with minimal overhead.
- Implement reusable scanning utilities that normalize package names and understand both `package.json` and `package-lock.json` structures.
- Ship a simple test suite around the parser and scanner to guard basic behaviors.
- Next: add CLI for offline use, optional CSV/JSONL output, and richer ignore rules (globs, hidden dirs).

## Quickstart (uv)
1) Create a virtual environment with uv:
```bash
uv venv
source .venv/bin/activate
```
2) Install dependencies from `pyproject.toml`:
```bash
uv sync
```
3) Start the API:
```bash
uv run uvicorn shai_hulud_auditor.main:app --host 0.0.0.0 --port 8000
```
4) Prepare a watchlist text file (one package per line, `#` starts a comment):
```
left-pad
# internal libs
custom-package
```
5) Call the scan endpoint:
```bash
curl -X POST http://localhost:8000/scan \
  -H "Content-Type: application/json" \
  -d '{"root_path": "/path/to/project", "watchlist_path": "/path/to/watchlist.txt"}'
```

## API
- `GET /health` → `{"status": "ok"}`.
- `POST /scan` → body:
  - `root_path` (str): directory to recurse.
  - `watchlist_path` (str): path to text file with package names.
  - `exclude_dirs` (list[str], optional): directory names to skip; defaults to `["node_modules", ".git"]`.
  - `include_lockfiles` (bool, optional): parse `package-lock.json` / `package.lock.json`; default `true`.
  Response includes `files_scanned`, `matched_files`, and a list of matched packages per file.

## Library Usage
```python
from pathlib import Path
from shai_hulud_auditor.scanner import load_watchlist, scan_path

watchlist = load_watchlist(Path("watchlist.txt"))
outcome = scan_path(Path("/path/to/root"), watchlist)

for path, packages in outcome.matches:
    print(path, sorted(packages))
```
