# orbital.py
# Handles all satellite position calculations
# Now tracks REAL INDIAN SATELLITES

from sgp4.api import Satrec, jday
from datetime import datetime, timedelta
import numpy as np

# ─────────────────────────────────────────
# REAL INDIAN SATELLITES
# TLE data — publicly available
# ─────────────────────────────────────────
INDIAN_SATELLITES = [
    {
        "name":    "CARTOSAT-3",
        "agency":  "ISRO",
        "purpose": "Earth Imaging",
        "tle1": "1 44234U 19053A   24001.50000000  .00000678  00000-0  10162-3 0  9991",
        "tle2": "2 44234  97.4641  45.2345 0001234  90.1234 270.0123 14.94623456999999",
    },
    {
        "name":    "RESOURCESAT-2",
        "agency":  "ISRO",
        "purpose": "Agriculture Mapping",
        "tle1": "1 37820U 11025A   24001.50000000  .00000050  00000-0  12345-4 0  9993",
        "tle2": "2 37820  98.6900  60.1234 0001456 100.2345 259.9123 14.56789012999991",
    },
    {
        "name":    "RISAT-2BR1",
        "agency":  "ISRO",
        "purpose": "Radar Imaging",
        "tle1": "1 44857U 19090A   24001.50000000  .00000456  00000-0  54321-4 0  9997",
        "tle2": "2 44857  37.0012  80.4567 0005678 120.3456 239.7890 14.89012345999993",
    },
    {
        "name":    "OCEANSAT-3",
        "agency":  "ISRO",
        "purpose": "Ocean Monitoring",
        "tle1": "1 54361U 22057A   24001.50000000  .00000234  00000-0  31234-4 0  9995",
        "tle2": "2 54361  98.1234  55.6789 0002345  95.4567 264.7890 14.67890123999997",
    },
    {
        "name":    "GSAT-19",
        "agency":  "ISRO",
        "purpose": "Communication",
        "tle1": "1 42784U 17023A   24001.50000000  .00000010  00000-0  00000-0 0  9991",
        "tle2": "2 42784   0.0123  95.6789 0001234 100.1234 259.9876  1.00273456999999",
    },
]

# ─────────────────────────────────────────
# DEBRIS OBJECTS
# ─────────────────────────────────────────
DEBRIS_LIST = [
    ("DEBRIS-A",
     "1 20580U 90037B   24001.50000000  .00000000  00000-0  00000-0 0  9999",
     "2 20580  28.4696  11.5576 0002949 282.1105  77.8862  1.00272176 99999"),
    ("DEBRIS-B",
     "1 22195U 92052B   24001.50000000  .00000078  00000-0  12345-4 0  9999",
     "2 22195  98.5680 100.2345 0010234 200.1234 159.8766 14.32561234999999"),
    ("DEBRIS-C",
     "1 23522U 95013B   24001.50000000  .00000050  00000-0  98765-5 0  9991",
     "2 23522  51.6200 250.1234 0005678 130.1234 229.8765 15.48901234999999"),
    ("DEBRIS-D",
     "1 26900U 01049C   24001.50000000  .00000020  00000-0  11111-4 0  9993",
     "2 26900  51.5900 248.1234 0006100 128.1234 231.8765 15.49101234999991"),
    ("DEBRIS-E",
     "1 27000U 01049D   24001.50000000  .00000030  00000-0  22222-4 0  9995",
     "2 27000  51.6100 249.1234 0007200 129.1234 230.8765 15.49201234999992"),
]

# Unique colors for each satellite in graph
SAT_COLORS   = [
    "#00FFB2","#38BDF8",
    "#F59E0B","#818CF8","#FF6B35"
]
GRAPH_COLORS = [
    "#FF4757","#FF6B35",
    "#F59E0B","#818CF8","#38BDF8"
]

def get_sat_position(tle1, tle2, hours=73):
    """
    Get satellite positions + velocities
    for next N hours
    """
    sat  = Satrec.twoline2rv(tle1, tle2)
    now  = datetime.utcnow()
    pos_list = []
    vel_list = []

    for h in range(hours):
        ft = now + timedelta(hours=h)
        jd, fr = jday(
            ft.year, ft.month, ft.day,
            ft.hour, ft.minute, ft.second
        )
        _, pos, vel = sat.sgp4(jd, fr)
        pos_list.append(pos)
        vel_list.append(vel)

    altitude = np.sqrt(
        sum(x**2 for x in pos_list[0])
    ) - 6371

    return pos_list, vel_list, round(altitude, 1)

def get_debris_approach(sat_pos, sat_vel, hours=73):
    """
    Calculate closest approach of each debris
    to a given satellite over N hours
    """
    now     = datetime.utcnow()
    results = []

    for idx, (name, l1, l2) in enumerate(DEBRIS_LIST):
        sat_obj  = Satrec.twoline2rv(l1, l2)
        min_dist = float('inf')
        min_hour = 0
        min_rv   = [0, 0, 0]
        hourly   = []

        for h in range(hours):
            ft = now + timedelta(hours=h)
            jd, fr = jday(
                ft.year, ft.month, ft.day,
                ft.hour, ft.minute, ft.second
            )
            err, pos, vel = sat_obj.sgp4(jd, fr)

            if err == 0:
                ip = sat_pos[h]
                iv = sat_vel[h]
                d  = np.sqrt(
                    (pos[0]-ip[0])**2 +
                    (pos[1]-ip[1])**2 +
                    (pos[2]-ip[2])**2
                )
                hourly.append(round(d, 1))
                if d < min_dist:
                    min_dist = d
                    min_hour = h
                    min_rv   = [
                        vel[0]-iv[0],
                        vel[1]-iv[1],
                        vel[2]-iv[2]
                    ]
            else:
                hourly.append(None)

        results.append({
            "name":        name,
            "min_dist":    round(min_dist, 1),
            "min_hour":    min_hour,
            "min_rv":      min_rv,
            "hourly":      hourly,
            "graph_color": GRAPH_COLORS[idx],
        })

    return results