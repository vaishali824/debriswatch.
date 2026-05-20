from flask import Flask, render_template, jsonify
from sgp4.api import Satrec, jday
from datetime import datetime, timedelta
import numpy as np

app = Flask(__name__)

ISS_TLE1 = "1 25544U 98067A   24001.50000000  .00001764  00000-0  40651-4 0  9993"
ISS_TLE2 = "2 25544  51.6416 247.4627 0006703 130.5360 325.0288 15.50026242  9999"

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

GRAPH_COLORS = ["#FF4757","#FF6B35","#F59E0B","#818CF8","#38BDF8"]

def get_risk(score):
    if score >= 80:   return "CRITICAL","#FF4757"
    elif score >= 60: return "HIGH","#FF6B35"
    elif score >= 40: return "MEDIUM","#F59E0B"
    elif score >= 20: return "LOW","#34D399"
    else:             return "MINIMAL","#00FFB2"

def score_debris(min_dist, min_hour, rel_vel):
    if min_dist < 100:    ds = 40
    elif min_dist < 500:  ds = 35
    elif min_dist < 1000: ds = 28
    elif min_dist < 3000: ds = 18
    elif min_dist < 5000: ds = 10
    elif min_dist < 8000: ds = 5
    else:                 ds = 2
    if min_hour < 6:      ts = 25
    elif min_hour < 12:   ts = 20
    elif min_hour < 24:   ts = 15
    elif min_hour < 48:   ts = 8
    else:                 ts = 3
    spd = np.sqrt(sum(v**2 for v in rel_vel))
    if spd > 14:   vs = 20
    elif spd > 10: vs = 15
    elif spd > 7:  vs = 10
    elif spd > 3:  vs = 6
    else:          vs = 2
    if min_dist < 1000:   os = 15
    elif min_dist < 3000: os = 10
    elif min_dist < 6000: os = 5
    else:                 os = 1
    return min(ds + ts + vs + os, 100)

def analyse():
    iss = Satrec.twoline2rv(ISS_TLE1, ISS_TLE2)
    now = datetime.utcnow()
    iss_pos_list = []
    iss_vel_list = []
    for h in range(73):
        ft = now + timedelta(hours=h)
        jd, fr = jday(ft.year, ft.month, ft.day,
                      ft.hour, ft.minute, ft.second)
        _, pos, vel = iss.sgp4(jd, fr)
        iss_pos_list.append(pos)
        iss_vel_list.append(vel)
    iss_alt = round(np.sqrt(sum(
        x**2 for x in iss_pos_list[0])) - 6371, 1)
    results = []
    for idx,(name,l1,l2) in enumerate(DEBRIS_LIST):
        sat = Satrec.twoline2rv(l1, l2)
        min_dist = float('inf')
        min_hour = 0
        min_rv   = [0,0,0]
        hourly   = []
        for h in range(73):
            ft = now + timedelta(hours=h)
            jd, fr = jday(ft.year,ft.month,ft.day,
                          ft.hour,ft.minute,ft.second)
            err,pos,vel = sat.sgp4(jd, fr)
            if err == 0:
                ip = iss_pos_list[h]
                iv = iss_vel_list[h]
                d  = np.sqrt(
                    (pos[0]-ip[0])**2+
                    (pos[1]-ip[1])**2+
                    (pos[2]-ip[2])**2)
                hourly.append(round(d,1))
                if d < min_dist:
                    min_dist = d
                    min_hour = h
                    min_rv   = [vel[0]-iv[0],
                                vel[1]-iv[1],
                                vel[2]-iv[2]]
            else:
                hourly.append(None)
        sc         = score_debris(min_dist,min_hour,min_rv)
        label,rcol = get_risk(sc)
        results.append({
            "name":       name,
            "score":      sc,
            "label":      label,
            "risk_color": rcol,
            "graph_color":GRAPH_COLORS[idx],
            "min_dist":   round(min_dist,1),
            "min_hour":   min_hour,
            "hourly":     hourly,
        })
    results.sort(key=lambda x:x["score"],reverse=True)
    return {
        "iss_alt":   iss_alt,
        "generated": now.strftime("%Y-%m-%d %H:%M UTC"),
        "debris":    results,
        "high":      sum(1 for r in results if r["label"] in ["CRITICAL","HIGH"]),
        "medium":    sum(1 for r in results if r["label"]=="MEDIUM"),
        "safe":      sum(1 for r in results if r["label"] in ["LOW","MINIMAL"]),
        "total":     len(results),
    }

@app.route("/")
def index():
    return render_template("dashboard.html", data=analyse())

@app.route("/api/data")
def api():
    return jsonify(analyse())

if __name__ == "__main__":
    print("\n  DebrisWatch AI running!")
    print("  Open browser: http://127.0.0.1:5000\n")
    app.run(debug=True)