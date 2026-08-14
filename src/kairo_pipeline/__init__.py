"""Shared production-pipeline contracts for Kairo DCC integrations."""

from .diagnostics import Diagnostic, DiagnosticBag, DiagnosticLocation, Severity

__version__ = "0.1.0"

__all__ = [
    "Diagnostic",
    "DiagnosticBag",
    "DiagnosticLocation",
    "Severity",
    "__version__",
]

