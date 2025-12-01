import json
from pathlib import Path

from shai_hulud_auditor.scanner import load_watchlist, scan_path


def test_load_watchlist_skips_comments(tmp_path: Path) -> None:
    watchlist_path = tmp_path / "watchlist.txt"
    watchlist_path.write_text("# comment\nleft-pad\n  lodash \n", encoding="utf-8")

    watchlist = load_watchlist(watchlist_path)
    assert watchlist == {"left-pad", "lodash"}


def test_scan_package_json(tmp_path: Path) -> None:
    root = tmp_path / "project"
    root.mkdir()
    package_json = root / "package.json"
    package_json.write_text(
        json.dumps({"dependencies": {"left-pad": "1.0.0"}, "devDependencies": {"typescript": "5.0.0"}}),
        encoding="utf-8",
    )

    outcome = scan_path(root, {"left-pad"}, include_lockfiles=False)

    assert outcome.files_scanned == 1
    assert len(outcome.matches) == 1
    assert outcome.matches[0][0] == package_json
    assert outcome.matches[0][1] == {"left-pad"}


def test_scan_package_lock(tmp_path: Path) -> None:
    root = tmp_path / "project"
    root.mkdir()
    lockfile = root / "package-lock.json"
    lockfile.write_text(
        json.dumps(
            {
                "name": "demo",
                "packages": {
                    "": {"name": "demo", "dependencies": {"left-pad": "1.0.0"}},
                    "node_modules/left-pad": {"version": "1.0.0", "resolved": "http://example.com"},
                },
                "dependencies": {"left-pad": {"version": "1.0.0"}},
            }
        ),
        encoding="utf-8",
    )

    outcome = scan_path(root, {"left-pad"})

    assert outcome.files_scanned == 1
    assert outcome.matches[0][0] == lockfile
    assert outcome.matches[0][1] == {"left-pad"}
