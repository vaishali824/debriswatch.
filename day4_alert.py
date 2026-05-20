import os
import requests
import numpy as np
import matplotlib.pyplot as plt
from sgp4.api import Satrec, jday
from datetime import datetime, timedelta

# ─────────────────────────────────────────
# SPACE-TRACK LOGIN
# Use your registered email and password
# ─────────────────────────────────────────
USERNAME = "vaishalimuddasani@gmail.com"   # ← replace with your email
PASSWORD = "h1a2r3ekrishna0!!0"          # ← replace with your password

BASE_URL = "https://www.space-track.org"

print("=" * 60)
print("      DEBRISWATCH AI — DAY 4")
print("      REAL DATA + ALERT SYSTEM")
print("=" * 60)

# ─────────────────────────────────────────
# STEP 1 — LOGIN TO SPACE-TRACK
# ─────────────────────────────────────────
print("\n  Connecting to NASA Space-Track...")
session = requests.Session()

login = session.post(
    f"{BASE_URL}/ajaxauth/login",
    data={"identity": USERNAME, "password": PASSWORD}
)

if login.status_code == 200:
    print("  ✅ Login successful!")
else:
    print("  ❌ Login failed. Check your email/password.")
    exit()

# ─────────────────────────────────────────
# STEP 2 — DOWNLOAD REAL DEBRIS TLE DATA
# We download debris objects near ISS orbit
# ISS orbits at ~51.6 degree inclination
# We get debris with similar inclination
# ─────────────────────────────────────────
print("\n  Downloading real debris TLE data...")

url = (
    f"{BASE_URL}/basicspacedata/query"
    f"/class/tle_latest/ORDINAL/1"
    f"/OBJECT_TYPE/DEBRIS"
    f"/INCLINATION/50--53"    # near ISS orbit angle
    f"/EPOCH/%3Enow-1"        # updated in last 1 day
    f"/orderby/EPOCH desc"
    f"/limit/20"              # get 20 debris objects
    f"/format/tle"
)

response = session.get(url)
tle_raw  = response.text.strip().split("\n")

# Parse TLE into pairs
debris_list = []
for i in range(0, len(tle_raw)-1, 2):
    line1 = tle_raw[i].strip()
    line2 = tle_raw[i+1].strip()
    if line1.startswith("1") and line2.startswith("2"):
        name = f"DEBRIS-{i//2 + 1}"
        debris_list.append((name, line1, line2))

print(f"  ✅ Downloaded {len(debris_list)} real debris objects!")
print(f"     All updated within last 24 hours from NASA")

# ─────────────────────────────────────────
# ISS TLE — also from Space-Track
# ─────────────────────────────────────────
print("\n  Downloading ISS TLE...")
iss_url = (
    f"{BASE_URL}/basicspacedata/query"
    f"/class/tle_latest/ORDINAL/1"
    f"/NORAD_CAT_ID/25544"
    f"/format/tle"
)
iss_response = session.get(iss_url).text.strip()
print(f"  ISS Response: {iss_response[:100]}")  # debug line

iss_raw = [line.strip() for line in iss_response.split("\n") 
           if line.strip()]

if len(iss_raw) >= 2:
    iss = Satrec.twoline2rv(iss_raw[0], iss_raw[1])
    print("  ✅ ISS TLE downloaded — latest data!")
else:
    print("  ⚠️  ISS TLE from Space-Track failed — using backup")
    iss = Satrec.twoline2rv(
        "1 25544U 98067A   24001.50000000  .00001764  00000-0  40651-4 0  9993",
        "2 25544  51.6416 247.4627 0006703 130.5360 325.0288 15.50026242  9999"
    )
    print("  ✅ ISS backup TLE loaded!")
# Logout
session.get(f"{BASE_URL}/ajaxauth/logout")

# ─────────────────────────────────────────
# STEP 3 — 72 HOUR CLOSEST APPROACH
# (same logic as Day 3 — now with real data)
# ─────────────────────────────────────────
now = datetime.utcnow()
print(f"\n  Scanning {len(debris_list)} debris objects over 72 hours...")
print("-" * 60)

iss_positions = []
for hour in range(73):
    ft = now + timedelta(hours=hour)
    jd, fr = jday(ft.year, ft.month, ft.day,
                  ft.hour, ft.minute, ft.second)
    _, pos, _ = iss.sgp4(jd, fr)
    iss_positions.append(pos)

debris_results = []
for name, l1, l2 in debris_list:
    try:
        sat = Satrec.twoline2rv(l1, l2)
        min_dist = float('inf')
        min_hour = 0
        min_pos  = None
        hourly   = []

        for hour in range(73):
            ft = now + timedelta(hours=hour)
            jd, fr = jday(ft.year, ft.month, ft.day,
                          ft.hour, ft.minute, ft.second)
            err, pos, _ = sat.sgp4(jd, fr)
            if err == 0:
                ip = iss_positions[hour]
                d  = np.sqrt(
                    (pos[0]-ip[0])**2 +
                    (pos[1]-ip[1])**2 +
                    (pos[2]-ip[2])**2
                )
                hourly.append(d)
                if d < min_dist:
                    min_dist = d
                    min_hour = hour
                    min_pos  = pos
            else:
                hourly.append(None)

        if min_dist < 100:
            risk  = "RED — HIGH RISK"
            color = "red"
        elif min_dist < 500:
            risk  = "YELLOW — MONITOR"
            color = "orange"
        else:
            risk  = "GREEN — SAFE"
            color = "lime"

        debris_results.append({
            "name":     name,
            "min_dist": min_dist,
            "min_hour": min_hour,
            "min_pos":  min_pos,
            "hourly":   hourly,
            "risk":     risk,
            "color":    color,
        })
    except:
        pass

debris_results.sort(key=lambda x: x["min_dist"])

# ─────────────────────────────────────────
# STEP 4 — ALERT SYSTEM
# ─────────────────────────────────────────
print("\n  ALERT SYSTEM REPORT:")
print("=" * 60)

high_risk   = [d for d in debris_results if "RED"    in d["risk"]]
monitor     = [d for d in debris_results if "YELLOW" in d["risk"]]
safe        = [d for d in debris_results if "GREEN"  in d["risk"]]

print(f"\n  🔴 HIGH RISK  : {len(high_risk)} objects")
print(f"  🟡 MONITOR    : {len(monitor)} objects")
print(f"  🟢 SAFE       : {len(safe)} objects")

print("\n  TOP THREATS:")
print("-" * 60)
for d in debris_results[:5]:
    print(f"  {d['name']}")
    print(f"    Closest : {d['min_dist']:.1f} km at T+{d['min_hour']}h")
    print(f"    Risk    : {d['risk']}")
    print()

# Alert trigger
print("-" * 60)
if high_risk:
    print(f"\n  🚨 ALERT TRIGGERED!")
    print(f"  {len(high_risk)} object(s) will come within 100km of ISS!")
    print(f"  Closest: {debris_results[0]['name']}")
    print(f"  Distance: {debris_results[0]['min_dist']:.1f} km")
    print(f"  Time: {debris_results[0]['min_hour']} hours from now")
    print(f"\n  ⚡ RECOMMENDED ACTION: Maneuver ISS orbit")
elif monitor:
    print(f"\n  ⚠️  WATCH ALERT!")
    print(f"  {len(monitor)} object(s) within 500km — monitor closely")
else:
    print(f"\n  ✅ ALL CLEAR — No immediate threats detected")

print("=" * 60)

# ─────────────────────────────────────────
# STEP 5 — SAVE ALERT REPORT TO FILE
# ─────────────────────────────────────────
with open("alert_report.txt", "w") as f:
    f.write("DEBRISWATCH AI — ALERT REPORT\n")
    f.write(f"Generated: {now.strftime('%Y-%m-%d %H:%M UTC')}\n")
    f.write("=" * 50 + "\n\n")
    f.write(f"HIGH RISK  : {len(high_risk)} objects\n")
    f.write(f"MONITOR    : {len(monitor)} objects\n")
    f.write(f"SAFE       : {len(safe)} objects\n\n")
    f.write("TOP THREATS:\n")
    for d in debris_results[:5]:
        f.write(f"\n{d['name']}\n")
        f.write(f"  Closest : {d['min_dist']:.1f} km\n")
        f.write(f"  Time    : T+{d['min_hour']}h\n")
        f.write(f"  Risk    : {d['risk']}\n")

print("\n  ✅ Alert report saved → alert_report.txt")

# ─────────────────────────────────────────
# STEP 6 — PLOT
# ─────────────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(16, 7))
fig.patch.set_facecolor('#0D1117')

# Left — distance chart
ax1 = axes[0]
ax1.set_facecolor('#161B22')
for d in debris_results:
    hrs   = [i for i, x in enumerate(d["hourly"]) if x is not None]
    dists = [x for x in d["hourly"] if x is not None]
    ax1.plot(hrs, dists, color=d["color"],
             linewidth=1.5, alpha=0.8,
             label=f"{d['name']} ({d['min_dist']:.0f}km)")
    ax1.scatter(d["min_hour"], d["min_dist"],
                color=d["color"], s=80, zorder=5)

ax1.axhline(y=100, color='red',
            linestyle='--', linewidth=1.5,
            label='Danger (100km)')
ax1.axhline(y=500, color='orange',
            linestyle='--', linewidth=1,
            label='Monitor (500km)')
ax1.set_xlabel('Hours from Now', color='white')
ax1.set_ylabel('Distance from ISS (km)', color='white')
ax1.set_title('Real Debris — 72 Hour Threat Analysis',
              color='white', fontweight='bold')
ax1.tick_params(colors='gray')
ax1.legend(fontsize=7, facecolor='#0D1117',
           labelcolor='white')
ax1.grid(alpha=0.15, color='gray')

# Right — 3D view
ax2 = fig.add_subplot(122, projection='3d')
ax2.set_facecolor('#161B22')

u = np.linspace(0, 2*np.pi, 40)
v = np.linspace(0, np.pi, 20)
ax2.plot_surface(
    6371*np.outer(np.cos(u), np.sin(v)),
    6371*np.outer(np.sin(u), np.sin(v)),
    6371*np.outer(np.ones(np.size(u)), np.cos(v)),
    color='steelblue', alpha=0.2, linewidth=0
)

iss_arr = np.array(iss_positions)
ax2.plot(iss_arr[:,0], iss_arr[:,1], iss_arr[:,2],
         color='lime', linewidth=1.5,
         alpha=0.5, label='ISS Orbit')
ax2.scatter(*iss_positions[0],
            color='lime', s=200, zorder=10,
            label='ISS Now')

for d in debris_results:
    if d["min_pos"]:
        ax2.scatter(*d["min_pos"],
                    color=d["color"], s=100, zorder=9)

ax2.set_title('3D — Closest Approach Positions',
              color='white', fontweight='bold')
ax2.tick_params(colors='gray', labelsize=6)
ax2.xaxis.pane.fill = False
ax2.yaxis.pane.fill = False
ax2.zaxis.pane.fill = False
ax2.legend(fontsize=7, facecolor='#0D1117',
           labelcolor='white')

plt.suptitle(
    'DebrisWatch AI — REAL NASA DATA — 72 Hour Analysis',
    color='white', fontsize=13, fontweight='bold'
)
plt.tight_layout()
plt.savefig('day4_real_data.png', dpi=150,
            facecolor='#0D1117')
print("  Chart saved → day4_real_data.png")
print("\n  Day 4 COMPLETE ✅")
print("  Tomorrow Day 5 → Build Risk Score + Dashboard")
plt.show()