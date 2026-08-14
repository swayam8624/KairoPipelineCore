from __future__ import annotations

from pathlib import Path
import tempfile
import unittest
from unittest import mock

from kairo_pipeline.fingerprint import fingerprint_bytes
from kairo_pipeline.manifest import PublishFile, PublishKind, PublishManifest, load_manifest
from kairo_pipeline.publish import plan_publish, publish_bundle


def build_fixture(root: Path, *, version: int = 1, payload: bytes = b"gltf") -> PublishManifest:
    geometry = root / "geometry"
    geometry.mkdir(parents=True)
    (geometry / "chair.gltf").write_bytes(payload)
    return PublishManifest(
        kind=PublishKind.ASSET,
        project="Portfolio",
        name="Chair",
        version=version,
        source_host="blender",
        source_path="sources/chair.blend",
        source_fingerprint=fingerprint_bytes(b"source"),
        outputs=(
            PublishFile(
                "geometry/chair.gltf",
                "scene",
                fingerprint_bytes(payload),
                "model/gltf+json",
            ),
        ),
    )


class PublishTests(unittest.TestCase):
    def test_plan_does_not_create_destination(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source"
            source.mkdir()
            destination = root / "library"
            manifest = build_fixture(source)
            plan = plan_publish(source, destination, manifest)
            self.assertFalse(destination.exists())
            self.assertEqual(
                plan.target.parts[-4:],
                ("Portfolio", "asset", "Chair", "v001"),
            )

    def test_bundle_is_published_with_verified_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source"
            source.mkdir()
            destination = root / "library"
            manifest = build_fixture(source)

            result = publish_bundle(source, destination, manifest)

            self.assertEqual(result.copied_files, 1)
            self.assertEqual(result.copied_bytes, 4)
            self.assertFalse(result.replaced)
            self.assertEqual(
                (result.target / "geometry/chair.gltf").read_bytes(),
                b"gltf",
            )
            self.assertEqual(load_manifest(result.target / "publish.kairo.json"), manifest)

    def test_fingerprint_mismatch_leaves_destination_absent(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source"
            source.mkdir()
            destination = root / "library"
            manifest = build_fixture(source)
            (source / "geometry/chair.gltf").write_bytes(b"tampered")

            with self.assertRaisesRegex(ValueError, "fingerprint mismatch"):
                publish_bundle(source, destination, manifest)
            self.assertFalse(destination.exists())

    def test_existing_version_requires_explicit_replace(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source"
            source.mkdir()
            destination = root / "library"
            manifest = build_fixture(source)
            publish_bundle(source, destination, manifest)

            with self.assertRaises(FileExistsError):
                publish_bundle(source, destination, manifest)

    def test_replace_failure_restores_previous_publish(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source"
            source.mkdir()
            destination = root / "library"
            original = build_fixture(source, payload=b"old")
            first = publish_bundle(source, destination, original)

            (source / "geometry/chair.gltf").write_bytes(b"new")
            replacement = PublishManifest(
                kind=original.kind,
                project=original.project,
                name=original.name,
                version=original.version,
                source_host=original.source_host,
                source_path=original.source_path,
                source_fingerprint=original.source_fingerprint,
                outputs=(
                    PublishFile(
                        "geometry/chair.gltf",
                        "scene",
                        fingerprint_bytes(b"new"),
                        "model/gltf+json",
                    ),
                ),
            )

            real_replace = __import__("os").replace
            calls = 0

            def fail_second_replace(source_path: object, target_path: object) -> None:
                nonlocal calls
                calls += 1
                if calls == 2:
                    raise OSError("injected publication failure")
                real_replace(source_path, target_path)

            with mock.patch(
                "kairo_pipeline.publish.os.replace",
                side_effect=fail_second_replace,
            ):
                with self.assertRaisesRegex(OSError, "injected"):
                    publish_bundle(source, destination, replacement, replace=True)

            self.assertEqual(
                (first.target / "geometry/chair.gltf").read_bytes(),
                b"old",
            )


if __name__ == "__main__":
    unittest.main()
