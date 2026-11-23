"""
Unit Tests for Inspection Engine and Reporting.
"""

import unittest
from kisignal_guard.cli import create_demo_board
from kisignal_guard.core.engine import InspectionEngine
from kisignal_guard.core.reporter import ReportGenerator


class TestEngineAndReports(unittest.TestCase):

    def test_engine_execution(self):
        board = create_demo_board()
        engine = InspectionEngine()
        result = engine.run(board)

        self.assertEqual(result.rules_executed, 5)
        self.assertGreater(len(result.violations), 0)
        self.assertLess(result.signal_integrity_score, 100.0)

    def test_rule_toggle(self):
        board = create_demo_board()
        engine = InspectionEngine()
        engine.set_rule_enabled("EMC-001", False)

        result = engine.run(board)
        self.assertEqual(result.rules_executed, 4)
        emc_violations = [v for v in result.violations if v.rule_id == "EMC-001"]
        self.assertEqual(len(emc_violations), 0)

    def test_report_generation(self):
        board = create_demo_board()
        engine = InspectionEngine()
        result = engine.run(board)

        json_out = ReportGenerator.to_json(result)
        self.assertIn('"signal_integrity_score":', json_out)
        self.assertIn('"violations":', json_out)

        md_out = ReportGenerator.to_markdown(result)
        self.assertIn("# KiSignal-Guard Verification Report", md_out)
        self.assertIn("## Detailed Violations", md_out)

        html_out = ReportGenerator.to_html(result)
        self.assertIn("<!DOCTYPE html>", html_out)
        self.assertIn("KiSignal-Guard SI & EMC Audit", html_out)


if __name__ == "__main__":
    unittest.main()
