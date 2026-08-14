from __future__ import annotations

import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
import json
from pathlib import Path
import tempfile

import kairo_pipeline
from kairo_pipeline.cli import main
from kairo_pipeline.fingerprint import fingerprint_bytes
from kairo_pipeline.manifest import PublishFile, PublishKind, PublishManifest, serialize_manifest


class PackageTests(unittest.TestCase):
    def test_public_version_is_available(self) -> None:
        self.assertEqual(kairo_pipeline.__version__, "0.1.0")

    def test_empty_cli_invocation_succeeds(self) -> None:
        with redirect_stdout(StringIO()):
            self.assertEqual(main([]), 0)

    def test_validate_manifest_emits_machine_readable_result(self) -> None:
        manifest = PublishManifest(
            kind=PublishKind.RENDER,
            project="Portfolio",
            name="FinalComp",
            version=1,
            source_host="nuke",
            source_path="shots/final.nk",
            source_fingerprint=fingerprint_bytes(b"script"),
            outputs=(
                PublishFile(
                    "renders/final.0001.exr",
                    "beauty",
                    fingerprint_bytes(b"frame"),
                    "image/x-exr",
                ),
            ),
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "publish.json"
            path.write_bytes(serialize_manifest(manifest))
            output = StringIO()
            with redirect_stdout(output):
                result = main(["validate-manifest", str(path), "--json"])
            self.assertEqual(result, 0)
            parsed = json.loads(output.getvalue())
            self.assertTrue(parsed["valid"])
            self.assertEqual(parsed["kind"], "render")

    def test_invalid_manifest_returns_controlled_error(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "broken.json"
            path.write_text("not json", encoding="utf-8")
            error = StringIO()
            with redirect_stderr(error):
                result = main(["validate-manifest", str(path)])
            self.assertEqual(result, 2)
            self.assertIn("line 1", error.getvalue())


if __name__ == "__main__":
    unittest.main()
