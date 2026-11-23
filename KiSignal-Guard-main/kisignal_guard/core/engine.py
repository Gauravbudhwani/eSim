"""
Inspection Engine for KiSignal-Guard.
Orchestrates rule execution, collects violations, and computes overall PCB integrity scoring.
"""

import time
from typing import List, Dict, Type, Optional
from kisignal_guard.core.models import BoardSnapshot, InspectionResult, Violation
from kisignal_guard.core.rules import (
    BaseRule,
    ReturnPathRule,
    DecouplingProximityRule,
    CrosstalkRule,
    DiffPairSkewRule,
    ThermalPadRule
)


class InspectionEngine:
    """Core verification engine."""

    def __init__(self):
        self.rules: Dict[str, BaseRule] = {}
        self._register_default_rules()

    def _register_default_rules(self) -> None:
        default_rules = [
            ReturnPathRule(enabled=True),
            DecouplingProximityRule(enabled=True),
            CrosstalkRule(enabled=True),
            DiffPairSkewRule(enabled=True),
            ThermalPadRule(enabled=True)
        ]
        for rule in default_rules:
            self.register_rule(rule)

    def register_rule(self, rule: BaseRule) -> None:
        self.rules[rule.rule_id] = rule

    def set_rule_enabled(self, rule_id: str, enabled: bool) -> None:
        if rule_id in self.rules:
            self.rules[rule_id].enabled = enabled

    def run(self, board: BoardSnapshot) -> InspectionResult:
        """Runs all enabled rules sequentially and returns aggregated results."""
        start_time = time.perf_counter()
        all_violations: List[Violation] = []
        rules_run = 0

        for rule in self.rules.values():
            if rule.enabled:
                rules_run += 1
                try:
                    found = rule.check(board)
                    all_violations.extend(found)
                except Exception as e:
                    # Defensive programming: ensure one rule error doesn't crash the entire audit
                    import logging
                    logging.getLogger("kisignal_guard").exception(f"Error in rule {rule.rule_id}: {e}")

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        return InspectionResult(
            board_title=board.title,
            violations=all_violations,
            rules_executed=rules_run,
            execution_time_ms=round(elapsed_ms, 2)
        )
