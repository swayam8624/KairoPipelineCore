"""Portable project-path validation and containment helpers."""

from __future__ import annotations

from pathlib import Path, PurePosixPath
import re


_WINDOWS_DRIVE = re.compile(r"^[A-Za-z]:")
_MAX_PATH_LENGTH = 1024


def normalize_project_path(value: str) -> str:
    """Validate and normalize a project-relative path.

    Input:
        A forward-slash path authored by a DCC adapter or manifest.

    Output:
        The canonical POSIX spelling without redundant ``.`` components.

    Task:
        Reject roots, parent traversal, Windows separators, drive prefixes,
        empty paths, control characters, and names that become ambiguous on
        common cross-platform filesystems.
    """

    if not isinstance(value, str):
        raise TypeError("project path must be a string")
    if not value or len(value) > _MAX_PATH_LENGTH:
        raise ValueError("project path must contain 1-1024 characters")
    if "\\" in value:
        raise ValueError("project path must use forward slashes")
    if value.startswith("/") or _WINDOWS_DRIVE.match(value):
        raise ValueError("project path must be relative")
    if any(ord(character) < 32 for character in value):
        raise ValueError("project path must not contain control characters")

    source_parts = value.split("/")
    if any(part == ".." for part in source_parts):
        raise ValueError("project path must not traverse a parent directory")

    parts = [part for part in source_parts if part not in ("", ".")]
    if not parts:
        raise ValueError("project path must identify a file or directory")
    for part in parts:
        if part[-1:] in (".", " "):
            raise ValueError("project path components must not end in dot or space")
        if ":" in part:
            raise ValueError("project path components must not contain colons")

    return PurePosixPath(*parts).as_posix()


def casefold_path_key(value: str) -> str:
    """Return a normalized case-insensitive uniqueness key."""

    return normalize_project_path(value).casefold()


def resolve_project_path(project_root: Path, value: str) -> Path:
    """Resolve a portable project path and prove it remains inside the root."""

    root = Path(project_root).resolve(strict=False)
    candidate = root.joinpath(*PurePosixPath(normalize_project_path(value)).parts)
    resolved = candidate.resolve(strict=False)
    try:
        resolved.relative_to(root)
    except ValueError as error:
        raise ValueError("resolved project path escapes the project root") from error
    return resolved

