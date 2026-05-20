import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from sgp4.api import Satrec, jday
from datetime import datetime, timedelta

# ─────────────────────────────────
# ISS TLE
# ─────────────────────────────────
iss = Satrec.twoline2rv(
    "1 25544U 98067A   24001.50000000  .00001764  00000-0  40651-4 0  9993",
    "2 25544  51.6416 247.4627 0006703 130.5360 325.0288 15.50026242  9999"
)

# ─────────────────────────────────
# DEBRIS LIST
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
# GET ISS POSITIONS FOR 72 HOURS
# ─────────────────────────────────
now = datetime.utcnow()
iss_positions = []
iss_velocities = []

for hour in range(73):
    ft = now + timedelta(hours=hour)
    jd, fr = jday(ft.year, ft.month, ft.day,
                  ft.hour, ft.minute, ft.second)
    _, pos, vel = iss.sgp4(jd, fr)
    iss_positions.append(pos)
    iss_velocities.append(vel)

# ─────────────────────────────────
# RISK SCORE ENGINE
# ─────────────────────────────────
def calculate_risk_score(min_dist, closing_speed,
                         min_hour, relative_velocity):
    """
    Calculate risk score out of 100
    based on 4 factors

    Factor 1 - Distance Score (40 points)
    Factor 2 - Closing Speed Score (25 points)
    Factor 3 - Time Urgency Score (20 points)
    Factor 4 - Relative Velocity Score (15 points)
    """

    # ── Factor 1: Distance (40 points) ──────────
    # Closer = more dangerous = higher score
    if min_dist < 10:
        dist_score = 40       # extremely close
    elif min_dist < 50:
        dist_score = 35
    elif min_dist < 100:
        dist_score = 28
    elif min_dist < 300:
        dist_score = 18
    elif min_dist < 500:
        dist_score = 10
    elif min_dist < 1000:
        dist_score = 5
    else:
        dist_score = 0        # safe distance

    # ── Factor 2: Closing Speed (25 points) ─────
    # How fast debris is approaching ISS
    # closing_speed in km/hour
    if closing_speed > 5:
        speed_score = 25      # approaching very fast
    elif closing_speed > 2:
        speed_score = 18
    elif closing_speed > 1:
        speed_score = 10
    elif closing_speed > 0:
        speed_score = 5       # slowly approaching
    else:
        speed_score = 0       # moving away

    # ── Factor 3: Time Urgency (20 points) ──────
    # Sooner the threat = more urgent
    if min_hour < 6:
        time_score = 20       # less than 6 hours!
    elif min_hour < 12:
        time_score = 16
    elif min_hour < 24:
        time_score = 12
    elif min_hour < 48:
        time_score = 6
    else:
        time_score = 2        # far future

    # ── Factor 4: Relative Velocity (15 points) ─
    # Higher relative velocity = more destructive
    # if collision happens
    rel_speed = np.sqrt(sum(v**2 for v in relative_velocity))
    if rel_speed > 14:
        vel_score = 15        # hypervelocity
    elif rel_speed > 10:
        vel_score = 10
    elif rel_speed > 7:
        vel_score = 6
    else:
        vel_score = 2

    # ── Total Score ──────────────────────────────
    total = dist_score + speed_score + time_score + vel_score

    return {
        "total":        total,
        "dist_score":   dist_score,
        "speed_score":  speed_score,
        "time_score":   time_score,
        "vel_score":    vel_score,
    }

def get_risk_label(score):
    if score >= 80:
        return "CRITICAL",  "red"
    elif score >= 60:
        return "HIGH",      "orangered"
    elif score >= 40:
        return "MEDIUM",    "orange"
    elif score >= 20:
        return "LOW",       "yellow"
    else:
        return "MINIMAL",   "lime"

# ─────────────────────────────────
# ANALYSE ALL DEBRIS
# ─────────────────────────────────
print("=" * 60)
print("      DEBRISWATCH AI — DAY 5")
print("      RISK SCORE ENGINE")
print("=" * 60)
print()

results = []

for name, l1, l2 in debris_list:
    sat = Satrec.twoline2rv(l1, l2)

    min_dist     = float('inf')
    min_hour     = 0
    prev_dist    = None
    min_rel_vel  = [0, 0, 0]
    hourly_dists = []

    for hour in range(73):
        ft = now + timedelta(hours=hour)
        jd, fr = jday(ft.year, ft.month, ft.day,
                      ft.hour, ft.minute, ft.second)
        err, pos, vel = sat.sgp4(jd, fr)

        if err == 0:
            ip = iss_positions[hour]
            iv = iss_velocities[hour]
            dist = np.sqrt(
                (pos[0]-ip[0])**2 +
                (pos[1]-ip[1])**2 +
                (pos[2]-ip[2])**2
            )
            hourly_dists.append(dist)

            if dist < min_dist:
                min_dist    = dist
                min_hour    = hour
                # relative velocity = debris vel - ISS vel
                min_rel_vel = [
                    vel[0]-iv[0],
                    vel[1]-iv[1],
                    vel[2]-iv[2]
                ]
        else:
            hourly_dists.append(None)

    # Calculate closing speed
    # (how fast distance changed per hour)
    valid = [d for d in hourly_dists if d is not None]
    if len(valid) >= 2:
        closing_speed = (valid[0] - min_dist) / max(min_hour, 1)
    else:
        closing_speed = 0

    # Get risk score
    scores = calculate_risk_score(
        min_dist, closing_speed,
        min_hour, min_rel_vel
    )
    label, color = get_risk_label(scores["total"])

    results.append({
        "name":          name,
        "min_dist":      min_dist,
        "min_hour":      min_hour,
        "scores":        scores,
        "label":         label,
        "color":         color,
        "hourly_dists":  hourly_dists,
        "closing_speed": closing_speed,
    })

# Sort by risk score
results.sort(key=lambda x: x["scores"]["total"], reverse=True)

# ─────────────────────────────────
# PRINT RESULTS
# ─────────────────────────────────
for r in results:
    s = r["scores"]
    print(f"  {r['name']}")
    print(f"  {'─'*45}")
    print(f"  Risk Score     : {s['total']}/100  →  {r['label']}")
    print(f"  Closest        : {r['min_dist']:.1f} km at T+{r['min_hour']}h")
    print(f"  Distance Score : {s['dist_score']}/40")
    print(f"  Speed Score    : {s['speed_score']}/25")
    print(f"  Urgency Score  : {s['time_score']}/20")
    print(f"  Velocity Score : {s['vel_score']}/15")
    print()

print("─" * 60)
top = results[0]
print(f"  🚨 HIGHEST RISK: {top['name']}")
print(f"     Score  : {top['scores']['total']}/100")
print(f"     Status : {top['label']}")
print(f"     Action : ", end="")
if top['scores']['total'] >= 80:
    print("MANEUVER ISS IMMEDIATELY")
elif top['scores']['total'] >= 60:
    print("PREPARE MANEUVER PLAN")
elif top['scores']['total'] >= 40:
    print("MONITOR CLOSELY")
else:
    print("CONTINUE MONITORING")
print("=" * 60)

# ─────────────────────────────────
# PLOT — RISK SCORE DASHBOARD
# ─────────────────────────────────
fig = plt.figure(figsize=(16, 10))
fig.patch.set_facecolor('#0D1117')

# ── Plot 1: Risk Score Bar Chart ─
ax1 = fig.add_subplot(2, 2, 1)
ax1.set_facecolor('#161B22')

names  = [r["name"] for r in results]
scores = [r["scores"]["total"] for r in results]
colors = [r["color"] for r in results]

bars = ax1.barh(names, scores, color=colors,
                edgecolor='white', linewidth=0.5)
ax1.axvline(x=80, color='red',
            linestyle='--', linewidth=1.5,
            label='Critical (80)')
ax1.axvline(x=60, color='orange',
            linestyle='--', linewidth=1,
            label='High (60)')
ax1.axvline(x=40, color='yellow',
            linestyle='--', linewidth=1,
            label='Medium (40)')

for bar, score in zip(bars, scores):
    ax1.text(score + 0.5, bar.get_y() + bar.get_height()/2,
             f'{score}/100', va='center',
             color='white', fontsize=9, fontweight='bold')

ax1.set_xlim(0, 105)
ax1.set_xlabel('Risk Score', color='white')
ax1.set_title('Risk Scores — All Debris',
              color='white', fontweight='bold')
ax1.tick_params(colors='white')
ax1.legend(fontsize=7, facecolor='#0D1117',
           labelcolor='white')
ax1.grid(axis='x', alpha=0.15, color='gray')

# ── Plot 2: Score Breakdown ──────
ax2 = fig.add_subplot(2, 2, 2)
ax2.set_facecolor('#161B22')

top_r      = results[0]
categories = ['Distance\n(max 40)',
              'Speed\n(max 25)',
              'Urgency\n(max 20)',
              'Velocity\n(max 15)']
values     = [
    top_r["scores"]["dist_score"],
    top_r["scores"]["speed_score"],
    top_r["scores"]["time_score"],
    top_r["scores"]["vel_score"],
]
maxvals    = [40, 25, 20, 15]
bar_colors = ['#FF4757', '#FF6B35', '#F59E0B', '#818CF8']

x = np.arange(len(categories))
ax2.bar(x, maxvals, color='#1C2333',
        edgecolor='gray', linewidth=0.5,
        label='Maximum possible')
ax2.bar(x, values, color=bar_colors,
        edgecolor='white', linewidth=0.5,
        label='Actual score')

for i, (v, m) in enumerate(zip(values, maxvals)):
    ax2.text(i, v + 0.3, f'{v}/{m}',
             ha='center', color='white',
             fontsize=9, fontweight='bold')

ax2.set_xticks(x)
ax2.set_xticklabels(categories,
                    color='white', fontsize=8)
ax2.set_title(
    f'Score Breakdown — {top_r["name"]} (Highest Risk)',
    color='white', fontweight='bold'
)
ax2.tick_params(colors='white')
ax2.legend(fontsize=7, facecolor='#0D1117',
           labelcolor='white')
ax2.grid(axis='y', alpha=0.15, color='gray')

# ── Plot 3: Distance over 72h ────
ax3 = fig.add_subplot(2, 2, 3)
ax3.set_facecolor('#161B22')

for r in results:
    hrs   = [i for i, d in enumerate(r["hourly_dists"])
             if d is not None]
    dists = [d for d in r["hourly_dists"]
             if d is not None]
    ax3.plot(hrs, dists, color=r["color"],
             linewidth=2, label=r["name"])
    ax3.scatter(r["min_hour"], r["min_dist"],
                color=r["color"], s=80, zorder=5)

ax3.axhline(y=100, color='red',
            linestyle='--', linewidth=1,
            label='Danger (100km)')
ax3.axhline(y=500, color='orange',
            linestyle='--', linewidth=0.8,
            label='Monitor (500km)')
ax3.set_xlabel('Hours from Now', color='white')
ax3.set_ylabel('Distance (km)', color='white')
ax3.set_title('Distance Over 72 Hours',
              color='white', fontweight='bold')
ax3.tick_params(colors='white')
ax3.legend(fontsize=7, facecolor='#0D1117',
           labelcolor='white')
ax3.grid(alpha=0.15, color='gray')

# ── Plot 4: Risk Level Summary ───
ax4 = fig.add_subplot(2, 2, 4)
ax4.set_facecolor('#161B22')
ax4.axis('off')

summary_text = "THREAT SUMMARY\n\n"
for r in results:
    bar = "█" * (r["scores"]["total"] // 5)
    summary_text += (
        f"{r['name']}\n"
        f"Score : {r['scores']['total']}/100\n"
        f"Level : {r['label']}\n"
        f"Time  : T+{r['min_hour']}h\n"
        f"Dist  : {r['min_dist']:.0f} km\n"
        f"{bar}\n\n"
    )

ax4.text(0.05, 0.95, summary_text,
         transform=ax4.transAxes,
         color='white', fontsize=8,
         verticalalignment='top',
         fontfamily='monospace',
         bbox=dict(boxstyle='round',
                   facecolor='#1C2333',
                   alpha=0.8))

plt.suptitle(
    'DebrisWatch AI — Risk Score Engine Dashboard',
    color='white', fontsize=14,
    fontweight='bold', y=1.01
)
plt.tight_layout()
plt.savefig('day5_risk_scores.png',
            dpi=150, facecolor='#0D1117')
print("\n  Saved → day5_risk_scores.png")
print("  Day 5 COMPLETE ✅")
print("\n  Tomorrow Day 6 → Build Web Dashboard")
print("  Open browser → see everything live!")
plt.show()