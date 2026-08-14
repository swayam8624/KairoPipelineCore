"""Command-line entry point for host-neutral pipeline operations."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
import json
from pathlib import Path
import sys

from .manifest import load_manifest
from .publish import plan_publish, publish_bundle
from .sequences import FramePattern, scan_sequence


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
    subcommands = parser.add_subparsers(dest="command")

    validate = subcommands.add_parser(
        "validate-manifest",
        help="Parse and validate one publish manifest.",
    )
    validate.add_argument("manifest", type=Path)
    validate.add_argument("--json", action="store_true", dest="as_json")

    sequence = subcommands.add_parser(
        "scan-sequence",
        help="Report missing and out-of-range sequence frames.",
    )
    sequence.add_argument("project_root", type=Path)
    sequence.add_argument("pattern")
    sequence.add_argument("first", type=int)
    sequence.add_argument("last", type=int)
    sequence.add_argument("--json", action="store_true", dest="as_json")

    publish = subcommands.add_parser(
        "publish",
        help="Validate and atomically publish a production bundle.",
    )
    publish.add_argument("source_root", type=Path)
    publish.add_argument("destination_root", type=Path)
    publish.add_argument("manifest", type=Path)
    publish.add_argument("--replace", action="store_true")
    publish.add_argument("--dry-run", action="store_true")
    publish.add_argument("--json", action="store_true", dest="as_json")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Parse command-line arguments and return a process exit status."""

    parser = build_parser()
    arguments = parser.parse_args(argv)
    try:
        if arguments.command is None:
            parser.print_help()
            return 0
        if arguments.command == "validate-manifest":
            manifest = load_manifest(arguments.manifest)
            result = {
                "valid": True,
                "schema": manifest.schema,
                "kind": manifest.kind.value,
                "project": manifest.project,
                "name": manifest.name,
                "version": manifest.version,
                "outputs": len(manifest.outputs),
                "dependencies": len(manifest.dependencies),
            }
            _print_result(result, arguments.as_json)
            return 0
        if arguments.command == "scan-sequence":
            scan = scan_sequence(
                arguments.project_root,
                FramePattern.parse(arguments.pattern),
                arguments.first,
                arguments.last,
            )
            result = {
                "complete": scan.complete,
                "pattern": scan.pattern.canonical(),
                "first": scan.first,
                "last": scan.last,
                "existing": list(scan.existing),
                "missing": list(scan.missing),
                "outside_range": list(scan.outside_range),
            }
            _print_result(result, arguments.as_json)
            return 0 if scan.complete else 1
        if arguments.command == "publish":
            manifest = load_manifest(arguments.manifest)
            if arguments.dry_run:
                plan = plan_publish(
                    arguments.source_root,
                    arguments.destination_root,
                    manifest,
                    replace=arguments.replace,
                )
                result = {
                    "status": "planned",
                    "target": str(plan.target),
                    "files": len(plan.files),
                    "replacing": plan.replacing,
                    "manifest_sha256": plan.manifest_fingerprint.sha256,
                }
            else:
                published = publish_bundle(
                    arguments.source_root,
                    arguments.destination_root,
                    manifest,
                    replace=arguments.replace,
                )
                result = {
                    "status": "published",
                    "target": str(published.target),
                    "files": published.copied_files,
                    "bytes": published.copied_bytes,
                    "replaced": published.replaced,
                    "manifest_sha256": published.manifest_fingerprint.sha256,
                }
            _print_result(result, arguments.as_json)
            return 0
        raise RuntimeError(f"unhandled command: {arguments.command}")
    except (OSError, TypeError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


def _print_result(value: dict[str, object], as_json: bool) -> None:
    if as_json:
        print(json.dumps(value, sort_keys=True, separators=(",", ":")))
        return
    for key, item in value.items():
        print(f"{key}: {item}")


if __name__ == "__main__":
    raise SystemExit(main())
