"""Sensor reads for the Robot Planter. Concept scaffold, never run on hardware.

Light: DFRobot ambient light sensor over I2C (lux).
Soil moisture: capacitive probe into an ADS1115 ADC, channel A0.
Pack voltage: 3S LiPo through a 1:4 divider into ADS1115 A1.
Obstacle: HC-SR04 ultrasonic on two GPIOs.
"""
from __future__ import annotations

import time
from dataclasses import dataclass

try:
    import board
    import busio
    from adafruit_ads1x15.ads1115 import ADS1115
    from adafruit_ads1x15.analog_in import AnalogIn
    from gpiozero import DistanceSensor
    from smbus2 import SMBus
except ImportError:  # desk run without the Pi stack
    board = busio = ADS1115 = AnalogIn = DistanceSensor = SMBus = None


@dataclass
class Reading:
    lux: float
    moisture: float        # 0 dry .. 1 wet, from the probe's calibrated span
    battery_v: float
    battery_pct: float
    obstacle_m: float
    ts: float


class Sensors:
    """One object per robot. `read()` is called once per loop."""

    MOISTURE_DRY = 2.80   # volts in air
    MOISTURE_WET = 1.25   # volts in water
    PACK_EMPTY_V = 10.5   # 3S, under load
    PACK_FULL_V = 12.6

    def __init__(self, cfg: dict) -> None:
        self.cfg = cfg
        pins, i2c = cfg["pins"], cfg["i2c"]
        self._sim = SMBus is None
        if self._sim:
            return
        self.bus = SMBus(1)
        self.light_addr = i2c["light"]
        adc_bus = busio.I2C(board.SCL, board.SDA)
        self.adc = ADS1115(adc_bus, address=i2c["adc"])
        self.ch_moist = AnalogIn(self.adc, 0)
        self.ch_batt = AnalogIn(self.adc, 1)
        self.sonar = DistanceSensor(
            echo=pins["sonar_echo"], trigger=pins["sonar_trig"], max_distance=4.0
        )

    def read(self) -> Reading:
        if self._sim:
            return Reading(lux=1500.0, moisture=0.4, battery_v=11.8,
                           battery_pct=62.0, obstacle_m=1.0, ts=time.time())
        v_batt = self.ch_batt.voltage * 4.0
        pct = 100.0 * (v_batt - self.PACK_EMPTY_V) / (self.PACK_FULL_V - self.PACK_EMPTY_V)
        v_m = self.ch_moist.voltage
        moist = (self.MOISTURE_DRY - v_m) / (self.MOISTURE_DRY - self.MOISTURE_WET)
        return Reading(
            lux=self._read_lux(),
            moisture=max(0.0, min(1.0, moist)),
            battery_v=v_batt,
            battery_pct=max(0.0, min(100.0, pct)),
            obstacle_m=self.sonar.distance,
            ts=time.time(),
        )

    def _read_lux(self) -> float:
        # DFRobot SEN0097-style: two bytes, big endian, lux = raw / 1.2
        hi, lo = self.bus.read_i2c_block_data(self.light_addr, 0x10, 2)
        return ((hi << 8) | lo) / 1.2
