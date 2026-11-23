"""
Domain models for KiSignal-Guard.
Independent of KiCad pcbnew types to ensure portability, mockability, and clean architecture.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any, Optional, Tuple


class Severity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class RuleCategory(str, Enum):
    RETURN_PATH = "Return Path & EMC"
    DECOUPLING = "PDN & Decoupling"
    CROSSTALK = "Crosstalk & Isolation"
    DIFF_PAIR = "Differential Pair"
    THERMAL = "Thermal Dissipation"


@dataclass(frozen=True)
class Point2D:
    x: float  # In millimeters
    y: float  # In millimeters

    def distance_to(self, other: "Point2D") -> float:
        import math
        return math.hypot(self.x - other.x, self.y - other.y)

    def to_tuple(self) -> Tuple[float, float]:
        return (self.x, self.y)


@dataclass
class TrackSegment:
    start: Point2D
    end: Point2D
    width_mm: float
    layer: str
    net_name: str

    @property
    def length_mm(self) -> float:
        return self.start.distance_to(self.end)

    @property
    def midpoint(self) -> Point2D:
        return Point2D(
            (self.start.x + self.end.x) / 2.0,
            (self.start.y + self.end.y) / 2.0
        )


@dataclass
class PadInfo:
    footprint_ref: str
    pad_number: str
    net_name: str
    position: Point2D
    layer: str
    is_power: bool = False
    is_ground: bool = False


@dataclass
class ViaInfo:
    position: Point2D
    drill_mm: float
    pad_diameter_mm: float
    net_name: str
    is_ground: bool = False


@dataclass
class ZonePolygon:
    net_name: str
    layer: str
    vertices: List[Point2D]
    is_ground: bool = False
    is_power: bool = False


@dataclass
class BoardSnapshot:
    """A clean, decoupled abstraction of the KiCad PCB."""
    title: str = "Untitled Board"
    tracks: List[TrackSegment] = field(default_factory=list)
    pads: List[PadInfo] = field(default_factory=list)
    vias: List[ViaInfo] = field(default_factory=list)
    zones: List[ZonePolygon] = field(default_factory=list)
    layers: List[str] = field(default_factory=list)


@dataclass
class Violation:
    rule_id: str
    rule_name: str
    category: RuleCategory
    severity: Severity
    message: str
    net_name: str
    location: Point2D
    recommendation: str
    metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class InspectionResult:
    board_title: str
    violations: List[Violation] = field(default_factory=list)
    rules_executed: int = 0
    execution_time_ms: float = 0.0

    @property
    def error_count(self) -> int:
        return sum(1 for v in self.violations if v.severity == Severity.ERROR)

    @property
    def warning_count(self) -> int:
        return sum(1 for v in self.violations if v.severity == Severity.WARNING)

    @property
    def info_count(self) -> int:
        return sum(1 for v in self.violations if v.severity == Severity.INFO)

    @property
    def signal_integrity_score(self) -> float:
        """
        Calculates a normalised PCB Signal Integrity Score (0 - 100%).
        Errors penalize 15 points, Warnings penalize 5 points, Info penalizes 1 point.
        """
        penalty = (self.error_count * 15.0) + (self.warning_count * 5.0) + (self.info_count * 1.0)
        return max(0.0, min(100.0, 100.0 - penalty))
