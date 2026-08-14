"""Versioned, strict, and deterministic cross-DCC publish manifests."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
import json
from pathlib import Path
import re
from types import MappingProxyType
from typing import Any, Mapping, Sequence

from .fingerprint import Fingerprint
from .paths import casefold_path_key, normalize_project_path


SCHEMA = "kairo.publish.v1"
_MAX_MANIFEST_BYTES = 8 * 1024 * 1024
_MAX_ITEMS = 100_000
_IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")


class PublishKind(StrEnum):
    """Department-neutral type of a published production result."""

    ASSET = "asset"
    CACHE = "cache"
    RENDER = "render"


@dataclass(frozen=True, slots=True, order=True)
class PublishFile:
    """One immutable file owned by or referenced from a publish."""

    path: str
    role: str
    fingerprint: Fingerprint
    media_type: str = "application/octet-stream"

    def __post_init__(self) -> None:
        object.__setattr__(self, "path", normalize_project_path(self.path))
        _validate_identifier("publish file role", self.role)
        if not isinstance(self.fingerprint, Fingerprint):
            raise TypeError("publish file fingerprint must be Fingerprint")
        if not isinstance(self.media_type, str) or not self.media_type:
            raise ValueError("publish file media type must not be empty")
        if len(self.media_type) > 255 or "\x00" in self.media_type:
            raise ValueError("publish file media type is invalid")

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "role": self.role,
            "fingerprint": self.fingerprint.to_dict(),
            "media_type": self.media_type,
        }

    @classmethod
    def from_dict(cls, value: object) -> "PublishFile":
        mapping = _require_mapping(value, "publish file")
        _require_exact_keys(
            mapping,
            {"path", "role", "fingerprint", "media_type"},
            "publish file",
        )
        return cls(
            path=_require_string(mapping, "path"),
            role=_require_string(mapping, "role"),
            fingerprint=Fingerprint.from_dict(mapping["fingerprint"]),
            media_type=_require_string(mapping, "media_type"),
        )


@dataclass(frozen=True, slots=True)
class PublishManifest:
    """Complete provenance and payload declaration for one publish version."""

    kind: PublishKind
    project: str
    name: str
    version: int
    source_host: str
    source_path: str
    source_fingerprint: Fingerprint
    outputs: tuple[PublishFile, ...]
    dependencies: tuple[PublishFile, ...] = ()
    metadata: Mapping[str, str] = field(default_factory=dict)
    schema: str = SCHEMA

    def __post_init__(self) -> None:
        if self.schema != SCHEMA:
            raise ValueError(f"unsupported publish manifest schema: {self.schema}")
        if not isinstance(self.kind, PublishKind):
            raise TypeError("publish kind must be PublishKind")
        _validate_identifier("project", self.project)
        _validate_identifier("name", self.name)
        _validate_identifier("source host", self.source_host)
        if not isinstance(self.version, int) or isinstance(self.version, bool):
            raise TypeError("publish version must be an integer")
        if not 1 <= self.version <= 999_999:
            raise ValueError("publish version must be between 1 and 999999")
        object.__setattr__(
            self,
            "source_path",
            normalize_project_path(self.source_path),
        )
        if not isinstance(self.source_fingerprint, Fingerprint):
            raise TypeError("source fingerprint must be Fingerprint")
        outputs = _require_file_tuple(self.outputs, "outputs")
        dependencies = _require_file_tuple(self.dependencies, "dependencies")
        if not outputs:
            raise ValueError("publish manifest must contain at least one output")
        if len(outputs) + len(dependencies) > _MAX_ITEMS:
            raise ValueError("publish manifest exceeds the file-count limit")
        _validate_unique_paths(outputs, dependencies)
        object.__setattr__(self, "outputs", tuple(sorted(outputs)))
        object.__setattr__(self, "dependencies", tuple(sorted(dependencies)))
        object.__setattr__(self, "metadata", _validate_metadata(self.metadata))

    @property
    def publish_directory(self) -> str:
        return f"{self.project}/{self.kind.value}/{self.name}/v{self.version:03d}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "kind": self.kind.value,
            "project": self.project,
            "name": self.name,
            "version": self.version,
            "source_host": self.source_host,
            "source_path": self.source_path,
            "source_fingerprint": self.source_fingerprint.to_dict(),
            "outputs": [item.to_dict() for item in self.outputs],
            "dependencies": [item.to_dict() for item in self.dependencies],
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, value: object) -> "PublishManifest":
        mapping = _require_mapping(value, "publish manifest")
        _require_exact_keys(
            mapping,
            {
                "schema",
                "kind",
                "project",
                "name",
                "version",
                "source_host",
                "source_path",
                "source_fingerprint",
                "outputs",
                "dependencies",
                "metadata",
            },
            "publish manifest",
        )
        try:
            kind = PublishKind(_require_string(mapping, "kind"))
        except ValueError as error:
            raise ValueError("publish kind is unsupported") from error
        return cls(
            schema=_require_string(mapping, "schema"),
            kind=kind,
            project=_require_string(mapping, "project"),
            name=_require_string(mapping, "name"),
            version=_require_integer(mapping, "version"),
            source_host=_require_string(mapping, "source_host"),
            source_path=_require_string(mapping, "source_path"),
            source_fingerprint=Fingerprint.from_dict(mapping["source_fingerprint"]),
            outputs=tuple(
                PublishFile.from_dict(item)
                for item in _require_sequence(mapping, "outputs")
            ),
            dependencies=tuple(
                PublishFile.from_dict(item)
                for item in _require_sequence(mapping, "dependencies")
            ),
            metadata=_require_string_mapping(mapping, "metadata"),
        )


def serialize_manifest(manifest: PublishManifest) -> bytes:
    """Serialize one manifest to canonical UTF-8 JSON with a final newline."""

    if not isinstance(manifest, PublishManifest):
        raise TypeError("manifest must be PublishManifest")
    return (
        json.dumps(
            manifest.to_dict(),
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")


def parse_manifest(payload: bytes) -> PublishManifest:
    """Parse bounded canonical or human-formatted manifest JSON strictly."""

    if not isinstance(payload, bytes):
        raise TypeError("manifest payload must be bytes")
    if not payload or len(payload) > _MAX_MANIFEST_BYTES:
        raise ValueError("manifest payload is empty or exceeds 8 MiB")
    try:
        text = payload.decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        raise ValueError("manifest is not valid UTF-8") from error
    try:
        value = json.loads(
            text,
            parse_constant=lambda constant: (_raise_non_finite(constant)),
        )
    except json.JSONDecodeError as error:
        raise ValueError(
            f"manifest JSON is invalid at line {error.lineno}, column {error.colno}"
        ) from error
    return PublishManifest.from_dict(value)


def load_manifest(path: Path) -> PublishManifest:
    source = Path(path)
    if not source.is_file():
        raise FileNotFoundError(f"publish manifest is not a regular file: {source}")
    if source.stat().st_size > _MAX_MANIFEST_BYTES:
        raise ValueError("manifest file exceeds 8 MiB")
    return parse_manifest(source.read_bytes())


def _validate_identifier(label: str, value: object) -> None:
    if not isinstance(value, str) or not _IDENTIFIER.fullmatch(value):
        raise ValueError(
            f"{label} must contain 1-128 ASCII letters, digits, dots, "
            "underscores, or hyphens and begin with a letter or digit"
        )


def _require_file_tuple(value: object, label: str) -> tuple[PublishFile, ...]:
    if not isinstance(value, tuple):
        raise TypeError(f"manifest {label} must be a tuple")
    if not all(isinstance(item, PublishFile) for item in value):
        raise TypeError(f"manifest {label} must contain PublishFile values")
    return value


def _validate_unique_paths(
    outputs: tuple[PublishFile, ...], dependencies: tuple[PublishFile, ...]
) -> None:
    seen: dict[str, str] = {}
    for item in (*outputs, *dependencies):
        key = casefold_path_key(item.path)
        if key in seen:
            raise ValueError(
                f"publish file path collides with {seen[key]}: {item.path}"
            )
        seen[key] = item.path


def _validate_metadata(value: Mapping[str, str]) -> Mapping[str, str]:
    if not isinstance(value, Mapping):
        raise TypeError("publish metadata must be a mapping")
    if len(value) > 256:
        raise ValueError("publish metadata exceeds 256 entries")
    result: dict[str, str] = {}
    for key, item in sorted(value.items()):
        _validate_identifier("metadata key", key)
        if not isinstance(item, str) or len(item) > 4096 or "\x00" in item:
            raise ValueError(f"metadata value is invalid for key {key}")
        result[key] = item
    return MappingProxyType(result)


def _require_mapping(value: object, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise TypeError(f"{label} must be an object")
    if not all(isinstance(key, str) for key in value):
        raise TypeError(f"{label} keys must be strings")
    return value


def _require_exact_keys(
    value: Mapping[str, Any], keys: set[str], label: str
) -> None:
    missing = sorted(keys - set(value))
    unknown = sorted(set(value) - keys)
    if missing:
        raise ValueError(f"{label} is missing fields: {', '.join(missing)}")
    if unknown:
        raise ValueError(f"{label} contains unknown fields: {', '.join(unknown)}")


def _require_string(value: Mapping[str, Any], key: str) -> str:
    result = value[key]
    if not isinstance(result, str):
        raise TypeError(f"manifest field {key} must be a string")
    return result


def _require_integer(value: Mapping[str, Any], key: str) -> int:
    result = value[key]
    if not isinstance(result, int) or isinstance(result, bool):
        raise TypeError(f"manifest field {key} must be an integer")
    return result


def _require_sequence(value: Mapping[str, Any], key: str) -> Sequence[Any]:
    result = value[key]
    if not isinstance(result, list):
        raise TypeError(f"manifest field {key} must be an array")
    if len(result) > _MAX_ITEMS:
        raise ValueError(f"manifest field {key} exceeds the item limit")
    return result


def _require_string_mapping(value: Mapping[str, Any], key: str) -> Mapping[str, str]:
    result = value[key]
    if not isinstance(result, Mapping):
        raise TypeError(f"manifest field {key} must be an object")
    if not all(isinstance(item_key, str) and isinstance(item, str) for item_key, item in result.items()):
        raise TypeError(f"manifest field {key} must map strings to strings")
    return result


def _raise_non_finite(value: str) -> None:
    raise ValueError(f"manifest contains non-finite number: {value}")

