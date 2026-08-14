from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from kairo_pipeline.fingerprint import Fingerprint, fingerprint_bytes, fingerprint_file
from kairo_pipeline.paths import casefold_path_key, normalize_project_path, resolve_project_path


class PathTests(unittest.TestCase):
    def test_normalize_removes_redundant_components(self) -> None:
        self.assertEqual(
            normalize_project_path("Assets//Props/./Chair.gltf"),
            "Assets/Props/Chair.gltf",
        )

    def test_casefold_key_detects_cross_platform_collision(self) -> None:
        self.assertEqual(
            casefold_path_key("Textures/Wood.PNG"),
            casefold_path_key("textures/wood.png"),
        )

    def test_unsafe_paths_are_rejected(self) -> None:
        unsafe = (
            "",
            "/tmp/file",
            "../outside",
            "assets/../../outside",
            "C:/temp/file",
            "assets\\file",
            "asset:/file",
        )
        for value in unsafe:
            with self.subTest(value=value), self.assertRaises(ValueError):
                normalize_project_path(value)

    def test_resolve_stays_inside_project_root(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            resolved = resolve_project_path(root, "Assets/Chair.gltf")
            self.assertEqual(
                resolved,
                root.resolve() / "Assets" / "Chair.gltf",
            )


class FingerprintTests(unittest.TestCase):
    def test_bytes_and_file_fingerprints_match(self) -> None:
        payload = b"kairo-pipeline\x00fixture"
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "fixture.bin"
            source.write_bytes(payload)
            self.assertEqual(fingerprint_file(source), fingerprint_bytes(payload))

    def test_fingerprint_round_trip_is_strict(self) -> None:
        fingerprint = fingerprint_bytes(b"asset")
        self.assertEqual(Fingerprint.from_dict(fingerprint.to_dict()), fingerprint)
        with self.assertRaises(ValueError):
            Fingerprint.from_dict({**fingerprint.to_dict(), "extra": True})

    def test_missing_file_is_rejected(self) -> None:
        with self.assertRaises(FileNotFoundError):
            fingerprint_file(Path("does-not-exist"))


if __name__ == "__main__":
    unittest.main()
