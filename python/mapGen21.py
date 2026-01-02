import json
import random

def generate_mega_arena(size=200):
    # Initialize with Grass (2)
    grid = [[2 for _ in range(size)] for _ in range(size)]
    
    # Create 3-lane wide lanes (Total width 9-12 units)
    for i in range(1, 6):
        center_x = i * (size // 6)
        for z in range(size):
            for offset in range(-6, 6): # Wide lanes
                if 0 <= center_x + offset < size:
                    grid[center_x + offset][z] = 0 # Lane Pavement

    # Add random obstacle blocks (ID 4)
    for _ in range(400):
        rx, rz = random.randint(1, size-2), random.randint(1, size-2)
        if grid[rx][rz] == 0:
            grid[rx][rz] = 4

    data = {"grid": grid, "size": size}
    with open("mega_arena.json", "w") as f:
        json.dump(data, f)
    print("Mega Arena Generated!")

generate_mega_arena()