"""
Power Distribution Network (PDN) Decoupling Proximity & Parasitic Inductance Analyzer.
Evaluates physical distance between IC power pins and their nearest bypass capacitors.
Excessive trace distance introduces parasitic loop inductance (~0.8 nH/mm), causing
ground bounce and power rail voltage droop during high-speed transistor switching.
"""

from typing import List, Dict
import math
from kisignal_guard.core.models import BoardSnapshot, Violation, Severity, RuleCategory, PadInfo
from kisignal_guard.core.rules.base_rule import BaseRule


class DecouplingProximityRule(BaseRule):
    def __init__(self, enabled: bool = True):
        super().__init__(
            rule_id="PDN-001",
            name="Decoupling Capacitor Proximity & Loop Inductance",
            category=RuleCategory.DECOUPLING,
            enabled=enabled
        )
        self.config = {
            "max_warning_distance_mm": 3.5,
            "max_error_distance_mm": 6.0,
            "inductance_per_mm_nH": 0.85
        }

    def check(self, board: BoardSnapshot) -> List[Violation]:
        violations: List[Violation] = []

        # Identify IC footprints (U*, IC*)
        ic_power_pads: List[PadInfo] = []
        cap_power_pads: List[PadInfo] = []

        for pad in board.pads:
            ref = pad.footprint_ref.upper()
            net = pad.net_name.upper()

            # Identify if this is a power rail (e.g. 3V3, 5V, VCC, VDD)
            is_pwr = pad.is_power or any(p in net for p in ["VCC", "VDD", "3V3", "5V", "+3.3V", "+5V", "VIO"])
            if not is_pwr:
                continue

            if ref.startswith("U") or ref.startswith("IC"):
                ic_power_pads.append(pad)
            elif ref.startswith("C"):
                cap_power_pads.append(pad)

        if not ic_power_pads:
            return violations

        max_warn = self.config.get("max_warning_distance_mm", 3.5)
        max_err = self.config.get("max_error_distance_mm", 6.0)
        l_per_mm = self.config.get("inductance_per_mm_nH", 0.85)

        for ic_pad in ic_power_pads:
            # Find matching capacitors on the same power net
            candidates = [c for c in cap_power_pads if c.net_name == ic_pad.net_name]
            if not candidates:
                # No bypass capacitor on this net at all!
                violations.append(
                    Violation(
                        rule_id=self.rule_id,
                        rule_name=self.name,
                        category=self.category,
                        severity=Severity.ERROR,
                        message=(
                            f"IC '{ic_pad.footprint_ref}' Pin {ic_pad.pad_number} on power net "
                            f"'{ic_pad.net_name}' has NO dedicated decoupling capacitor on the board."
                        ),
                        net_name=ic_pad.net_name,
                        location=ic_pad.position,
                        recommendation=(
                            f"Add a 100nF ceramic decoupling capacitor immediately adjacent to "
                            f"{ic_pad.footprint_ref} Pin {ic_pad.pad_number}."
                        ),
                        metrics={"distance_mm": float("inf"), "inductance_nH": float("inf")}
                    )
                )
                continue

            # Find closest capacitor
            closest_cap = min(candidates, key=lambda c: ic_pad.position.distance_to(c.position))
            dist_mm = ic_pad.position.distance_to(closest_cap.position)
            est_inductance_nH = 2.0 * dist_mm * l_per_mm  # 2x for power and ground loop

            if dist_mm > max_err:
                violations.append(
                    Violation(
                        rule_id=self.rule_id,
                        rule_name=self.name,
                        category=self.category,
                        severity=Severity.ERROR,
                        message=(
                            f"Decoupling cap {closest_cap.footprint_ref} is {dist_mm:.2f} mm away from "
                            f"{ic_pad.footprint_ref} pin {ic_pad.pad_number} (Exceeds {max_err} mm limit). "
                            f"Estimated parasitic loop inductance: ~{est_inductance_nH:.1f} nH."
                        ),
                        net_name=ic_pad.net_name,
                        location=ic_pad.position,
                        recommendation=(
                            f"Move capacitor {closest_cap.footprint_ref} closer (< {max_warn} mm) to "
                            f"{ic_pad.footprint_ref} pin {ic_pad.pad_number} to minimize PDN impedance."
                        ),
                        metrics={"distance_mm": round(dist_mm, 2), "inductance_nH": round(est_inductance_nH, 1)}
                    )
                )
            elif dist_mm > max_warn:
                violations.append(
                    Violation(
                        rule_id=self.rule_id,
                        rule_name=self.name,
                        category=self.category,
                        severity=Severity.WARNING,
                        message=(
                            f"Decoupling cap {closest_cap.footprint_ref} is {dist_mm:.2f} mm from "
                            f"{ic_pad.footprint_ref} pin {ic_pad.pad_number}. "
                            f"Parasitic loop inductance: ~{est_inductance_nH:.1f} nH."
                        ),
                        net_name=ic_pad.net_name,
                        location=ic_pad.position,
                        recommendation=(
                            f"Consider placing {closest_cap.footprint_ref} within {max_warn} mm of the power pin."
                        ),
                        metrics={"distance_mm": round(dist_mm, 2), "inductance_nH": round(est_inductance_nH, 1)}
                    )
                )

        return violations
