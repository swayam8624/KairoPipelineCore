from __future__ import annotations

import unittest

from kairo_pipeline.fingerprint import fingerprint_bytes
from kairo_pipeline.manifest import (
    PublishFile,
    PublishKind,
    PublishManifest,
    parse_manifest,
    serialize_manifest,
)


def make_manifest() -> PublishManifest:
    return PublishManifest(
        kind=PublishKind.ASSET,
        project="Portfolio",
        name="WorkshopChair",
        version=2,
        source_host="blender",
        source_path="scenes/workshop.blend",
        source_fingerprint=fingerprint_bytes(b"blend-source"),
        outputs=(
            PublishFile(
                "geometry/chair.gltf",
                "scene",
                fingerprint_bytes(b"gltf"),
                "model/gltf+json",
            ),
        ),
        dependencies=(
            PublishFile(
                "textures/chair_basecolor.png",
                "basecolor",
                fingerprint_bytes(b"png"),
                "image/png",
            ),
        ),
        metadata={"artist": "Test Artist", "units": "meter"},
    )


class ManifestTests(unittest.TestCase):
    def test_round_trip_is_byte_deterministic(self) -> None:
        manifest = make_manifest()
        payload = serialize_manifest(manifest)
        parsed = parse_manifest(payload)
        self.assertEqual(serialize_manifest(parsed), payload)
        self.assertEqual(
            parsed.publish_directory,
            "Portfolio/asset/WorkshopChair/v002",
        )

    def test_unknown_root_field_is_rejected(self) -> None:
        value = make_manifest().to_dict()
        value["unexpected"] = True
        import json

        with self.assertRaisesRegex(ValueError, "unknown fields"):
            parse_manifest(json.dumps(value).encode())

    def test_duplicate_root_and_nested_keys_are_rejected(self) -> None:
        payload = serialize_manifest(make_manifest())

        # A silently overwritten version or hash can undermine provenance if
        # different tools interpret duplicate JSON object keys differently.
        root_duplicate = payload.replace(
            b'"version":2', b'"version":2,"version":3'
        )
        self.assertNotEqual(root_duplicate, payload)
        with self.assertRaisesRegex(ValueError, "duplicate JSON key: version"):
            parse_manifest(root_duplicate)

        metadata_duplicate = payload.replace(
            b'"artist":"Test Artist"',
            b'"artist":"Test Artist","artist":"Different Artist"',
        )
        self.assertNotEqual(metadata_duplicate, payload)
        with self.assertRaisesRegex(ValueError, "duplicate JSON key: artist"):
            parse_manifest(metadata_duplicate)

        nested_duplicate = payload.replace(
            b'"media_type":"model/gltf+json"',
            b'"media_type":"model/gltf+json","media_type":"invalid"',
        )
        self.assertNotEqual(nested_duplicate, payload)
        with self.assertRaisesRegex(ValueError, "duplicate JSON key: media_type"):
            parse_manifest(nested_duplicate)

    def test_project_and_asset_directory_names_are_portable(self) -> None:
        # Identifier regex alone permitted DOS device names such as CON. A
        # valid manifest could publish on Linux and fail when reopened on
        # Windows because project/name become real directory components.
        from dataclasses import replace

        for name in ("CON", "aux", "NUL.txt", "PRN", "COM1", "LPT9"):
            with self.subTest(name=name):
                with self.assertRaises(ValueError):
                    replace(make_manifest(), project=name)
                with self.assertRaises(ValueError):
                    replace(make_manifest(), name=name)
        self.assertEqual(replace(make_manifest(), project="Conifer").project, "Conifer")
        self.assertEqual(replace(make_manifest(), name="COM10").name, "COM10")

    def test_case_insensitive_file_collision_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "collides"):
            PublishManifest(
                kind=PublishKind.ASSET,
                project="Portfolio",
                name="Collision",
                version=1,
                source_host="maya",
                source_path="scene.ma",
                source_fingerprint=fingerprint_bytes(b"source"),
                outputs=(
                    PublishFile(
                        "Textures/Wood.png",
                        "texture",
                        fingerprint_bytes(b"a"),
                    ),
                    PublishFile(
                        "textures/wood.PNG",
                        "texture",
                        fingerprint_bytes(b"b"),
                    ),
                ),
            )

    def test_non_finite_json_number_is_rejected(self) -> None:
        payload = serialize_manifest(make_manifest()).replace(b"\"version\":2", b"\"version\":NaN")
        with self.assertRaisesRegex(ValueError, "non-finite"):
            parse_manifest(payload)

    def test_manifest_requires_output(self) -> None:
        with self.assertRaisesRegex(ValueError, "at least one output"):
            PublishManifest(
                kind=PublishKind.CACHE,
                project="Portfolio",
                name="Smoke",
                version=1,
                source_host="houdini",
                source_path="shots/smoke.hipnc",
                source_fingerprint=fingerprint_bytes(b"source"),
                outputs=(),
            )


if __name__ == "__main__":
    unittest.main()
