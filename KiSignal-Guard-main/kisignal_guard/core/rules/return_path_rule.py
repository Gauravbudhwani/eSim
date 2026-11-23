"""
Return Path Discontinuity & Split-Plane Crossing Analyzer.
High-frequency signal currents return along the path of least impedance directly underneath
the trace on the adjacent reference ground/power plane. Crossing splits or voids forces
the return current to loop around the opening, creating high EMI radiation and signal distortion.
"""

from typing import List, Set
from kisignal_guard.core.models import BoardSnapshot, Violation, Severity, RuleCategory, Point2D
from kisignal_guard.core.rules.base_rule import BaseRule
from kisignal_guard.core.geometry import point_in_polygon, segments_intersect


class ReturnPathRule(BaseRule):
    def __init__(self, enabled: bool = True):
        super().__init__(
            rule_id="EMC-001",
            name="Return Path Discontinuity & Split Plane Crossing",
            category=RuleCategory.RETURN_PATH,
            enabled=enabled
        )
        self.config = {
            "critical_net_keywords": ["CLK", "SPI", "USB", "TX", "RX", "SDA", "SCL", "MISO", "MOSI", "ETH"],
            "sample_divisions": 3
        }

    def check(self, board: BoardSnapshot) -> List[Violation]:
        violations: List[Violation] = []
        if not board.zones:
            return violations

        # Filter ground and power zones that serve as reference planes
        ref_zones = [z for z in board.zones if z.is_ground or z.is_power]
        if not ref_zones:
            return violations

        critical_keywords = [k.upper() for k in self.config.get("critical_net_keywords", [])]

        for track in board.tracks:
            net_upper = track.net_name.upper()
            # Ignore power and ground nets
            if "GND" in net_upper or "VCC" in net_upper or "VDD" in net_upper:
                continue

            is_critical = any(kw in net_upper for kw in critical_keywords)
            
            # Sample points along the track segment
            divisions = self.config.get("sample_divisions", 3)
            sampled_points = []
            for i in range(divisions + 1):
                t = i / float(divisions)
                sx = track.start.x + t * (track.end.x - track.start.x)
                sy = track.start.y + t * (track.end.y - track.start.y)
                sampled_points.append(Point2D(sx, sy))

            # Check coverage over reference planes
            uncovered_points = []
            for pt in sampled_points:
                covered = any(point_in_polygon(pt, z.vertices) for z in ref_zones)
                if not covered:
                    uncovered_points.append(pt)

            if uncovered_points:
                severity = Severity.ERROR if is_critical else Severity.WARNING
                loc = uncovered_points[0]
                rec = (
                    f"Reroute net '{track.net_name}' over a solid, unbroken ground plane or "
                    f"add a stitching capacitor / ground bridge across the plane split."
                )
                violations.append(
                    Violation(
                        rule_id=self.rule_id,
                        rule_name=self.name,
                        category=self.category,
                        severity=severity,
                        message=(
                            f"Track on net '{track.net_name}' crosses a copper void/split plane. "
                            f"{len(uncovered_points)}/{len(sampled_points)} sample points lack reference ground."
                        ),
                        net_name=track.net_name,
                        location=loc,
                        recommendation=rec,
                        metrics={
                            "is_critical": is_critical,
                            "uncovered_samples": len(uncovered_points),
                            "layer": track.layer,
                            "length_mm": round(track.length_mm, 3)
                        }
                    )
                )

        return violations
