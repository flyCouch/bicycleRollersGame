import pygame
import json
import math
import time

# --- Config ---
RES_W, RES_H = 1200, 600
HALF_W = RES_W // 2
FPS = 60
FOV = math.pi / 3
NUM_RAYS = 200 # Higher density for smooth curves
DRAW_DIST = 900 
MAP_SIZE = 200
SUN_POS = [100, 100] 

# Hand Colors (Anatomical)
L_HAND_COL = (50, 120, 255) # Blue
R_HAND_COL = (50, 255, 120) # Green

class Player:
    def __init__(self, x, z, color, controls, laser_color):
        self.x, self.z = float(x), float(z)
        self.angle = 0.0 
        self.color = color
        self.laser_color = laser_color
        self.controls = controls 
        self.speed = 0.0

    def update(self, keys, grid):
        # Ultra Sharp Turning
        if keys[self.controls[2]]: self.angle -= 0.09
        if keys[self.controls[3]]: self.angle += 0.09
        
        if keys[self.controls[0]]: self.speed = min(self.speed + 0.02, 0.45)
        elif keys[self.controls[1]]: self.speed = max(self.speed - 0.02, -0.15)
        else: self.speed *= 0.93

        nx = self.x + math.cos(self.angle) * self.speed
        nz = self.z + math.sin(self.angle) * self.speed
        if 1 < nx < MAP_SIZE-1 and 1 < nz < MAP_SIZE-1:
            if grid[int(nx)][int(nz)] < 3:
                self.x, self.z = nx, nz
            else: self.speed *= -0.5

def draw_custom_rider(screen, x, y, sprite_h, target, obs):
    rel_ang = target.angle - obs.angle
    while rel_ang > math.pi: rel_ang -= 2*math.pi
    while rel_ang < -math.pi: rel_ang += 2*math.pi
    
    aspect = abs(math.sin(rel_ang))
    base_w = 16 + int(28 * aspect)
    body_h = sprite_h // 2.5
    
    # 1. SHADOW (Corrected Projection)
    s_dx = target.x - SUN_POS[0]
    sh_off = (s_dx / 40) * 12
    pygame.draw.ellipse(screen, (10, 25, 10), (x - base_w//2 + sh_off, y + body_h - 2, base_w, 8))

    # 2. BODY
    pygame.draw.ellipse(screen, target.color, (x - base_w//2, y, base_w, body_h))
    
    # 3. ANATOMICAL HANDS (Locked to Rider's L/R)
    h_size = max(4, body_h // 6)
    # Right Hand (Green)
    r_h_x = x + (math.cos(rel_ang + math.pi/2) * (base_w/2))
    pygame.draw.circle(screen, R_HAND_COL, (int(r_h_x), int(y + body_h//2)), int(h_size))
    # Left Hand (Blue)
    l_h_x = x + (math.cos(rel_ang - math.pi/2) * (base_w/2))
    pygame.draw.circle(screen, L_HAND_COL, (int(l_h_x), int(y + body_h//2)), int(h_size))

    # 4. VISOR & LIGHTS
    if abs(rel_ang) > math.pi/2: # Facing Us
        pygame.draw.rect(screen, (0, 0, 0), (x - (base_w-8)//2, y + 6, base_w-8, 4))
        pygame.draw.circle(screen, (255, 255, 200), (int(x), int(y + body_h - 4)), 5)
    else: # Facing Away
        pygame.draw.circle(screen, (220, 0, 0), (int(x), int(y + body_h - 4)), 4)

def draw_arena(screen, obs, target, grid, x_offset):
    # Background
    for i in range(RES_H // 2):
        col = (15, 80 + i//4, 180)
        pygame.draw.line(screen, col, (x_offset, i), (x_offset + HALF_W, i))
    pygame.draw.rect(screen, (15, 75, 15), (x_offset, RES_H // 2, HALF_W, RES_H // 2))

    # Raycasting Chaos
    z_buffer = [float('inf')] * NUM_RAYS
    for i in range(NUM_RAYS):
        ray_angle = obs.angle - FOV/2 + i * (FOV / NUM_RAYS)
        cos_a, sin_a = math.cos(ray_angle), math.sin(ray_angle)
        for depth in range(1, DRAW_DIST):
            tx, tz = obs.x + depth * 0.18 * cos_a, obs.z + depth * 0.18 * sin_a
            tile = grid[int(tx)][int(tz)] if (0 < tx < MAP_SIZE and 0 < tz < MAP_SIZE) else 3
            if tile >= 3:
                dist = depth * 0.18 * math.cos(obs.angle - ray_angle)
                z_buffer[i] = dist
                wall_h = (RES_H / (dist + 0.001)) * 2.0
                fog = max(0, min(1, 1 - (dist / (DRAW_DIST * 0.18))))
                
                # Color based on shape type
                if tile == 3: base_c = (200, 180, 0) # Border
                elif tile == 4: base_c = (100, 100, 255) # Circles/Spheres
                elif tile == 5: base_c = (255, 100, 100) # Ellipses
                else: base_c = (150, 150, 150) # Blobs
                
                f_col = [int(c * fog) for c in base_c]
                y_s = (RES_H - wall_h)//2
                pygame.draw.rect(screen, f_col, (x_offset+i*(HALF_W//NUM_RAYS), y_s, (HALF_W//NUM_RAYS)+1, wall_h))
                break

    # Laser & Rider
    dx, dz = target.x - obs.x, target.z - obs.z
    t_dist = math.sqrt(dx*dx + dz*dz)
    t_ang = math.atan2(dz, dx) - obs.angle
    while t_ang > math.pi: t_ang -= 2*math.pi
    while t_ang < -math.pi: t_ang += 2*math.pi

    if abs(t_ang) < FOV/2:
        tx_screen = x_offset + (t_ang / FOV + 0.5) * HALF_W
        pygame.draw.line(screen, target.laser_color, (tx_screen, 0), (tx_screen, RES_H // 2), 2)
        idx = int((t_ang / FOV + 0.5) * NUM_RAYS)
        if 0 <= idx < NUM_RAYS and t_dist < z_buffer[idx] + 1:
            draw_custom_rider(screen, tx_screen, RES_H//2, RES_H/(t_dist+0.001), target, obs)

def main():
    pygame.init()
    screen = pygame.display.set_mode((RES_W, RES_H))
    clock = pygame.time.Clock()
    with open("mega_arena.json", "r") as f: grid = json.load(f)['grid']

    p1 = Player(20, 20, (0, 140, 255), [pygame.K_w, pygame.K_s, pygame.K_a, pygame.K_d], (0, 255, 255))
    p2 = Player(180, 180, (255, 40, 40), [pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT], (255, 0, 255))

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT: return
        keys = pygame.key.get_pressed()
        p1.update(keys, grid); p2.update(keys, grid)
        screen.fill((0, 0, 0))
        draw_arena(screen, p1, p2, grid, 0)
        draw_arena(screen, p2, p1, grid, HALF_W)
        pygame.draw.rect(screen, (255, 255, 255), (HALF_W-2, 0, 4, RES_H))
        pygame.display.flip()
        clock.tick(FPS)

if __name__ == "__main__":
    main()