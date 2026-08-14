from __future__ import annotations

import unittest

from kairo_pipeline.diagnostics import (
    Diagnostic,
    DiagnosticBag,
    DiagnosticLocation,
    Severity,
)


class DiagnosticTests(unittest.TestCase):
    def test_round_trip_preserves_navigable_diagnostic(self) -> None:
        diagnostic = Diagnostic(
            code="MESH_UV_MISSING",
            severity=Severity.ERROR,
            message="The mesh has no primary UV set.",
            location=DiagnosticLocation(
                host="blender",
                resource="Assets/Chair.blend",
                object_path="Chair/Seat",
                property_name="uv_layers",
            ),
            suggestion="Create a non-empty UV map before publishing.",
        )

        self.assertEqual(Diagnostic.from_dict(diagnostic.to_dict()), diagnostic)
        self.assertTrue(diagnostic.blocks_publish)

    def test_unknown_fields_are_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "unknown fields"):
            Diagnostic.from_dict(
                {
                    "code": "BAD_FIELD",
                    "severity": "warning",
                    "message": "Unexpected field.",
                    "surprise": True,
                }
            )

    def test_invalid_code_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "diagnostic code"):
            Diagnostic("mesh.bad", Severity.ERROR, "Invalid code.")

    def test_bag_is_sorted_and_reports_blocking_errors(self) -> None:
        bag = DiagnosticBag(
            [
                Diagnostic("Z_WARNING", Severity.WARNING, "Warning."),
                Diagnostic("A_ERROR", Severity.ERROR, "Error."),
                Diagnostic("A_INFO", Severity.INFO, "Info."),
            ]
        )

        self.assertTrue(bag.blocks_publish)
        self.assertEqual(
            [item.code for item in bag],
            ["A_ERROR", "A_INFO", "Z_WARNING"],
        )

    def test_location_requires_a_host(self) -> None:
        with self.assertRaisesRegex(ValueError, "host"):
            DiagnosticLocation(host="")


if __name__ == "__main__":
    unittest.main()
