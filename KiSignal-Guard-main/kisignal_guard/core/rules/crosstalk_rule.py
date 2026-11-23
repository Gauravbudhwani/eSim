"""
Crosstalk & 3W Rule Compliance Analyzer.
Identifies long parallel trace runs on the same layer that violate the high-speed 3W rule
(center-to-center spacing >= 3 * trace width, or edge-to-edge gap >= 2 * trace width).
Excessive parallel coupling length induces near-end crosstalk (NEXT) and far-end crosstalk (FEXT).
"""

from typing import List
from kisignal_guard.core.models import BoardSnapshot, Violation, Severity, RuleCategory, Point2D
from kisignal_guard.core.rules.base_rule import BaseRule
from kisignal_guard.core.geometry import (
    are_segments_parallel,
    segment_to_segment_distance,
    parallel_overlap_length
)


class CrosstalkRule(BaseRule):
    def __init__(self, enabled: bool = True):
        super().__init__(
            rule_id="SI-001",
            name="Crosstalk & 3W Rule Compliance",
            category=RuleCategory.CROSSTALK,
            enabled=enabled
        )
        self.config = {
            "min_parallel_length_mm": 4.0,     # Ignore short incidental parallel segments
            "spacing_multiplier": 2.0,         # Edge-to-edge gap must be >= 2 * width
            "critical_coupling_length_mm": 12.0
        }

    def check(self, board: BoardSnapshot) -> List[Violation]:
        violations: List[Violation] = []
        tracks = board.tracks
        num_tracks = len(tracks)

        min_len = self.config.get("min_parallel_length_mm", 4.0)
        multiplier = self.config.get("spacing_multiplier", 2.0)
        crit_len = self.config.get("critical_coupling_length_mm", 12.0)

        checked_pairs = set()

        for i in range(num_tracks):
            t1 = tracks[i]
            # Ignore very short segments
            if t1.length_mm < min_len:
                continue

            for j in range(i + 1, num_tracks):
                t2 = tracks[j]
                # Only check same layer, different nets
                if t1.layer != t2.layer or t1.net_name == t2.net_name:
                    continue

                # Don't check between ground and ground or power nets
                if ("GND" in t1.net_name.upper() and "GND" in t2.net_name.upper()):
                    continue

                if t2.length_mm < min_len:
                    continue

                # Check if parallel
                if not are_segments_parallel(t1.start, t1.end, t2.start, t2.end):
                    continue

                # Calculate parallel overlap length
                overlap = parallel_overlap_length(t1.start, t1.end, t2.start, t2.end)
                if overlap < min_len:
                    continue

                # Compute actual edge-to-edge distance
                center_dist = segment_to_segment_distance(t1.start, t1.end, t2.start, t2.end)
                edge_dist = center_dist - (t1.width_mm / 2.0 + t2.width_mm / 2.0)

                required_gap = max(t1.width_mm, t2.width_mm) * multiplier

                if edge_dist < required_gap:
                    pair_key = tuple(sorted([f"{t1.net_name}_{t1.start.to_tuple()}", f"{t2.net_name}_{t2.start.to_tuple()}"]))
                    if pair_key in checked_pairs:
                        continue
                    checked_pairs.add(pair_key)

                    severity = Severity.ERROR if overlap >= crit_len else Severity.WARNING
                    midpoint = Point2D(
                        (t1.midpoint.x + t2.midpoint.x) / 2.0,
                        (t1.midpoint.y + t2.midpoint.y) / 2.0
                    )

                    violations.append(
                        Violation(
                            rule_id=self.rule_id,
                            rule_name=self.name,
                            category=self.category,
                            severity=severity,
                            message=(
                                f"Crosstalk hazard between nets '{t1.net_name}' and '{t2.net_name}'. "
                                f"Parallel coupling run is {overlap:.2f} mm with spacing {edge_dist:.2f} mm "
                                f"(Violates 3W rule: required gap >= {required_gap:.2f} mm)."
                            ),
                            net_name=f"{t1.net_name} <-> {t2.net_name}",
                            location=midpoint,
                            recommendation=(
                                f"Increase spacing between '{t1.net_name}' and '{t2.net_name}' to at least "
                                f"{required_gap:.2f} mm or interpose an in-between ground shield trace."
                            ),
                            metrics={
                                "coupling_length_mm": round(overlap, 2),
                                "actual_gap_mm": round(edge_dist, 2),
                                "required_gap_mm": round(required_gap, 2),
                                "layer": t1.layer
                            }
                        )
                    )

        return violations
