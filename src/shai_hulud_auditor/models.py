from typing import List

from pydantic import BaseModel, Field


class ScanRequest(BaseModel):
    root_path: str = Field(..., description="Directory to scan recursively.")
    watchlist_path: str = Field(..., description="Path to the text file that lists packages of concern.")
    exclude_dirs: List[str] = Field(
        default_factory=lambda: ["node_modules", ".git"],
        description="Directory names to skip during the scan.",
    )
    include_lockfiles: bool = Field(
        default=True, description="Whether to also parse package-lock.json / package.lock.json files."
    )


class FileMatch(BaseModel):
    file_path: str
    matched_packages: List[str]


class ScanResult(BaseModel):
    root_path: str
    watchlist_size: int
    files_scanned: int
    matched_files: int
    matches: List[FileMatch]
