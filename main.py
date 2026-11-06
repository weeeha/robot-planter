"""Robot Planter main loop. Concept scaffold, never run on hardware.

    python main.py --config config/config.yaml [--once]
"""
from __future__ import annotations

import argparse
import json
import time
from datetime import datetime

import yaml

from brain.docking import Docker
from brain.geofence import Geofence, Pose
from brain.scheduler import HOME, SLEEP, STAY, Scheduler
from firmware.motors import Drive
from firmware.sensors import Sensors


def go_to(drive: Drive, pose: Pose, fence: Geofence, target, obstacle) -> None:
    turn, dist = fence.bearing_to(pose, *target)
    drive.turn(turn)
    pose.heading += turn
    covered = drive.forward(dist, stop_if=obstacle)
    dl = dr = covered
    pose.advance(dl, dr, drive.track)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config/config.yaml")
    ap.add_argument("--once", action="store_true")
    args = ap.parse_args()
    cfg = yaml.safe_load(open(args.config))

    sensors, drive = Sensors(cfg), Drive(cfg)
    fence, pose = Geofence(cfg), Pose()
    sched, docker = Scheduler(cfg, fence), Docker(cfg, drive, sensors)
    stop_m = cfg["thresholds"]["obstacle_stop_m"]

    def obstacle() -> bool:
        return sensors.read().obstacle_m < stop_m

    while True:
        r = sensors.read()
        now = datetime.now()
        action = sched.decide(r, pose, now)
        entry = {"ts": now.isoformat(timespec="seconds"), "lux": round(r.lux),
                 "moisture": round(r.moisture, 2), "battery_pct": round(r.battery_pct),
                 "pose": [round(pose.x, 2), round(pose.y, 2)],
                 "action": action.kind, "reason": action.reason}
        if action.kind not in (SLEEP, STAY):
            go_to(drive, pose, fence, action.target, obstacle)
            if action.kind == HOME and docker.seek():
                pose.reset()
                entry["docked"] = True
        with open(cfg["log_path"], "a") as f:
            f.write(json.dumps(entry) + "\n")
        if args.once:
            break
        time.sleep(cfg["loop_seconds"])


if __name__ == "__main__":
    main()
