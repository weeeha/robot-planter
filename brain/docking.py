"""Find the dock and back onto it.

The dock has a 2 Hz LED beacon. A photodiode on the rear of the shell feeds ADS1115 A2. The
robot turns until the blink is strongest, then reverses slowly until the pack voltage shows
the charger (a jump of more than 0.3 V), which means the contacts met.
"""
from __future__ import annotations

import math
import time

from firmware.motors import Drive
from firmware.sensors import Sensors


class Docker:
    def __init__(self, cfg: dict, drive: Drive, sensors: Sensors) -> None:
        self.cfg = cfg["dock"]
        self.drive = drive
        self.sensors = sensors

    def beacon_strength(self) -> float:
        """Amplitude of the 2 Hz component over one second of samples."""
        if self.sensors._sim:
            return 0.5
        samples = []
        t0 = time.time()
        while time.time() - t0 < 1.0:
            samples.append(self.sensors.adc_a2())  # provided by Sensors in a later pass
            time.sleep(0.02)
        return max(samples) - min(samples)

    def seek(self) -> bool:
        """Rotate to face away from the beacon, reverse until charging. True on contact."""
        best, best_at = -1.0, 0.0
        for i in range(12):                    # 12 x 30 degrees
            s = self.beacon_strength()
            if s > best:
                best, best_at = s, i * math.pi / 6
            self.drive.turn(math.pi / 6)
        self.drive.turn(best_at)                # rear now faces the dock
        v0 = self.sensors.read().battery_v
        t0 = time.time()
        while time.time() - t0 < self.cfg["seek_timeout_s"]:
            self.drive.forward(0.10, speed=-self.cfg["approach_speed"])
            if self.sensors.read().battery_v - v0 > 0.3:
                self.drive.stop()
                return True
            if self.sensors._sim:
                return True
        self.drive.stop()
        return False
