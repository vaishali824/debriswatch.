import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from sgp4.api import Satrec, jday
from datetime import datetime

iss = Satrec.twoline2rv(
    "1 25544U 98067A   24001.50000000  .00001764  00000-0  40651-4 0  9993",
    "2 25544  51.6416 247.4627 0006703 130.5360 325.0288 15.50026242  9999"
)

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

now = datetime.utcnow()
jd, fr = jday(now.year, now.month, now.day,
              now.hour, now.minute, now.second)

_, iss_pos, _ = iss.sgp4(jd, fr)
iss_alt = np.sqrt(sum(x**2 for x in iss_pos)) - 6371

print("=" * 55)
print("      DEBRISWATCH AI — DAY 2 OUTPUT")
print("=" * 55)
print(f"\n  ISS Altitude : {iss_alt:.1f} km above Earth")
print(f"  X={iss_pos[0]:.0f}  Y={iss_pos[1]:.0f}  Z={iss_pos[2]:.0f} km")
print("\n  SCANNING DEBRIS OBJECTS...")
print("-" * 55)

results = []
for name, l1, l2 in debris_list:
    sat = Satrec.twoline2rv(l1, l2)
    error, pos, vel = sat.sgp4(jd, fr)
    if error == 0:
        dist = np.sqrt(
            (pos[0] - iss_pos[0])**2 +
            (pos[1] - iss_pos[1])**2 +
            (pos[2] - iss_pos[2])**2
        )
        if dist < 100:
            risk  = "RED    — HIGH RISK"
            color = "red"
        elif dist < 1000:
            risk  = "YELLOW — MONITOR"
            color = "orange"
        else:
            risk  = "GREEN  — SAFE"
            color = "lime"
        results.append((name, pos, dist, risk, color))
        print(f"  {name} : {dist:>10.1f} km  →  {risk}")

results.sort(key=lambda x: x[2])
print("-" * 55)
print(f"  CLOSEST : {results[0][0]} at {results[0][2]:.1f} km")
print(f"  SAFEST  : {results[-1][0]} at {results[-1][2]:.1f} km")
print("=" * 55)

fig = plt.figure(figsize=(12, 9))
ax  = fig.add_subplot(111, projection='3d')

u = np.linspace(0, 2*np.pi, 60)
v = np.linspace(0, np.pi, 30)
ex = 6371 * np.outer(np.cos(u), np.sin(v))
ey = 6371 * np.outer(np.sin(u), np.sin(v))
ez = 6371 * np.outer(np.ones(np.size(u)), np.cos(v))
ax.plot_surface(ex, ey, ez, color='steelblue',
                alpha=0.25, linewidth=0)

ax.scatter(iss_pos[0], iss_pos[1], iss_pos[2],
           color='lime', s=300, zorder=10,
           label=f'ISS (Alt: {iss_alt:.0f} km)')

for name, pos, dist, risk, color in results:
    ax.scatter(pos[0], pos[1], pos[2],
               color=color, s=180, zorder=9)
    ax.text(pos[0]+200, pos[1]+200, pos[2]+200,
            f'{name} — {dist:.0f} km',
            color=color, fontsize=8, fontweight='bold')

c = results[0]
ax.plot([iss_pos[0], c[1][0]],
        [iss_pos[1], c[1][1]],
        [iss_pos[2], c[1][2]],
        color='red', linewidth=2,
        linestyle='--',
        label=f'Closest: {c[2]:.0f} km')

ax.set_xlabel('X (km)')
ax.set_ylabel('Y (km)')
ax.set_zlabel('Z (km)')
ax.set_title('DebrisWatch AI — ISS + Debris RIGHT NOW',
             fontsize=13, fontweight='bold')
ax.legend(fontsize=9)

plt.tight_layout()
plt.savefig('day2_output.png', dpi=150)
print("\n  Saved → day2_output.png")
print("  Rotate the graph with your mouse!")
print("\n  Day 2 COMPLETE ✅")
plt.show()