"""Differential drive through the DFRobot TB6612FNG motor HAT (I2C 0x10).

The HAT has four channels at 1.2 A each; the chassis
has four 48:1 gearmotors. Channels M1+M2 feed the left pair, M3+M4 the right, so each side gets
two channels in parallel and the per-channel current stays inside the rating.
"""
from __future__ import annotations

import math
import time

try:
    from gpiozero import Button
    from smbus2 import SMBus
except ImportError:
    Button = SMBus = None

REG_MODE = 0x00
REG_SPEED = {1: 0x02, 2: 0x04, 3: 0x06, 4: 0x08}   # 16-bit duty, 0..65535
REG_DIR = {1: 0x03, 2: 0x05, 3: 0x07, 4: 0x09}     # 0 stop, 1 cw, 2 ccw
LEFT, RIGHT = (1, 2), (3, 4)


class Drive:
    def __init__(self, cfg: dict) -> None:
        d, pins = cfg["drive"], cfg["pins"]
        self.addr = cfg["i2c"]["motor_hat"]
        self.wheel_c = math.pi * d["wheel_diameter_m"]
        self.track = d["track_width_m"]
        self.tpr = d["encoder_ticks_per_rev"]
        self.cruise = d["cruise_speed"]
        self._sim = SMBus is None
        self.ticks = {"l": 0, "r": 0}
        if self._sim:
            return
        self.bus = SMBus(1)
        self.bus.write_byte_data(self.addr, REG_MODE, 0x01)  # DC motor mode
        self.enc_l = Button(pins["encoder_left"], pull_up=True)
        self.enc_r = Button(pins["encoder_right"], pull_up=True)
        self.enc_l.when_pressed = lambda: self._tick("l")
        self.enc_r.when_pressed = lambda: self._tick("r")

    # --- low level -------------------------------------------------------
    def _tick(self, side: str) -> None:
        self.ticks[side] += 1

    def _set(self, channels: tuple[int, int], speed: float) -> None:
        """speed in -1..1 for one side."""
        duty = int(min(1.0, abs(speed)) * 65535)
        direction = 0 if duty == 0 else (1 if speed > 0 else 2)
        if self._sim:
            return
        for ch in channels:
            self.bus.write_word_data(self.addr, REG_SPEED[ch], duty)
            self.bus.write_byte_data(self.addr, REG_DIR[ch], direction)

    def stop(self) -> None:
        self._set(LEFT, 0.0)
        self._set(RIGHT, 0.0)

    # --- odometry --------------------------------------------------------
    def pop_distance(self) -> tuple[float, float]:
        """Metres travelled per side since the last call."""
        dl = self.ticks["l"] / self.tpr * self.wheel_c
        dr = self.ticks["r"] / self.tpr * self.wheel_c
        self.ticks = {"l": 0, "r": 0}
        return dl, dr

    # --- moves -----------------------------------------------------------
    def forward(self, metres: float, speed: float | None = None,
                stop_if=lambda: False) -> float:
        """Drive straight; returns metres actually covered (stops early on `stop_if`)."""
        s = speed or self.cruise
        self.pop_distance()
        self._set(LEFT, s)
        self._set(RIGHT, s)
        covered = 0.0
        t0 = time.time()
        while covered < metres and time.time() - t0 < 30:
            if stop_if():
                break
            time.sleep(0.05)
            dl, dr = self.pop_distance()
            covered += (dl + dr) / 2
            if self._sim:
                covered += s * 0.05 * 0.4   # pretend ~0.1 m/s at cruise
        self.stop()
        return covered

    def turn(self, radians: float) -> None:
        """Spin in place. Positive is counter-clockwise."""
        arc = abs(radians) * self.track / 2
        sign = 1 if radians > 0 else -1
        self.pop_distance()
        self._set(LEFT, -sign * self.cruise)
        self._set(RIGHT, sign * self.cruise)
        done = 0.0
        t0 = time.time()
        while done < arc and time.time() - t0 < 10:
            time.sleep(0.05)
            dl, dr = self.pop_distance()
            done += (abs(dl) + abs(dr)) / 2
            if self._sim:
                done += 0.01
        self.stop()
