from sgp4.api import Satrec, jday
from datetime import datetime, timedelta
import numpy as np
import matplotlib.pyplot as plt

# Real TLE data of ISS (International Space Station)
line1 = "1 25544U 98067A   24001.50000000  .00001764  00000-0  40651-4 0  9993"
line2 = "2 25544  51.6416 247.4627 0006703 130.5360 325.0288 15.50026242  9999"

satellite = Satrec.twoline2rv(line1, line2)

positions = []
now = datetime.utcnow()

print("Calculating ISS position for next 72 hours...")
print("=" * 45)

for hour in range(73):
    t = now + timedelta(hours=hour)
    jd, fr = jday(t.year, t.month, t.day, t.hour, t.minute, t.second)
    error, pos, vel = satellite.sgp4(jd, fr)

    if error == 0:
        x, y, z = pos
        altitude = np.sqrt(x**2 + y**2 + z**2) - 6371
        speed = np.sqrt(vel[0]**2 + vel[1]**2 + vel[2]**2)
        positions.append((x, y, z))

        if hour % 12 == 0:
            print(f"T+{hour:02d}h → Altitude: {altitude:.1f} km | Speed: {speed:.2f} km/s")

print("=" * 45)
print(f"Total positions calculated: {len(positions)}")

# Plot 3D orbit
pos = np.array(positions)
fig = plt.figure(figsize=(10, 8))
ax = fig.add_subplot(111, projection='3d')

# Draw Earth
u, v = np.mgrid[0:2*np.pi:30j, 0:np.pi:15j]
ax.plot_wireframe(
    6371*np.cos(u)*np.sin(v),
    6371*np.sin(u)*np.sin(v),
    6371*np.cos(v),
    color='blue', alpha=0.1
)

# Draw orbit
ax.plot(pos[:,0], pos[:,1], pos[:,2], 'r-', linewidth=2, label='ISS Orbit (72h)')
ax.scatter(*pos[0], color='green', s=150, label='Now', zorder=5)
ax.scatter(*pos[-1], color='red', s=150, label='After 72h', zorder=5)

ax.set_title('DebrisWatch AI — ISS Orbit (72 Hours)', fontweight='bold')
ax.legend()
plt.tight_layout()
plt.savefig('my_first_orbit.png', dpi=150)
plt.show()

print("\nSaved as my_first_orbit.png")
print("Day 1 COMPLETE. You just tracked a real satellite.")