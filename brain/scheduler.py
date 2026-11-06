"""The decision loop. A short rule list, not a model. Concept scaffold, untested.

Every ten minutes the loop takes a reading and asks each rule in order. The first rule that
returns an action wins. Most of the time the answer is SLEEP.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from datetime import datetime, time as dtime
from typing import Callable

from firmware.sensors import Reading
from brain.geofence import Geofence, Pose

SLEEP, STAY, HOME, SUN, WANDER = "sleep", "stay", "home", "sun", "wander"


@dataclass
class Action:
    kind: str
    target: tuple[float, float] | None = None
    reason: str = ""


@dataclass
class Memory:
    """What yesterday taught us: the brightest spot seen per hour."""
    best_lux_by_hour: dict[int, tuple[float, float, float]] = field(default_factory=dict)
    last_moisture: float | None = None

    def remember(self, hour: int, lux: float, pose: Pose) -> None:
        cur = self.best_lux_by_hour.get(hour)
        if cur is None or lux > cur[0]:
            self.best_lux_by_hour[hour] = (lux, pose.x, pose.y)


def _between(now: dtime, start: str, end: str) -> bool:
    s = dtime.fromisoformat(start)
    e = dtime.fromisoformat(end)
    return s <= now <= e if s <= e else (now >= s or now <= e)


class Scheduler:
    def __init__(self, cfg: dict, fence: Geofence, mem: Memory | None = None) -> None:
        self.cfg = cfg
        self.t = cfg["thresholds"]
        self.fence = fence
        self.mem = mem or Memory()
        self.rules: list[Callable[[Reading, Pose, datetime], Action | None]] = [
            self.rule_battery, self.rule_rain, self.rule_sun, self.rule_wander,
        ]

    def decide(self, r: Reading, pose: Pose, now: datetime) -> Action:
        self.mem.remember(now.hour, r.lux, pose)
        for rule in self.rules:
            a = rule(r, pose, now)
            if a:
                return a
        return Action(SLEEP, reason="nothing to do")

    # --- rules, in priority order -----------------------------------------
    def rule_battery(self, r, pose, now):
        if r.battery_pct < self.t["battery_home_pct"]:
            return Action(HOME, (0.0, 0.0), f"battery {r.battery_pct:.0f}%")

    def rule_rain(self, r, pose, now):
        last = self.mem.last_moisture
        self.mem.last_moisture = r.moisture
        if last is not None and r.moisture - last > self.t["moisture_rain_jump"]:
            return Action(STAY, reason="rain, stay put")

    def rule_sun(self, r, pose, now):
        a, b = self.t["midday"]
        if not _between(now.time(), a, b) or r.lux >= self.t["low_light_lux"]:
            return None
        best = self.mem.best_lux_by_hour.get(now.hour)
        if best and best[0] > r.lux * 1.5:
            return Action(SUN, self.fence.clamp_target(best[1], best[2]),
                          f"{r.lux:.0f} lux here, {best[0]:.0f} remembered")

    def rule_wander(self, r, pose, now):
        q = self.cfg["quiet_hours"]
        if not _between(now.time(), q["start"], q["end"]):
            return None
        if random.random() > 0.3:          # most quiet-hour checks do nothing
            return None
        reach = self.cfg["drive"]["wander_max_m"]
        tx = pose.x + random.uniform(-reach, reach)
        ty = pose.y + random.uniform(-reach, reach)
        return Action(WANDER, self.fence.clamp_target(tx, ty), "quiet hour, nobody looking")
