# Wiring

Power: 3S LiPo (11.1 V nominal) to the motor HAT's VM. A 5 V 3 A buck (not in the parts list
yet) feeds the Pi 5. Sensors run from the Pi's 3.3 V rail except the HC-SR04, which takes 5 V
and needs a divider on echo.

| Part | Connection | Notes |
|---|---|---|
| DFRobot TB6612FNG HAT | sits on the Pi header, I2C `0x10` | M1+M2 left pair, M3+M4 right pair |
| Dagu gearmotors x4 | HAT M1..M4 | 48:1, 65 mm wheels |
| Encoders x2 | GPIO 17 (L), GPIO 27 (R) | hall or slot, one edge per tick, 48/rev |
| HC-SR04 | trig GPIO 23, echo GPIO 24 via 1k/2k | front of the shell, under the pot lip |
| ADS1115 | I2C `0x48`, 3.3 V | A0 moisture, A1 pack voltage (1:4 divider), A2 beacon photodiode |
| Capacitive moisture v2 | ADS A0 | probe in the pot soil through the cradle |
| DFRobot ambient light | I2C `0x23` | top of the mast, under the rain hood |
| Beacon photodiode | ADS A2 | rear of shell, points at the dock LED |
| Dock | spring contacts to the pack's charge lead; LED on 2 Hz blink | balance charger on the house side |

Open: the 5 V buck for the Pi, a pack fuse, and a hard power switch under the shell lip.
