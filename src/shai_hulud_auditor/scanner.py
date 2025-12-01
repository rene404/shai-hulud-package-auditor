from __future__ import annotations

import os
from dataclasses import dataclass
from json import JSONDecodeError
from pathlib import Path
from typing import Dict, Iterable, List, Set, Tuple


def normalize_name(name: str) -> str:
    """Normalize package names for comparison."""
    return name.strip().lower()


def load_watchlist(watchlist_path: Path) -> Set[str]:
    """Load a newline-delimited list of packages to flag."""
    if not watchlist_path.exists():
        raise FileNotFoundError(f"Watchlist file not found: {watchlist_path}")

    watchlist: Set[str] = set()
    for raw in watchlist_path.read_text(encoding="utf-8").splitlines():
        cleaned = raw.strip()
        if not cleaned or cleaned.startswith("#"):
            continue
        watchlist.add(normalize_name(cleaned))
    return watchlist


def _extract_dependency_names(deps: Dict) -> Set[str]:
    names: Set[str] = set()
    for dep_name, meta in deps.items():
        names.add(normalize_name(dep_name))
        if isinstance(meta, dict):
            nested = meta.get("dependencies", {})
            if isinstance(nested, dict):
                names.update(_extract_dependency_names(nested))
    return names


def parse_package_json(path: Path) -> Set[str]:
    try:
        import json

        with path.open(encoding="utf-8") as handle:
            data = json.load(handle)
    except JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {path}: {exc}") from exc

    packages: Set[str] = set()
    for key in ("dependencies", "devDependencies", "peerDependencies", "optionalDependencies"):
        deps = data.get(key, {})
        if isinstance(deps, dict):
            packages.update(normalize_name(name) for name in deps.keys())
    return packages


def parse_package_lock(path: Path) -> Set[str]:
    try:
        import json

        with path.open(encoding="utf-8") as handle:
            data = json.load(handle)
    except JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {path}: {exc}") from exc

    packages: Set[str] = set()

    if isinstance(data.get("packages"), dict):
        for meta in data["packages"].values():
            if not isinstance(meta, dict):
                continue
            name = meta.get("name")
            if isinstance(name, str):
                packages.add(normalize_name(name))
            deps = meta.get("dependencies", {})
            if isinstance(deps, dict):
                packages.update(_extract_dependency_names(deps))

    deps_root = data.get("dependencies", {})
    if isinstance(deps_root, dict):
        packages.update(_extract_dependency_names(deps_root))

    return packages


@dataclass
class ScanOutcome:
    matches: List[Tuple[Path, Set[str]]]
    files_scanned: int


def scan_path(
    root_path: Path,
    watchlist: Set[str],
    *,
    include_lockfiles: bool = True,
    exclude_dirs: Iterable[str] | None = None,
) -> ScanOutcome:
    if not root_path.exists():
        raise FileNotFoundError(f"Root path not found: {root_path}")
    if not root_path.is_dir():
        raise NotADirectoryError(f"Root path is not a directory: {root_path}")

    exclude_set = set(exclude_dirs or [])
    target_files = {"package.json"}
    if include_lockfiles:
        target_files.update({"package-lock.json", "package.lock.json"})

    matches: List[Tuple[Path, Set[str]]] = []
    files_scanned = 0

    for dirpath, dirnames, filenames in os.walk(root_path):
        dirnames[:] = [d for d in dirnames if d not in exclude_set]
        for filename in filenames:
            if filename not in target_files:
                continue

            current_path = Path(dirpath) / filename
            files_scanned += 1

            if filename == "package.json":
                packages = parse_package_json(current_path)
            else:
                packages = parse_package_lock(current_path)

            matched = {pkg for pkg in packages if pkg in watchlist}
            if matched:
                matches.append((current_path, matched))

    return ScanOutcome(matches=matches, files_scanned=files_scanned)
