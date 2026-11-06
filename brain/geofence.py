"""Dead-reckoned pose and a square geofence. Concept scaffold, untested.

The dock is the origin, facing +y. Pose updates from per-side wheel distances. Drift is
expected; the dock seek re-zeroes the pose every time it charges.
"""
from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass
class Pose:
    x: float = 0.0
    y: float = 0.0
    heading: float = math.pi / 2   # radians, +y is "away from the dock"

    def advance(self, dl: float, dr: float, track: float) -> None:
        d = (dl + dr) / 2
        self.heading += (dr - dl) / track
        self.x += d * math.cos(self.heading)
        self.y += d * math.sin(self.heading)

    def reset(self) -> None:
        self.x, self.y, self.heading = 0.0, 0.0, math.pi / 2


class Geofence:
    def __init__(self, cfg: dict) -> None:
        g = cfg["geofence"]
        self.min_x, self.max_x = g["min_x"], g["max_x"]
        self.min_y, self.max_y = g["min_y"], g["max_y"]

    def inside(self, x: float, y: float, margin: float = 0.2) -> bool:
        return (self.min_x + margin <= x <= self.max_x - margin
                and self.min_y + margin <= y <= self.max_y - margin)

    def clamp_target(self, x: float, y: float) -> tuple[float, float]:
        return (min(max(x, self.min_x + 0.3), self.max_x - 0.3),
                min(max(y, self.min_y + 0.3), self.max_y - 0.3))

    @staticmethod
    def bearing_to(pose: Pose, x: float, y: float) -> tuple[float, float]:
        """(turn radians, distance metres) from pose to a point."""
        dx, dy = x - pose.x, y - pose.y
        want = math.atan2(dy, dx)
        turn = (want - pose.heading + math.pi) % (2 * math.pi) - math.pi
        return turn, math.hypot(dx, dy)
