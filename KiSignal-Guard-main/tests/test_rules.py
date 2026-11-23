"""
Unit Tests for Individual Electrical & Semantic Verification Rules.
"""

import unittest
from kisignal_guard.core.models import (
    BoardSnapshot,
    TrackSegment,
    PadInfo,
    ViaInfo,
    ZonePolygon,
    Point2D,
    Severity
)
from kisignal_guard.core.rules import (
    ReturnPathRule,
    DecouplingProximityRule,
    CrosstalkRule,
    DiffPairSkewRule,
    ThermalPadRule
)


class TestRules(unittest.TestCase):

    def test_return_path_rule_detects_void_crossing(self):
        rule = ReturnPathRule()
        board = BoardSnapshot(title="Test_Return_Path")

        # Ground plane covers x: 0 to 20 only
        board.zones.append(
            ZonePolygon(
                net_name="GND",
                layer="B.Cu",
                vertices=[Point2D(0, 0), Point2D(20, 0), Point2D(20, 20), Point2D(0, 20)],
                is_ground=True
            )
        )
        # Track extends into uncovered region (x: 10 to 40)
        board.tracks.append(
            TrackSegment(
                start=Point2D(10, 10),
                end=Point2D(40, 10),
                width_mm=0.2,
                layer="F.Cu",
                net_name="CLK_SYS"
            )
        )

        violations = rule.check(board)
        self.assertEqual(len(violations), 1)
        self.assertEqual(violations[0].rule_id, "EMC-001")
        self.assertEqual(violations[0].severity, Severity.ERROR)

    def test_decoupling_rule(self):
        rule = DecouplingProximityRule()
        board = BoardSnapshot(title="Test_Decoupling")

        # IC Power Pin at (10, 10)
        board.pads.append(
            PadInfo(footprint_ref="U1", pad_number="1", net_name="3V3", position=Point2D(10, 10), layer="F.Cu", is_power=True)
        )
        # Decoupling Cap at (20, 10) -> distance is 10mm (> 6.0mm limit)
        board.pads.append(
            PadInfo(footprint_ref="C1", pad_number="1", net_name="3V3", position=Point2D(20, 10), layer="F.Cu", is_power=True)
        )

        violations = rule.check(board)
        self.assertEqual(len(violations), 1)
        self.assertEqual(violations[0].severity, Severity.ERROR)
        self.assertIn("10.00 mm", violations[0].message)

    def test_crosstalk_rule(self):
        rule = CrosstalkRule()
        board = BoardSnapshot(title="Test_Crosstalk")

        # Two 10mm tracks running side-by-side with 0.1mm gap (width=0.3 -> 3W requires gap >= 0.6mm)
        board.tracks.append(
            TrackSegment(start=Point2D(0, 0), end=Point2D(10, 0), width_mm=0.3, layer="F.Cu", net_name="SIG_A")
        )
        board.tracks.append(
            TrackSegment(start=Point2D(0, 0.4), end=Point2D(10, 0.4), width_mm=0.3, layer="F.Cu", net_name="SIG_B")
        )

        violations = rule.check(board)
        self.assertEqual(len(violations), 1)
        self.assertEqual(violations[0].rule_id, "SI-001")

    def test_diff_pair_skew(self):
        rule = DiffPairSkewRule()
        board = BoardSnapshot(title="Test_Diff_Pair")

        board.tracks.append(
            TrackSegment(start=Point2D(0, 0), end=Point2D(20, 0), width_mm=0.2, layer="F.Cu", net_name="D_P")
        )
        board.tracks.append(
            TrackSegment(start=Point2D(0, 1), end=Point2D(18, 1), width_mm=0.2, layer="F.Cu", net_name="D_N")
        )

        violations = rule.check(board)
        self.assertEqual(len(violations), 1)
        self.assertEqual(violations[0].metrics["delta_mm"], 2.0)
        self.assertEqual(violations[0].severity, Severity.ERROR)

    def test_thermal_pad_rule(self):
        rule = ThermalPadRule()
        board = BoardSnapshot(title="Test_Thermal")

        # Power IC with thermal pad and zero vias
        board.pads.append(
            PadInfo(footprint_ref="U1", pad_number="EP", net_name="GND", position=Point2D(50, 50), layer="F.Cu", is_ground=True)
        )

        violations = rule.check(board)
        self.assertEqual(len(violations), 1)
        self.assertEqual(violations[0].severity, Severity.ERROR)
        self.assertIn("0 thermal vias", violations[0].message)


if __name__ == "__main__":
    unittest.main()
