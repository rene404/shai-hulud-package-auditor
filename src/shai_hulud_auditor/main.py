from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, HTTPException

from .models import FileMatch, ScanRequest, ScanResult
from .scanner import load_watchlist, scan_path

app = FastAPI(
    title="Shai-Hulud Package Auditor",
    version="0.1.0",
    description="Scan directories for npm manifests and flag packages listed in your Shai-Hulud watchlist.",
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/scan", response_model=ScanResult)
def scan(request: ScanRequest) -> ScanResult:
    root_path = Path(request.root_path).expanduser().resolve()
    watchlist_path = Path(request.watchlist_path).expanduser().resolve()

    try:
        watchlist = load_watchlist(watchlist_path)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except OSError as exc:  # pragma: no cover - unlikely unless FS issues
        raise HTTPException(status_code=500, detail=f"Unable to read watchlist: {exc}") from exc

    try:
        outcome = scan_path(
            root_path,
            watchlist,
            include_lockfiles=request.include_lockfiles,
            exclude_dirs=request.exclude_dirs,
        )
    except (FileNotFoundError, NotADirectoryError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    matches = [
        FileMatch(file_path=str(path), matched_packages=sorted(packages)) for path, packages in outcome.matches
    ]

    return ScanResult(
        root_path=str(root_path),
        watchlist_size=len(watchlist),
        files_scanned=outcome.files_scanned,
        matched_files=len(matches),
        matches=matches,
    )


def run() -> None:
    """Convenience entrypoint for `python -m shai_hulud_auditor`."""
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    import uvicorn

    uvicorn.run("shai_hulud_auditor.main:app", host=host, port=port, reload=False)


if __name__ == "__main__":
    run()
