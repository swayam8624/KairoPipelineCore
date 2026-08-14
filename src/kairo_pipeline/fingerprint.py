"""Deterministic content fingerprints for source and dependency tracking."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path
import re
from typing import BinaryIO


_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_READ_SIZE = 1024 * 1024


@dataclass(frozen=True, slots=True, order=True)
class Fingerprint:
    """SHA-256 digest paired with the exact number of fingerprinted bytes."""

    sha256: str
    size: int

    def __post_init__(self) -> None:
        if not isinstance(self.sha256, str) or not _SHA256.fullmatch(self.sha256):
            raise ValueError("fingerprint digest must be lowercase SHA-256 hex")
        if not isinstance(self.size, int) or isinstance(self.size, bool) or self.size < 0:
            raise ValueError("fingerprint size must be a non-negative integer")

    def to_dict(self) -> dict[str, object]:
        return {"sha256": self.sha256, "size": self.size}

    @classmethod
    def from_dict(cls, value: object) -> "Fingerprint":
        if not isinstance(value, dict):
            raise TypeError("fingerprint must be an object")
        if set(value) != {"sha256", "size"}:
            raise ValueError("fingerprint must contain sha256 and size only")
        return cls(sha256=value["sha256"], size=value["size"])


def fingerprint_bytes(value: bytes) -> Fingerprint:
    """Fingerprint an immutable in-memory payload."""

    if not isinstance(value, bytes):
        raise TypeError("fingerprint input must be bytes")
    return Fingerprint(hashlib.sha256(value).hexdigest(), len(value))


def fingerprint_stream(stream: BinaryIO) -> Fingerprint:
    """Fingerprint a binary stream from its current position in bounded reads."""

    digest = hashlib.sha256()
    size = 0
    while True:
        chunk = stream.read(_READ_SIZE)
        if not chunk:
            break
        if not isinstance(chunk, bytes):
            raise TypeError("fingerprint stream must produce bytes")
        digest.update(chunk)
        size += len(chunk)
    return Fingerprint(digest.hexdigest(), size)


def fingerprint_file(path: Path) -> Fingerprint:
    """Fingerprint a regular file without loading it entirely into memory."""

    source = Path(path)
    if not source.is_file():
        raise FileNotFoundError(f"fingerprint source is not a regular file: {source}")
    with source.open("rb") as stream:
        return fingerprint_stream(stream)

