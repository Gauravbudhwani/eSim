"""
Unit Tests for Computational Geometry Algorithms.
"""

import unittest
from kisignal_guard.core.models import Point2D
from kisignal_guard.core.geometry import (
    point_in_polygon,
    segments_intersect,
    point_to_segment_distance,
    segment_to_segment_distance,
    are_segments_parallel,
    parallel_overlap_length
)


class TestGeometry(unittest.TestCase):

    def test_point_in_polygon(self):
        # A 10x10 square from (0,0) to (10,10)
        poly = [Point2D(0, 0), Point2D(10, 0), Point2D(10, 10), Point2D(0, 10)]

        self.assertTrue(point_in_polygon(Point2D(5, 5), poly))
        self.assertTrue(point_in_polygon(Point2D(1, 1), poly))
        self.assertFalse(point_in_polygon(Point2D(15, 5), poly))
        self.assertFalse(point_in_polygon(Point2D(-2, 5), poly))

    def test_segments_intersect(self):
        # Crossing segments
        p1, q1 = Point2D(0, 0), Point2D(10, 10)
        p2, q2 = Point2D(0, 10), Point2D(10, 0)
        self.assertTrue(segments_intersect(p1, q1, p2, q2))

        # Parallel non-intersecting
        p3, q3 = Point2D(0, 2), Point2D(10, 2)
        p4, q4 = Point2D(0, 5), Point2D(10, 5)
        self.assertFalse(segments_intersect(p3, q3, p4, q4))

    def test_are_segments_parallel(self):
        p1, q1 = Point2D(0, 0), Point2D(10, 0)
        p2, q2 = Point2D(2, 5), Point2D(12, 5)
        self.assertTrue(are_segments_parallel(p1, q1, p2, q2))

        # Perpendicular
        p3, q3 = Point2D(0, 0), Point2D(0, 10)
        self.assertFalse(are_segments_parallel(p1, q1, p3, q3))

    def test_parallel_overlap_length(self):
        # Segment 1: from x=0 to x=10
        p1, q1 = Point2D(0, 0), Point2D(10, 0)
        # Segment 2: from x=4 to x=12 (overlap is from 4 to 10 -> length = 6)
        p2, q2 = Point2D(4, 2), Point2D(12, 2)
        overlap = parallel_overlap_length(p1, q1, p2, q2)
        self.assertAlmostEqual(overlap, 6.0, places=2)

    def test_segment_to_segment_distance(self):
        # Two parallel horizontal segments at y=0 and y=3
        p1, q1 = Point2D(0, 0), Point2D(10, 0)
        p2, q2 = Point2D(0, 3), Point2D(10, 3)
        dist = segment_to_segment_distance(p1, q1, p2, q2)
        self.assertAlmostEqual(dist, 3.0, places=3)


if __name__ == "__main__":
    unittest.main()
