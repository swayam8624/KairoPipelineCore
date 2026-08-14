"""Command-line entry point for host-neutral pipeline operations."""

from __future__ import annotations

import argparse
from collections.abc import Sequence


def build_parser() -> argparse.ArgumentParser:
    """Build the public command-line parser without executing an operation."""

    parser = argparse.ArgumentParser(
        prog="kairo-pipeline",
        description="Validate and inspect Kairo production-pipeline data.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 0.1.0",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Parse command-line arguments and return a process exit status."""

    build_parser().parse_args(argv)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

