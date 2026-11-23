"""
Computational Geometry Module for PCB Semantic Analysis.
Implements 2D intersection, point-in-polygon ray casting, parallel segment overlap,
and spatial distance metrics without requiring external C++ geometry dependencies.
"""

import math
from typing import List, Tuple, Optional
from kisignal_guard.core.models import Point2D


def point_in_polygon(point: Point2D, polygon: List[Point2D]) -> bool:
    """
    Ray-casting algorithm (Even-odd rule / Jordan curve theorem)
    Returns True if point is inside the polygon, False otherwise.
    """
    if len(polygon) < 3:
        return False

    inside = False
    x, y = point.x, point.y
    n = len(polygon)

    for i in range(n):
        p1 = polygon[i]
        p2 = polygon[(i + 1) % n]

        # Check if point is on horizontal ray crossing segment
        if (p1.y > y) != (p2.y > y):
            # Compute x-coordinate of intersection
            x_inters = (p2.x - p1.x) * (y - p1.y) / (p2.y - p1.y + 1e-12) + p1.x
            if x < x_inters:
                inside = not inside

    return inside


def orientation(p: Point2D, q: Point2D, r: Point2D) -> int:
    """
    Finds orientation of ordered triplet (p, q, r).
    0 -> Collinear
    1 -> Clockwise
    2 -> Counterclockwise
    """
    val = (q.y - p.y) * (r.x - q.x) - (q.x - p.x) * (r.y - q.y)
    if abs(val) < 1e-9:
        return 0
    return 1 if val > 0 else 2


def on_segment(p: Point2D, q: Point2D, r: Point2D) -> bool:
    """Checks if point q lies on line segment pr."""
    return (
        min(p.x, r.x) - 1e-9 <= q.x <= max(p.x, r.x) + 1e-9 and
        min(p.y, r.y) - 1e-9 <= q.y <= max(p.y, r.y) + 1e-9
    )


def segments_intersect(p1: Point2D, q1: Point2D, p2: Point2D, q2: Point2D) -> bool:
    """Returns True if line segment 'p1q1' and 'p2q2' intersect."""
    o1 = orientation(p1, q1, p2)
    o2 = orientation(p1, q1, q2)
    o3 = orientation(p2, q2, p1)
    o4 = orientation(p2, q2, q1)

    # General case
    if o1 != o2 and o3 != o4:
        return True

    # Special collinear cases
    if o1 == 0 and on_segment(p1, p2, q1):
        return True
    if o2 == 0 and on_segment(p1, q2, q1):
        return True
    if o3 == 0 and on_segment(p2, p1, q2):
        return True
    if o4 == 0 and on_segment(p2, q1, q2):
        return True

    return False


def point_to_segment_distance(pt: Point2D, a: Point2D, b: Point2D) -> float:
    """Calculates perpendicular or clamped distance from point pt to segment ab."""
    ab_dx = b.x - a.x
    ab_dy = b.y - a.y
    ab_len_sq = ab_dx * ab_dx + ab_dy * ab_dy

    if ab_len_sq < 1e-12:
        return pt.distance_to(a)

    # Project point onto segment: t = dot(pt - a, ab) / |ab|^2
    t = ((pt.x - a.x) * ab_dx + (pt.y - a.y) * ab_dy) / ab_len_sq
    t = max(0.0, min(1.0, t))

    proj_x = a.x + t * ab_dx
    proj_y = a.y + t * ab_dy
    return pt.distance_to(Point2D(proj_x, proj_y))


def segment_to_segment_distance(p1: Point2D, q1: Point2D, p2: Point2D, q2: Point2D) -> float:
    """Computes minimum Euclidean distance between two 2D line segments."""
    if segments_intersect(p1, q1, p2, q2):
        return 0.0

    d1 = point_to_segment_distance(p1, p2, q2)
    d2 = point_to_segment_distance(q1, p2, q2)
    d3 = point_to_segment_distance(p2, p1, q1)
    d4 = point_to_segment_distance(q2, p1, q1)

    return min(d1, d2, d3, d4)


def are_segments_parallel(
    p1: Point2D, q1: Point2D, p2: Point2D, q2: Point2D, tolerance_deg: float = 7.5
) -> bool:
    """Checks whether two segments are approximately parallel."""
    dx1, dy1 = q1.x - p1.x, q1.y - p1.y
    dx2, dy2 = q2.x - p2.x, q2.y - p2.y

    len1 = math.hypot(dx1, dy1)
    len2 = math.hypot(dx2, dy2)

    if len1 < 1e-6 or len2 < 1e-6:
        return False

    # Cosine of angle between direction vectors
    dot = (dx1 * dx2 + dy1 * dy2) / (len1 * len2)
    dot = max(-1.0, min(1.0, dot))
    angle = math.degrees(math.acos(abs(dot)))

    return angle <= tolerance_deg


def parallel_overlap_length(p1: Point2D, q1: Point2D, p2: Point2D, q2: Point2D) -> float:
    """
    Calculates the overlapping length of segment 2 projected onto segment 1.
    Essential for determining parallel trace coupling / crosstalk hazard length.
    """
    dx = q1.x - p1.x
    dy = q1.y - p1.y
    len1 = math.hypot(dx, dy)
    if len1 < 1e-6:
        return 0.0

    ux, uy = dx / len1, dy / len1

    # Project endpoints of segment 2 onto the line along segment 1
    t_start = (p2.x - p1.x) * ux + (p2.y - p1.y) * uy
    t_end = (q2.x - p1.x) * ux + (q2.y - p1.y) * uy

    min_proj = min(t_start, t_end)
    max_proj = max(t_start, t_end)

    # Overlap with [0, len1]
    overlap_start = max(0.0, min_proj)
    overlap_end = min(len1, max_proj)

    return max(0.0, overlap_end - overlap_start)
