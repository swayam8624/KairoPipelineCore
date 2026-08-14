"""Shared production-pipeline contracts for Kairo DCC integrations."""

from .diagnostics import Diagnostic, DiagnosticBag, DiagnosticLocation, Severity
from .fingerprint import Fingerprint, fingerprint_bytes, fingerprint_file
from .paths import casefold_path_key, normalize_project_path, resolve_project_path

__version__ = "0.1.0"

__all__ = [
    "Diagnostic",
    "DiagnosticBag",
    "DiagnosticLocation",
    "Fingerprint",
    "Severity",
    "casefold_path_key",
    "fingerprint_bytes",
    "fingerprint_file",
    "normalize_project_path",
    "resolve_project_path",
    "__version__",
]

