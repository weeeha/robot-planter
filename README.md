# Robot Planter

A plant pot on wheels. It lives outside in one patch of the yard, sits still most of the day like
any pot, and walks around occasionally, maybe at night when nobody is looking. It finds the sun
when it wants it, rolls back to its dock to charge, and the only sign it moves is that it is
never quite where you left it.

## What is here

| Folder | What |
|---|---|
| `brain/` | decision loop: when to move, where, when to go charge |
| `firmware/` | motor, sensor and power drivers for the parts in the wiring table |
| `config/` | geofence, quiet hours, thresholds, dock beacon |
| `docs/` | wiring, parts list; printed-part STLs live in the case study repo |
| `main.py` | the ten-minute loop, writes `log.jsonl` |

## Wiring

| Part | Pin / bus | Notes |
|---|---|---|
| DFRobot TB6612FNG motor HAT | I2C `0x10` | channels M1+M2 paralleled left, M3+M4 right |
| Wheel encoders (2) | GPIO 17, 27 | one per side, rising edge |
| HC-SR04 ultrasonic | trig GPIO 23, echo GPIO 24 | echo through a 1k/2k divider to 3.3 V |
| Capacitive soil moisture | ADS1115 A0, I2C `0x48` | analog, 3.3 V supply |
| DFRobot ambient light | I2C `0x23` | lux, under the clear dome behind the pot |
| Pack voltage | ADS1115 A1 | 3S LiPo through a 1:4 divider |
| Dock beacon LED | photodiode on ADS1115 A2 | 2 Hz blink, seen from the rear of the shell |
| Dock contacts | pack charge port | balance charger behind the ramp |

## Run

```bash
pip install -r requirements.txt
python main.py --config config/config.yaml
```

## Status

Planned build; the code has not run on hardware yet. Plan and visuals: https://vyhouski.com/projects/robot-planter
