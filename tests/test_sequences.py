from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from kairo_pipeline.sequences import FramePattern, scan_sequence


class FramePatternTests(unittest.TestCase):
    def test_hash_and_printf_patterns_have_same_canonical_form(self) -> None:
        hashes = FramePattern.parse("renders/beauty.####.exr")
        printf = FramePattern.parse("renders/beauty.%04d.exr")
        self.assertEqual(hashes, printf)
        self.assertEqual(hashes.canonical(), "renders/beauty.####.exr")
        self.assertEqual(hashes.path_for_frame(12), "renders/beauty.0012.exr")

    def test_negative_frames_preserve_sign(self) -> None:
        pattern = FramePattern.parse("cache/sim.###.bgeo.sc")
        self.assertEqual(pattern.path_for_frame(-2), "cache/sim.-002.bgeo.sc")

    def test_missing_or_ambiguous_tokens_are_rejected(self) -> None:
        for value in (
            "renders/beauty.exr",
            "renders/####/beauty.####.exr",
            "renders/%04d.####.exr",
        ):
            with self.subTest(value=value), self.assertRaises(ValueError):
                FramePattern.parse(value)


class SequenceScanTests(unittest.TestCase):
    def test_scan_reports_existing_missing_and_outside_frames(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            renders = root / "renders"
            renders.mkdir()
            for frame in (0, 1, 3, 4):
                (renders / f"beauty.{frame:04d}.exr").touch()

            result = scan_sequence(
                root,
                FramePattern.parse("renders/beauty.####.exr"),
                1,
                3,
            )

            self.assertEqual(result.existing, (1, 3))
            self.assertEqual(result.missing, (2,))
            self.assertEqual(result.outside_range, (0, 4))
            self.assertFalse(result.complete)

    def test_empty_directory_reports_complete_missing_range(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            result = scan_sequence(
                Path(directory),
                FramePattern.parse("renders/beauty.##.png"),
                1,
                2,
            )
            self.assertEqual(result.missing, (1, 2))

    def test_reverse_range_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            scan_sequence(Path.cwd(), FramePattern.parse("a.##.exr"), 2, 1)


if __name__ == "__main__":
    unittest.main()
