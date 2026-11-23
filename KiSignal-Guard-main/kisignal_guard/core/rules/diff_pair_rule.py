"""
Differential Pair Skew & Length Matching Analyzer.
Differential signaling relies on high common-mode rejection. Length mismatch
between the positive and negative traces introduces phase skew (differential-to-common-mode
conversion), resulting in signal degradation and electromagnetic radiation.
"""

from typing import List, Dict
import re
from kisignal_guard.core.models import BoardSnapshot, Violation, Severity, RuleCategory, Point2D
from kisignal_guard.core.rules.base_rule import BaseRule


class DiffPairSkewRule(BaseRule):
    def __init__(self, enabled: bool = True):
        super().__init__(
            rule_id="SI-002",
            name="Differential Pair Skew & Length Matching",
            category=RuleCategory.DIFF_PAIR,
            enabled=enabled
        )
        self.config = {
            "max_warning_skew_mm": 0.5,     # ~3 ps in FR4
            "max_error_skew_mm": 1.5,       # ~9 ps in FR4
            "prop_delay_ps_per_mm": 6.2     # Typical microstrip propagation delay in FR4
        }

    def check(self, board: BoardSnapshot) -> List[Violation]:
        violations: List[Violation] = []

        # Group track lengths by net
        net_lengths: Dict[str, float] = {}
        net_first_point: Dict[str, Point2D] = {}

        for track in board.tracks:
            net = track.net_name
            net_lengths[net] = net_lengths.get(net, 0.0) + track.length_mm
            if net not in net_first_point:
                net_first_point[net] = track.midpoint

        # Match differential pairs using regex patterns
        # Pattern 1: *_P and *_N
        # Pattern 2: *+ and *-
        pairs = []
        checked_nets = set()

        for net_p in net_lengths:
            if net_p in checked_nets:
                continue

            net_n = None
            if net_p.endswith("_P"):
                candidate = net_p[:-2] + "_N"
                if candidate in net_lengths:
                    net_n = candidate
            elif net_p.endswith("+"):
                candidate = net_p[:-1] + "-"
                if candidate in net_lengths:
                    net_n = candidate

            if net_n:
                pairs.append((net_p, net_n))
                checked_nets.add(net_p)
                checked_nets.add(net_n)

        max_warn = self.config.get("max_warning_skew_mm", 0.5)
        max_err = self.config.get("max_error_skew_mm", 1.5)
        ps_per_mm = self.config.get("prop_delay_ps_per_mm", 6.2)

        for p_net, n_net in pairs:
            len_p = net_lengths[p_net]
            len_n = net_lengths[n_net]
            delta_len = abs(len_p - len_n)
            skew_ps = delta_len * ps_per_mm

            if delta_len > max_err:
                violations.append(
                    Violation(
                        rule_id=self.rule_id,
                        rule_name=self.name,
                        category=self.category,
                        severity=Severity.ERROR,
                        message=(
                            f"Differential pair '{p_net}' / '{n_net}' has severe length mismatch: "
                            f"{len_p:.2f} mm vs {len_n:.2f} mm (Delta: {delta_len:.2f} mm, Skew: ~{skew_ps:.1f} ps)."
                        ),
                        net_name=f"{p_net}/{n_net}",
                        location=net_first_point.get(p_net, Point2D(0, 0)),
                        recommendation=(
                            f"Add serpentine / meander length tuning to the shorter net to balance "
                            f"within {max_warn} mm (< {max_warn * ps_per_mm:.1f} ps)."
                        ),
                        metrics={
                            "len_positive_mm": round(len_p, 2),
                            "len_negative_mm": round(len_n, 2),
                            "delta_mm": round(delta_len, 2),
                            "skew_ps": round(skew_ps, 1)
                        }
                    )
                )
            elif delta_len > max_warn:
                violations.append(
                    Violation(
                        rule_id=self.rule_id,
                        rule_name=self.name,
                        category=self.category,
                        severity=Severity.WARNING,
                        message=(
                            f"Differential pair '{p_net}' / '{n_net}' length difference is {delta_len:.2f} mm "
                            f"(Estimated phase skew: ~{skew_ps:.1f} ps)."
                        ),
                        net_name=f"{p_net}/{n_net}",
                        location=net_first_point.get(p_net, Point2D(0, 0)),
                        recommendation=f"Tune shorter trace length within {max_warn} mm.",
                        metrics={
                            "len_positive_mm": round(len_p, 2),
                            "len_negative_mm": round(len_n, 2),
                            "delta_mm": round(delta_len, 2),
                            "skew_ps": round(skew_ps, 1)
                        }
                    )
                )

        return violations
