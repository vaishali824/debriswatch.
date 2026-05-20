import numpy as np
import matplotlib.pyplot as plt
from sgp4.api import Satrec, jday
from datetime import datetime, timedelta

# ─────────────────────────────────
# ISS TLE DATA
# ─────────────────────────────────
iss = Satrec.twoline2rv(
    "1 25544U 98067A   24001.50000000  .00001764  00000-0  40651-4 0  9993",
    "2 25544  51.6416 247.4627 0006703 130.5360 325.0288 15.50026242  9999"
)

# ─────────────────────────────────
# DEBRIS TLE DATA
# ─────────────────────────────────
debris_list = [
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

# ─────────────────────────────────
# TRACK EVERY HOUR FOR 72 HOURS
# ─────────────────────────────────
now = datetime.utcnow()
print("=" * 60)
print("      DEBRISWATCH AI — DAY 3 OUTPUT")
print("      72-HOUR CLOSEST APPROACH FINDER")
print("=" * 60)

all_results   = []   # stores best result per debris
iss_positions = []   # ISS path for plotting

# Loop every hour for 72 hours
for hour in range(73):
    future_time = now + timedelta(hours=hour)
    jd, fr = jday(
        future_time.year, future_time.month,
        future_time.day,  future_time.hour,
        future_time.minute, future_time.second
    )
    _, iss_pos, _ = iss.sgp4(jd, fr)
    iss_positions.append(iss_pos)

# For each debris — find its closest approach hour
print("\n  CLOSEST APPROACH IN NEXT 72 HOURS:")
print("-" * 60)

debris_results = []

for name, l1, l2 in debris_list:
    sat = Satrec.twoline2rv(l1, l2)

    min_dist     = float('inf')
    min_hour     = 0
    min_pos      = None
    hourly_dists = []

    for hour in range(73):
        future_time = now + timedelta(hours=hour)
        jd, fr = jday(
            future_time.year, future_time.month,
            future_time.day,  future_time.hour,
            future_time.minute, future_time.second
        )

        error, pos, vel = sat.sgp4(jd, fr)
        if error == 0:
            iss_pos = iss_positions[hour]
            dist = np.sqrt(
                (pos[0] - iss_pos[0])**2 +
                (pos[1] - iss_pos[1])**2 +
                (pos[2] - iss_pos[2])**2
            )
            hourly_dists.append(dist)

            # Track minimum distance
            if dist < min_dist:
                min_dist = dist
                min_hour = hour
                min_pos  = pos
        else:
            hourly_dists.append(None)

    # Risk level at closest approach
    if min_dist < 100:
        risk  = "🔴 HIGH RISK"
        color = "red"
    elif min_dist < 500:
        risk  = "🟡 MONITOR"
        color = "orange"
    else:
        risk  = "🟢 SAFE"
        color = "lime"

    debris_results.append({
        "name":         name,
        "min_dist":     min_dist,
        "min_hour":     min_hour,
        "min_pos":      min_pos,
        "hourly_dists": hourly_dists,
        "risk":         risk,
        "color":        color,
    })

    print(f"  {name}")
    print(f"    Closest approach : {min_dist:.1f} km")
    print(f"    Time             : T+{min_hour}h from now")
    print(f"    Risk level       : {risk}")
    print()

# Sort by closest approach distance
debris_results.sort(key=lambda x: x["min_dist"])

print("-" * 60)
print(f"  ⚠️  BIGGEST THREAT : {debris_results[0]['name']}")
print(f"      Distance       : {debris_results[0]['min_dist']:.1f} km")
print(f"      Time to threat : {debris_results[0]['min_hour']} hours from now")
print(f"      Risk           : {debris_results[0]['risk']}")
print("=" * 60)

# ─────────────────────────────────
# PLOT 1 — Distance over 72 hours
# ─────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(16, 7))
fig.patch.set_facecolor('#0D1117')

ax1 = axes[0]
ax1.set_facecolor('#161B22')

hours = list(range(73))
for d in debris_results:
    dists = [x for x in d["hourly_dists"] if x is not None]
    hrs   = [i for i, x in enumerate(d["hourly_dists"]) if x is not None]
    ax1.plot(hrs, dists,
             label=f"{d['name']} (min: {d['min_dist']:.0f}km)",
             linewidth=2)
    # Mark closest approach point
    ax1.scatter(d["min_hour"], d["min_dist"],
                s=120, zorder=5)
    ax1.annotate(f"  T+{d['min_hour']}h\n  {d['min_dist']:.0f}km",
                 (d["min_hour"], d["min_dist"]),
                 color="white", fontsize=7)

# Danger zone line
ax1.axhline(y=100, color='red', linestyle='--',
            linewidth=1.5, label='Danger Zone (100km)')
ax1.axhline(y=500, color='orange', linestyle='--',
            linewidth=1, label='Monitor Zone (500km)')

ax1.set_xlabel('Hours from Now', color='white', fontsize=10)
ax1.set_ylabel('Distance from ISS (km)', color='white', fontsize=10)
ax1.set_title('Debris Distance from ISS — Next 72 Hours',
              color='white', fontsize=11, fontweight='bold')
ax1.tick_params(colors='gray')
ax1.legend(fontsize=7, facecolor='#0D1117', labelcolor='white')
ax1.grid(alpha=0.2, color='gray')

# ─────────────────────────────────
# PLOT 2 — 3D positions at closest
# ─────────────────────────────────
ax2 = fig.add_subplot(122, projection='3d')
ax2.set_facecolor('#161B22')

# Earth
u = np.linspace(0, 2*np.pi, 40)
v = np.linspace(0, np.pi, 20)
ex = 6371 * np.outer(np.cos(u), np.sin(v))
ey = 6371 * np.outer(np.sin(u), np.sin(v))
ez = 6371 * np.outer(np.ones(np.size(u)), np.cos(v))
ax2.plot_surface(ex, ey, ez, color='steelblue',
                 alpha=0.2, linewidth=0)

# ISS orbit path
iss_arr = np.array(iss_positions)
ax2.plot(iss_arr[:,0], iss_arr[:,1], iss_arr[:,2],
         color='lime', linewidth=1.5,
         alpha=0.6, label='ISS Orbit Path')

# ISS current position
ax2.scatter(*iss_positions[0],
            color='lime', s=200, zorder=10,
            label='ISS Now')

# Debris closest approach positions
for d in debris_results:
    if d["min_pos"]:
        ax2.scatter(*d["min_pos"],
                    color=d["color"], s=150, zorder=9)
        ax2.text(d["min_pos"][0]+300,
                 d["min_pos"][1]+300,
                 d["min_pos"][2]+300,
                 f"{d['name']}\n{d['min_dist']:.0f}km @ T+{d['min_hour']}h",
                 color=d["color"], fontsize=7)

ax2.set_title('Closest Approach Positions (72h)',
              color='white', fontsize=10, fontweight='bold')
ax2.tick_params(colors='gray', labelsize=6)
ax2.xaxis.pane.fill = False
ax2.yaxis.pane.fill = False
ax2.zaxis.pane.fill = False
ax2.legend(fontsize=7, facecolor='#0D1117', labelcolor='white')

plt.suptitle('DebrisWatch AI — 72 Hour Threat Analysis',
             color='white', fontsize=13,
             fontweight='bold', y=1.01)
plt.tight_layout()
plt.savefig('day3_72hour_analysis.png', dpi=150,
            facecolor='#0D1117')
print("\n  Saved → day3_72hour_analysis.png")
print("  Day 3 COMPLETE ✅")
print("\n  Tomorrow Day 4 → Connect REAL Space-Track")
print("  data + build alert system")
plt.show()