import pygame
import json
import math
import time

# --- Config ---
RES_W, RES_H = 1200, 600
HALF_W = RES_W // 2
FPS = 60
FOV = math.pi / 3
NUM_RAYS = 180 
DRAW_DIST = 800 
MAP_SIZE = 200
SUN_POS = [100, 100] 

# Universal Hand Colors
LEFT_HAND_COL = (50, 100, 255)  # Blue
RIGHT_HAND_COL = (50, 255, 100) # Green

class Player:
    def __init__(self, x, z, color, controls, laser_color):
        self.x, self.z = float(x), float(z)
        self.angle = 0.0 
        self.color = color
        self.laser_color = laser_color
        self.controls = controls 
        self.speed = 0.0

    def update(self, keys, grid):
        if keys[self.controls[2]]: self.angle -= 0.05
        if keys[self.controls[3]]: self.angle += 0.05
        if keys[self.controls[0]]: self.speed = min(self.speed + 0.015, 0.35)
        elif keys[self.controls[1]]: self.speed = max(self.speed - 0.015, -0.1)
        else: self.speed *= 0.94

        nx = self.x + math.cos(self.angle) * self.speed
        nz = self.z + math.sin(self.angle) * self.speed
        if 1 < nx < MAP_SIZE-1 and 1 < nz < MAP_SIZE-1:
            if grid[int(nx)][int(nz)] < 3:
                self.x, self.z = nx, nz

def draw_custom_rider(screen, x, y, sprite_h, target, obs):
    # Relative Math for rotation
    rel_ang = target.angle - obs.angle
    while rel_ang > math.pi: rel_ang -= 2*math.pi
    while rel_ang < -math.pi: rel_ang += 2*math.pi
    
    aspect = abs(math.sin(rel_ang))
    base_w = 16 + int(24 * aspect)
    body_h = sprite_h // 2.5
    
    # 1. SHADOW (Projected from Sun)
    vec_x = target.x - SUN_POS[0]
    sh_off_x = (vec_x / 50) * 10 
    pygame.draw.ellipse(screen, (10, 35, 10), (x - base_w//2 + sh_off_x, y + body_h - 2, base_w, 8))

    # 2. OVAL BODY
    pygame.draw.ellipse(screen, target.color, (x - base_w//2, y, base_w, body_h))
    
    # 3. HANDS (Left=Blue, Right=Green)
    # We use a simple depth offset so hands appear to wrap around the oval
    hand_size = max(4, body_h // 6)
    
    # Calculate visual X positions for hands
    # As the rider rotates, the hands move across the face of the oval
    # Using cos(rel_ang) to shift hands based on rider orientation
    shift = math.cos(rel_ang) * (base_w // 2)
    
    # Left Hand (Blue)
    pygame.draw.circle(screen, LEFT_HAND_COL, (int(x - base_w//2 + (shift/4)), int(y + body_h//2)), int(hand_size))
    # Right Hand (Green)
    pygame.draw.circle(screen, RIGHT_HAND_COL, (int(x + base_w//2 - (shift/4)), int(y + body_h//2)), int(hand_size))

    # 4. VISOR & LIGHTS
    facing_toward = abs(rel_ang) > math.pi/2
    if facing_toward:
        # Visor
        pygame.draw.rect(screen, (5, 5, 5), (x - (base_w-8)//2, y + 6, base_w-8, 4))
        # Headlight (Yellow)
        pygame.draw.circle(screen, (255, 255, 180), (int(x), int(y + body_h - 4)), 5)
    else:
        # Tail light (Red)
        pygame.draw.circle(screen, (220, 0, 0), (int(x), int(y + body_h - 4)), 4)

def draw_arena(screen, obs, target, grid, x_offset):
    # Sky & Sun
    for i in range(RES_H // 2):
        col = (20, 95 + i//4, 210)
        pygame.draw.line(screen, col, (x_offset, i), (x_offset + HALF_W, i))
    
    dsx, dsz = SUN_POS[0] - obs.x, SUN_POS[1] - obs.z
    sun_ang = math.atan2(dsz, dsx) - obs.angle
    while sun_ang > math.pi: sun_ang -= 2*math.pi
    if abs(sun_ang) < FOV:
        ssx = x_offset + (sun_ang / FOV + 0.5) * HALF_W
        pygame.draw.circle(screen, (255, 255, 160), (int(ssx), 65), 35)

    # Floor
    pygame.draw.rect(screen, (20, 90, 20), (x_offset, RES_H // 2, HALF_W, RES_H // 2))

    # Raycasting
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
                wall_h = (RES_H / (dist + 0.001)) * (2.0 if tile==3 else 0.5)
                fog = max(0, min(1, 1 - (dist / (DRAW_DIST * 0.15))))
                col = (255, 210, 0) if tile==3 else (130, 40, 40)
                f_col = [int(c * fog) for c in col]
                y_s = (RES_H - wall_h)//2 if tile==3 else RES_H//2
                pygame.draw.rect(screen, f_col, (x_offset+i*(HALF_W//NUM_RAYS), y_s, (HALF_W//NUM_RAYS)+1, wall_h))
                break

    # Sprite & Laser Rendering
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
            sprite_h = RES_H / (t_dist + 0.001)
            draw_custom_rider(screen, tx_screen, RES_H//2, sprite_h, target, obs)

def main():
    pygame.init()
    screen = pygame.display.set_mode((RES_W, RES_H))
    clock = pygame.time.Clock()
    with open("mega_arena.json", "r") as f: grid = json.load(f)['grid']

    # Blue Rider (Left Screen) vs Red Rider (Right Screen)
    # Both have Blue Left hands and Green Right hands
    p1 = Player(100, 20, (0, 140, 255), [pygame.K_w, pygame.K_s, pygame.K_a, pygame.K_d], (0, 255, 255))
    p2 = Player(110, 30, (255, 40, 40), [pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT], (255, 0, 255))

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