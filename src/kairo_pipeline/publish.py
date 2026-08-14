"""Validated atomic publication of immutable production bundles."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import shutil
import tempfile
from typing import Iterable

from .fingerprint import Fingerprint, fingerprint_bytes, fingerprint_file
from .manifest import PublishFile, PublishManifest, serialize_manifest
from .paths import resolve_project_path


@dataclass(frozen=True, slots=True)
class PublishPlan:
    """Fully validated filesystem mutation plan produced before staging."""

    target: Path
    files: tuple[PublishFile, ...]
    manifest_fingerprint: Fingerprint
    replacing: bool


@dataclass(frozen=True, slots=True)
class PublishResult:
    """Evidence returned after the atomic target rename succeeds."""

    target: Path
    copied_files: int
    copied_bytes: int
    manifest_fingerprint: Fingerprint
    replaced: bool


def plan_publish(
    source_root: Path,
    destination_root: Path,
    manifest: PublishManifest,
    *,
    replace: bool = False,
) -> PublishPlan:
    """Validate all inputs and return the exact intended destination.

    No directory is created and no destination content is changed by this
    function. Every payload fingerprint is checked before publication begins.
    """

    if not isinstance(manifest, PublishManifest):
        raise TypeError("manifest must be PublishManifest")
    if not isinstance(replace, bool):
        raise TypeError("replace must be a boolean")
    source = Path(source_root)
    if not source.is_dir():
        raise NotADirectoryError(f"publish source root is not a directory: {source}")
    destination = Path(destination_root).resolve(strict=False)
    if destination.exists() and not destination.is_dir():
        raise NotADirectoryError(
            f"publish destination root is not a directory: {destination}"
        )

    files = tuple(sorted((*manifest.outputs, *manifest.dependencies)))
    for item in files:
        source_file = resolve_project_path(source, item.path)
        if source_file.is_symlink():
            raise ValueError(f"publish input must not be a symbolic link: {item.path}")
        actual = fingerprint_file(source_file)
        if actual != item.fingerprint:
            raise ValueError(
                f"publish input fingerprint mismatch for {item.path}: "
                f"expected {item.fingerprint.sha256}, got {actual.sha256}"
            )

    target = resolve_project_path(destination, manifest.publish_directory)
    if target.exists():
        if not target.is_dir() or target.is_symlink():
            raise FileExistsError(f"publish target is not a regular directory: {target}")
        if not replace:
            raise FileExistsError(f"publish version already exists: {target}")

    manifest_fingerprint = fingerprint_bytes(serialize_manifest(manifest))
    return PublishPlan(
        target=target,
        files=files,
        manifest_fingerprint=manifest_fingerprint,
        replacing=target.exists(),
    )


def publish_bundle(
    source_root: Path,
    destination_root: Path,
    manifest: PublishManifest,
    *,
    replace: bool = False,
) -> PublishResult:
    """Copy, verify, and atomically expose one complete publish bundle."""

    source = Path(source_root).resolve(strict=True)
    destination = Path(destination_root).resolve(strict=False)
    plan = plan_publish(source, destination, manifest, replace=replace)
    created_parents = _create_target_parents(destination, plan.target.parent)
    staging = Path(
        tempfile.mkdtemp(prefix=f".{manifest.name}.staging-", dir=plan.target.parent)
    )
    backup: Path | None = None
    copied_bytes = 0
    try:
        for item in plan.files:
            source_file = resolve_project_path(source, item.path)
            staged_file = resolve_project_path(staging, item.path)
            staged_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source_file, staged_file, follow_symlinks=False)
            if fingerprint_file(staged_file) != item.fingerprint:
                raise OSError(f"staged file verification failed: {item.path}")
            copied_bytes += item.fingerprint.size

        manifest_path = staging / "publish.kairo.json"
        manifest_payload = serialize_manifest(manifest)
        _write_new_file(manifest_path, manifest_payload)
        if fingerprint_file(manifest_path) != plan.manifest_fingerprint:
            raise OSError("staged publish manifest verification failed")

        if plan.replacing:
            backup = Path(
                tempfile.mkdtemp(
                    prefix=f".{manifest.name}.backup-",
                    dir=plan.target.parent,
                )
            )
            backup.rmdir()
            os.replace(plan.target, backup)
        try:
            os.replace(staging, plan.target)
        except BaseException:
            if backup is not None and backup.exists() and not plan.target.exists():
                os.replace(backup, plan.target)
                backup = None
            raise

        if backup is not None:
            shutil.rmtree(backup)
            backup = None

        return PublishResult(
            target=plan.target,
            copied_files=len(plan.files),
            copied_bytes=copied_bytes,
            manifest_fingerprint=plan.manifest_fingerprint,
            replaced=plan.replacing,
        )
    except BaseException:
        if staging.exists():
            shutil.rmtree(staging)
        if backup is not None and backup.exists() and not plan.target.exists():
            os.replace(backup, plan.target)
            backup = None
        if backup is not None and backup.exists():
            shutil.rmtree(backup)
        _remove_empty_parents(created_parents)
        raise


def _create_target_parents(destination: Path, parent: Path) -> tuple[Path, ...]:
    try:
        parent.relative_to(destination)
    except ValueError as error:
        raise ValueError(
            "publish parent does not descend from destination root"
        ) from error
    missing: list[Path] = []
    cursor = parent
    while not cursor.exists():
        missing.append(cursor)
        if cursor == destination:
            break
        cursor = cursor.parent
    for directory in reversed(missing):
        directory.mkdir()
    return tuple(missing)


def _remove_empty_parents(paths: Iterable[Path]) -> None:
    for path in paths:
        try:
            path.rmdir()
        except OSError:
            pass


def _write_new_file(path: Path, payload: bytes) -> None:
    with path.open("xb") as stream:
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())
