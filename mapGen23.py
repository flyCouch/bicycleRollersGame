import json
import math
import random

MAP_SIZE = 200
grid = [[0 for _ in range(MAP_SIZE)] for _ in range(MAP_SIZE)]

def add_circle(cx, cz, r, val=4):
    for i in range(max(0, cx-r), min(MAP_SIZE, cx+r)):
        for j in range(max(0, cz-r), min(MAP_SIZE, cz+r)):
            if math.sqrt((i - cx)**2 + (j - cz)**2) <= r:
                grid[i][j] = val

def add_ellipse(cx, cz, rx, rz, angle, val=5):
    cos_a, sin_a = math.cos(angle), math.sin(angle)
    for i in range(max(0, cx-max(rx, rz)), min(MAP_SIZE, cx+max(rx, rz))):
        for j in range(max(0, cz-max(rx, rz)), min(MAP_SIZE, cz+max(rx, rz))):
            dx, dz = i - cx, j - cz
            # Rotated ellipse math
            x_rot = dx * cos_a + dz * sin_a
            z_rot = -dx * sin_a + dz * cos_a
            if (x_rot**2 / rx**2) + (z_rot**2 / rz**2) <= 1:
                grid[i][j] = val

def add_blob(cx, cz, size, nodes=6, val=6):
    points = []
    for n in range(nodes):
        ang = (n / nodes) * math.pi * 2
        r = size * random.uniform(0.5, 1.2)
        points.append((cx + math.cos(ang) * r, cz + math.sin(ang) * r))
    # Fill bounding box using point-in-polygon
    for i in range(int(cx-size), int(cx+size)):
        for j in range(int(cz-size), int(cz+size)):
            if 0 <= i < MAP_SIZE and 0 <= j < MAP_SIZE:
                # Basic cross-product winding check
                inside = True
                # (Simple square for demo, but complex poly logic goes here)
                if math.sqrt((i-cx)**2 + (j-cz)**2) < size * 0.7:
                    grid[i][j] = val

# --- Generate the Chaos ---
add_circle(50, 50, 15, 4)        # Large Cylinder
add_ellipse(150, 150, 30, 10, 0.8, 5) # Slanted Monolith
add_circle(100, 100, 10, 3)      # Small pillar
for _ in range(10): # Random debris
    add_circle(random.randint(10,190), random.randint(10,190), random.randint(2,8), 4)

with open("mega_arena.json", "w") as f:
    json.dump({'grid': grid}, f)