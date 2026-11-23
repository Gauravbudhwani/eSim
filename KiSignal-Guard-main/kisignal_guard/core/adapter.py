"""
KiCad pcbnew Adapter Module.
Translates live KiCad 9 C++ pcbnew objects into decoupled Python domain models (BoardSnapshot).
Handles KiCad unit conversions (internal nanometers <-> millimeters) cleanly.
"""

import math
from typing import Optional
from kisignal_guard.core.models import (
    BoardSnapshot,
    TrackSegment,
    PadInfo,
    ViaInfo,
    ZonePolygon,
    Point2D
)

# Nanometer conversion factor (KiCad 7, 8, and 9 use nanometers internally: 1 mm = 1,000,000 nm)
NM_TO_MM = 1e-6


class PcbnewAdapter:
    """Adapts KiCad pcbnew Board object into a BoardSnapshot domain model."""

    @staticmethod
    def is_kicad_available() -> bool:
        try:
            import pcbnew
            return True
        except ImportError:
            return False

    @classmethod
    def load_from_pcbnew(cls, board=None) -> BoardSnapshot:
        """
        Extracts PCB elements from the active pcbnew board into a clean BoardSnapshot.
        If board is None, attempts to fetch pcbnew.GetBoard().
        """
        try:
            import pcbnew
        except ImportError:
            raise RuntimeError("pcbnew module is not available in the current Python environment.")

        if board is None:
            board = pcbnew.GetBoard()

        if board is None:
            raise ValueError("No active board found in KiCad PCB editor.")

        title = board.GetFileName() or "Active KiCad 9 Board"
        snapshot = BoardSnapshot(title=title)

        # 1. Extract Tracks and Vias
        tracks = board.GetTracks()
        for t in tracks:
            # Check if this item is a Via
            if hasattr(pcbnew, "PCB_VIA") and isinstance(t, pcbnew.PCB_VIA):
                pos = Point2D(t.GetPosition().x * NM_TO_MM, t.GetPosition().y * NM_TO_MM)
                drill_mm = t.GetDrill() * NM_TO_MM
                width_mm = t.GetWidth() * NM_TO_MM
                net_name = t.GetNetname()
                is_gnd = "GND" in net_name.upper()
                snapshot.vias.append(
                    ViaInfo(position=pos, drill_mm=drill_mm, pad_diameter_mm=width_mm, net_name=net_name, is_ground=is_gnd)
                )
            else:
                # Regular track segment
                start_pt = Point2D(t.GetStart().x * NM_TO_MM, t.GetStart().y * NM_TO_MM)
                end_pt = Point2D(t.GetEnd().x * NM_TO_MM, t.GetEnd().y * NM_TO_MM)
                width_mm = t.GetWidth() * NM_TO_MM
                layer_name = board.GetLayerName(t.GetLayer())
                net_name = t.GetNetname()

                snapshot.tracks.append(
                    TrackSegment(
                        start=start_pt,
                        end=end_pt,
                        width_mm=width_mm,
                        layer=layer_name,
                        net_name=net_name
                    )
                )

        # 2. Extract Footprints & Pads
        footprints = board.GetFootprints()
        for fp in footprints:
            ref = fp.GetReference()
            for pad in fp.Pads():
                pos = Point2D(pad.GetPosition().x * NM_TO_MM, pad.GetPosition().y * NM_TO_MM)
                net_name = pad.GetNetname()
                pad_num = pad.GetNumber()
                layer_name = board.GetLayerName(pad.GetLayer())

                net_upper = net_name.upper()
                is_pwr = any(p in net_upper for p in ["VCC", "VDD", "3V3", "5V", "+3.3V", "+5V", "VBUS", "VIO"])
                is_gnd = "GND" in net_upper

                snapshot.pads.append(
                    PadInfo(
                        footprint_ref=ref,
                        pad_number=pad_num,
                        net_name=net_name,
                        position=pos,
                        layer=layer_name,
                        is_power=is_pwr,
                        is_ground=is_gnd
                    )
                )

        # 3. Extract Copper Zones
        zones = board.Zones()
        for zone in zones:
            net_name = zone.GetNetname()
            net_upper = net_name.upper()
            is_gnd = "GND" in net_upper
            is_pwr = any(p in net_upper for p in ["VCC", "VDD", "3V3", "5V", "PWR"])

            # Extract filled polygon outline
            poly_set = zone.GetFilledPolysList(zone.GetLayer())
            layer_name = board.GetLayerName(zone.GetLayer())

            for i in range(poly_set.OutlineCount()):
                outline = poly_set.Outline(i)
                pts: list[Point2D] = []
                for j in range(outline.PointCount()):
                    pt = outline.Point(j)
                    pts.append(Point2D(pt.x * NM_TO_MM, pt.y * NM_TO_MM))

                if pts:
                    snapshot.zones.append(
                        ZonePolygon(
                            net_name=net_name,
                            layer=layer_name,
                            vertices=pts,
                            is_ground=is_gnd,
                            is_power=is_pwr
                        )
                    )

        return snapshot
