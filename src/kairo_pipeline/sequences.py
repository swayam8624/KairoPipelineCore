"""Frame-sequence patterns and deterministic filesystem inspection."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path, PurePosixPath
import re

from .paths import normalize_project_path, resolve_project_path


_PRINTF_TOKEN = re.compile(r"%0([1-9]|1[0-2])d")
_HASH_TOKEN = re.compile(r"(#{1,12})")


@dataclass(frozen=True, slots=True)
class FramePattern:
    """Portable image/cache sequence path containing one frame token."""

    prefix: str
    suffix: str
    padding: int

    def __post_init__(self) -> None:
        if not isinstance(self.prefix, str) or not isinstance(self.suffix, str):
            raise TypeError("frame pattern prefix and suffix must be strings")
        if not isinstance(self.padding, int) or not 1 <= self.padding <= 12:
            raise ValueError("frame padding must be between 1 and 12")
        normalize_project_path(f"{self.prefix}{'#' * self.padding}{self.suffix}")

    @classmethod
    def parse(cls, value: str) -> "FramePattern":
        """Parse exactly one ``####`` or ``%04d`` style token."""

        normalized = normalize_project_path(value)
        matches = list(_PRINTF_TOKEN.finditer(normalized)) + list(
            _HASH_TOKEN.finditer(normalized)
        )
        matches.sort(key=lambda match: match.start())
        if len(matches) != 1:
            raise ValueError("frame pattern must contain exactly one frame token")
        match = matches[0]
        padding = (
            int(match.group(1))
            if match.re is _PRINTF_TOKEN
            else len(match.group(1))
        )
        return cls(normalized[: match.start()], normalized[match.end() :], padding)

    def canonical(self) -> str:
        return f"{self.prefix}{'#' * self.padding}{self.suffix}"

    def path_for_frame(self, frame: int) -> str:
        if not isinstance(frame, int) or isinstance(frame, bool):
            raise TypeError("frame number must be an integer")
        sign = "-" if frame < 0 else ""
        digits = f"{abs(frame):0{self.padding}d}"
        return normalize_project_path(f"{self.prefix}{sign}{digits}{self.suffix}")

    def filename_regex(self) -> re.Pattern[str]:
        name_prefix = PurePosixPath(self.prefix).name
        return re.compile(
            rf"^{re.escape(name_prefix)}(-?\d{{{self.padding},}}){re.escape(self.suffix)}$"
        )

    def directory(self) -> str:
        parent = PurePosixPath(self.prefix).parent
        return "" if parent == PurePosixPath(".") else parent.as_posix()


@dataclass(frozen=True, slots=True)
class SequenceScan:
    """Existing and missing frames for one requested inclusive range."""

    pattern: FramePattern
    first: int
    last: int
    existing: tuple[int, ...]
    missing: tuple[int, ...]
    outside_range: tuple[int, ...]

    @property
    def complete(self) -> bool:
        return not self.missing


def scan_sequence(
    project_root: Path,
    pattern: FramePattern,
    first: int,
    last: int,
) -> SequenceScan:
    """Inspect a sequence directory without following paths outside the project."""

    if not isinstance(first, int) or isinstance(first, bool):
        raise TypeError("first frame must be an integer")
    if not isinstance(last, int) or isinstance(last, bool):
        raise TypeError("last frame must be an integer")
    if first > last:
        raise ValueError("first frame must not exceed last frame")
    if last - first > 1_000_000:
        raise ValueError("requested frame range exceeds one million frames")

    directory_path = (
        resolve_project_path(project_root, pattern.directory())
        if pattern.directory()
        else Path(project_root).resolve(strict=False)
    )
    matcher = pattern.filename_regex()
    discovered: set[int] = set()
    if directory_path.is_dir():
        for child in directory_path.iterdir():
            if not child.is_file():
                continue
            match = matcher.fullmatch(child.name)
            if match:
                discovered.add(int(match.group(1)))

    expected = set(range(first, last + 1))
    return SequenceScan(
        pattern=pattern,
        first=first,
        last=last,
        existing=tuple(sorted(discovered & expected)),
        missing=tuple(sorted(expected - discovered)),
        outside_range=tuple(sorted(discovered - expected)),
    )

