"""Certification tests for deterministic, rollback-safe publication."""

from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from kairo_pipeline import (
    PublishFile,
    PublishKind,
    PublishManifest,
    fingerprint_file,
    plan_publish,
    publish_bundle,
    serialize_manifest,
)


class CertificationTests(unittest.TestCase):
    def _manifest(self, source: Path, *, version: int = 1) -> PublishManifest:
        payload = source / "geometry" / "demo.bin"
        return PublishManifest(
            kind=PublishKind.ASSET,
            project="Certification",
            name="Demo",
            version=version,
            source_host="certification",
            source_path="geometry/demo.bin",
            source_fingerprint=fingerprint_file(payload),
            outputs=(
                PublishFile(
                    path="geometry/demo.bin",
                    role="geometry",
                    fingerprint=fingerprint_file(payload),
                ),
            ),
        )

    def test_plan_is_non_mutating_and_failed_replace_preserves_last_good_publish(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source"
            destination = root / "library"
            payload = source / "geometry" / "demo.bin"
            payload.parent.mkdir(parents=True)
            payload.write_bytes(b"version-one")

            manifest = self._manifest(source)
            self.assertEqual(serialize_manifest(manifest), serialize_manifest(manifest))

            plan = plan_publish(source, destination, manifest)
            self.assertFalse(destination.exists(), "dry planning must not create destination state")
            self.assertFalse(plan.target.exists())

            first = publish_bundle(source, destination, manifest)
            published_payload = first.target / "geometry" / "demo.bin"
            published_manifest = first.target / "publish.kairo.json"
            self.assertEqual(published_payload.read_bytes(), b"version-one")
            self.assertTrue(published_manifest.is_file())
            first_manifest_bytes = published_manifest.read_bytes()

            # Mutating source bytes without updating the declared fingerprint is
            # rejected before replacement can disturb the last good target.
            payload.write_bytes(b"tampered-without-manifest-update")
            with self.assertRaises(ValueError):
                publish_bundle(source, destination, manifest, replace=True)
            self.assertEqual(published_payload.read_bytes(), b"version-one")
            self.assertEqual(published_manifest.read_bytes(), first_manifest_bytes)

            # A new validated manifest may explicitly replace the immutable
            # version directory. The previous state remains visible until the
            # final atomic rename succeeds.
            payload.write_bytes(b"version-two")
            replacement_manifest = self._manifest(source)
            second = publish_bundle(
                source,
                destination,
                replacement_manifest,
                replace=True,
            )
            self.assertTrue(second.replaced)
            self.assertEqual((second.target / "geometry" / "demo.bin").read_bytes(), b"version-two")
            self.assertNotEqual(
                (second.target / "publish.kairo.json").read_bytes(),
                first_manifest_bytes,
            )


if __name__ == "__main__":
    unittest.main()
