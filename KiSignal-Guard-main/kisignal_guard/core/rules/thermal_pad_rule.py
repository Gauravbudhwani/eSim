"""
Thermal Via & Ground Pad Dissipation Analyzer.
High-power ICs (QFN, DFN, PowerSOIC, Regulators) generate significant heat.
An exposed thermal pad (EPAD) must be stitched with an array of thermal vias
to conduct heat to inner and bottom ground planes. Lack of thermal vias causes
die thermal throttling and premature component failure.
"""

from typing import List
from kisignal_guard.core.models import BoardSnapshot, Violation, Severity, RuleCategory, Point2D
from kisignal_guard.core.rules.base_rule import BaseRule


class ThermalPadRule(BaseRule):
    def __init__(self, enabled: bool = True):
        super().__init__(
            rule_id="TH-001",
            name="Power IC Thermal Via Stitching",
            category=RuleCategory.THERMAL,
            enabled=enabled
        )
        self.config = {
            "min_thermal_vias": 4,
            "search_radius_mm": 2.5
        }

    def check(self, board: BoardSnapshot) -> List[Violation]:
        violations: List[Violation] = []

        # Find power IC exposed pads (identified by ref U/Q and pad labeled EP, EPAD, 0, or ground net)
        thermal_pads = []
        for pad in board.pads:
            ref = pad.footprint_ref.upper()
            pad_num = str(pad.pad_number).upper()
            is_ic = ref.startswith("U") or ref.startswith("Q") or ref.startswith("IC")
            is_thermal_id = "EP" in pad_num or "THERMAL" in pad_num or pad_num in ["0", "9", "49", "65"]
            is_gnd = pad.is_ground or "GND" in pad.net_name.upper()

            if is_ic and (is_thermal_id or (is_gnd and pad_num in ["EP", "PAD", "0"])):
                thermal_pads.append(pad)

        if not thermal_pads:
            return violations

        min_vias = self.config.get("min_thermal_vias", 4)
        radius = self.config.get("search_radius_mm", 2.5)

        for pad in thermal_pads:
            # Count ground vias within search radius of thermal pad
            nearby_vias = [
                v for v in board.vias
                if (v.is_ground or "GND" in v.net_name.upper()) and pad.position.distance_to(v.position) <= radius
            ]

            num_vias = len(nearby_vias)
            if num_vias < min_vias:
                severity = Severity.ERROR if num_vias == 0 else Severity.WARNING
                violations.append(
                    Violation(
                        rule_id=self.rule_id,
                        rule_name=self.name,
                        category=self.category,
                        severity=severity,
                        message=(
                            f"IC '{pad.footprint_ref}' thermal pad (Pad {pad.pad_number}) has only {num_vias} "
                            f"thermal vias within {radius} mm (Minimum required: {min_vias})."
                        ),
                        net_name=pad.net_name,
                        location=pad.position,
                        recommendation=(
                            f"Add a {min_vias}-via grid array (drill 0.3mm) connected to GND under "
                            f"'{pad.footprint_ref}' to ensure adequate heat sinking."
                        ),
                        metrics={
                            "vias_found": num_vias,
                            "min_required": min_vias,
                            "search_radius_mm": radius
                        }
                    )
                )

        return violations
