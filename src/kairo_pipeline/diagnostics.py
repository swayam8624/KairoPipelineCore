"""Structured diagnostics shared by interactive DCC tools and headless CI."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
import re
from typing import Any, Iterable, Iterator, Mapping


_DIAGNOSTIC_CODE = re.compile(r"^[A-Z][A-Z0-9_]{2,63}$")
_MAX_TEXT_LENGTH = 4096


class Severity(StrEnum):
    """Impact of a diagnostic on a production publish operation."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass(frozen=True, slots=True)
class DiagnosticLocation:
    """Navigable host location associated with a diagnostic.

    `host` identifies the adapter, such as ``blender`` or ``houdini``.
    `resource` is a portable source file or scene identifier. `object_path`
    and `property_name` are host-owned opaque navigation tokens; the shared
    package never attempts to resolve them itself.
    """

    host: str
    resource: str = ""
    object_path: str = ""
    property_name: str = ""

    def __post_init__(self) -> None:
        for label, value in (
            ("host", self.host),
            ("resource", self.resource),
            ("object_path", self.object_path),
            ("property_name", self.property_name),
        ):
            _validate_text(label, value, allow_empty=label != "host")

    def to_dict(self) -> dict[str, str]:
        return {
            "host": self.host,
            "resource": self.resource,
            "object_path": self.object_path,
            "property_name": self.property_name,
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "DiagnosticLocation":
        _reject_unknown_keys(
            value,
            {"host", "resource", "object_path", "property_name"},
            "diagnostic location",
        )
        return cls(
            host=_required_string(value, "host"),
            resource=_optional_string(value, "resource"),
            object_path=_optional_string(value, "object_path"),
            property_name=_optional_string(value, "property_name"),
        )


@dataclass(frozen=True, slots=True)
class Diagnostic:
    """One deterministic and optionally navigable production diagnostic."""

    code: str
    severity: Severity
    message: str
    location: DiagnosticLocation | None = None
    suggestion: str = ""

    def __post_init__(self) -> None:
        if not _DIAGNOSTIC_CODE.fullmatch(self.code):
            raise ValueError(
                "diagnostic code must contain 3-64 uppercase ASCII letters, "
                "digits, or underscores and begin with a letter"
            )
        if not isinstance(self.severity, Severity):
            raise TypeError("diagnostic severity must be a Severity value")
        _validate_text("message", self.message, allow_empty=False)
        _validate_text("suggestion", self.suggestion, allow_empty=True)
        if self.location is not None and not isinstance(
            self.location, DiagnosticLocation
        ):
            raise TypeError("diagnostic location must be DiagnosticLocation or None")

    @property
    def blocks_publish(self) -> bool:
        return self.severity is Severity.ERROR

    def sort_key(self) -> tuple[str, str, str, str, str]:
        location = self.location or DiagnosticLocation(host="unknown")
        return (
            self.severity.value,
            self.code,
            location.resource,
            location.object_path,
            location.property_name,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "severity": self.severity.value,
            "message": self.message,
            "location": self.location.to_dict() if self.location else None,
            "suggestion": self.suggestion,
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "Diagnostic":
        _reject_unknown_keys(
            value,
            {"code", "severity", "message", "location", "suggestion"},
            "diagnostic",
        )
        raw_location = value.get("location")
        if raw_location is not None and not isinstance(raw_location, Mapping):
            raise TypeError("diagnostic location must be an object or null")
        try:
            severity = Severity(_required_string(value, "severity"))
        except ValueError as error:
            raise ValueError("diagnostic severity is unsupported") from error
        return cls(
            code=_required_string(value, "code"),
            severity=severity,
            message=_required_string(value, "message"),
            location=(
                DiagnosticLocation.from_dict(raw_location)
                if raw_location is not None
                else None
            ),
            suggestion=_optional_string(value, "suggestion"),
        )


class DiagnosticBag:
    """Mutable collector with deterministic snapshots and publish status."""

    __slots__ = ("_items",)

    def __init__(self, diagnostics: Iterable[Diagnostic] = ()) -> None:
        self._items: list[Diagnostic] = []
        self.extend(diagnostics)

    def add(self, diagnostic: Diagnostic) -> None:
        if not isinstance(diagnostic, Diagnostic):
            raise TypeError("diagnostic bag accepts Diagnostic values only")
        self._items.append(diagnostic)

    def extend(self, diagnostics: Iterable[Diagnostic]) -> None:
        for diagnostic in diagnostics:
            self.add(diagnostic)

    @property
    def blocks_publish(self) -> bool:
        return any(item.blocks_publish for item in self._items)

    def snapshot(self) -> tuple[Diagnostic, ...]:
        return tuple(sorted(self._items, key=Diagnostic.sort_key))

    def __len__(self) -> int:
        return len(self._items)

    def __iter__(self) -> Iterator[Diagnostic]:
        return iter(self.snapshot())


def _validate_text(label: str, value: object, *, allow_empty: bool) -> None:
    if not isinstance(value, str):
        raise TypeError(f"{label} must be a string")
    if not allow_empty and not value:
        raise ValueError(f"{label} must not be empty")
    if len(value) > _MAX_TEXT_LENGTH:
        raise ValueError(f"{label} exceeds {_MAX_TEXT_LENGTH} characters")
    if "\x00" in value:
        raise ValueError(f"{label} must not contain NUL bytes")


def _reject_unknown_keys(
    value: Mapping[str, Any], allowed: set[str], label: str
) -> None:
    unknown = sorted(set(value) - allowed)
    if unknown:
        raise ValueError(f"{label} contains unknown fields: {', '.join(unknown)}")


def _required_string(value: Mapping[str, Any], key: str) -> str:
    if key not in value:
        raise ValueError(f"required field is missing: {key}")
    result = value[key]
    if not isinstance(result, str):
        raise TypeError(f"field {key} must be a string")
    return result


def _optional_string(value: Mapping[str, Any], key: str) -> str:
    result = value.get(key, "")
    if not isinstance(result, str):
        raise TypeError(f"field {key} must be a string")
    return result

