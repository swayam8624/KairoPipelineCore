"""Shared production-pipeline contracts for Kairo DCC integrations."""

from .diagnostics import Diagnostic, DiagnosticBag, DiagnosticLocation, Severity
from .fingerprint import Fingerprint, fingerprint_bytes, fingerprint_file
from .manifest import (
    PublishFile,
    PublishKind,
    PublishManifest,
    load_manifest,
    parse_manifest,
    serialize_manifest,
)
from .paths import casefold_path_key, normalize_project_path, resolve_project_path
from .sequences import FramePattern, SequenceScan, scan_sequence

__version__ = "0.1.0"

__all__ = [
    "Diagnostic",
    "DiagnosticBag",
    "DiagnosticLocation",
    "Fingerprint",
    "FramePattern",
    "PublishFile",
    "PublishKind",
    "PublishManifest",
    "SequenceScan",
    "Severity",
    "casefold_path_key",
    "fingerprint_bytes",
    "fingerprint_file",
    "load_manifest",
    "normalize_project_path",
    "parse_manifest",
    "resolve_project_path",
    "scan_sequence",
    "serialize_manifest",
    "__version__",
]
