from __future__ import annotations

import unittest

import kairo_pipeline
from kairo_pipeline.cli import main


class PackageTests(unittest.TestCase):
    def test_public_version_is_available(self) -> None:
        self.assertEqual(kairo_pipeline.__version__, "0.1.0")

    def test_empty_cli_invocation_succeeds(self) -> None:
        self.assertEqual(main([]), 0)


if __name__ == "__main__":
    unittest.main()
