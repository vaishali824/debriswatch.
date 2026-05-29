# orbital.py
# Now uses auto-fetched TLE data
# from NASA Space-Track

from sgp4.api import Satrec, jday
from datetime import datetime, timedelta
import numpy as np

SAT_COLORS = [
    "#00FFB2", "#38BDF8",
    "#F59E0B", "#818CF8", "#FF6B35"
]
GRAPH_COLORS = [
    "#FF4757", "#FF6B35",
    "#F59E0B", "#818CF8", "#38BDF8"
]

SAT_PURPOSES = {
    "CARTOSAT-3":    "Earth Imaging",
    "RESOURCESAT-2": "Agriculture Mapping",
    "RISAT-2BR1":    "Radar Imaging",
    "OCEANSAT-3":    "Ocean Monitoring",
    "GSAT-19":       "Communication",
}

def get_sat_position(tle1, tle2, hours=73):
    sat      = Satrec.twoline2rv(tle1, tle2)
    now      = datetime.utcnow()
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

def get_debris_approach(
    sat_pos, sat_vel, debris_list, hours=73
):
    now     = datetime.utcnow()
    results = []
    for idx, (name, l1, l2) in \
            enumerate(debris_list):
        try:
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
                err, pos, vel = sat_obj.sgp4(
                    jd, fr
                )
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
                "graph_color": GRAPH_COLORS[
                    idx % len(GRAPH_COLORS)
                ],
            })
        except:
            pass
    return results