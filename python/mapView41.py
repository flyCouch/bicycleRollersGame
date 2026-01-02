import pygame
import json
import math
import random

# --- Config ---
res_w, res_h = 1200, 600
FPS = 60
FOV = math.pi / 3
NUM_RAYS = 240 
DRAW_DIST = 900 
MAP_SIZE = 200

# --- 10:00 AM SUN & WEATHER ---
SUN_AZIMUTH = math.radians(45) # South-East
SUN_ELEVATION = 0.55 

class Cloud:
    def __init__(self, view_w):
        self.x = random.uniform(0, view_w)
        self.y = random.randint(20, 140)
        self.speed = random.uniform(0.04, 0.08) # Slow, atmospheric drift
        self.width = random.randint(80, 160)

# Hand Colors (Anatomical Lock)
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
        if keys[self.controls[2]]: self.angle -= 0.09 # Sharp turning
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
    
    # 10am Shadow logic (Points North-West)
    sh_len = (1.0 - SUN_ELEVATION) * 45
    sh_dx = math.cos(SUN_AZIMUTH + math.pi) * sh_len
    pygame.draw.ellipse(screen, (5, 20, 5), (x - base_w//2 + sh_dx, y + body_h - 2, base_w, 8))

    # Body
    pygame.draw.ellipse(screen, target.color, (x - base_w//2, y, base_w, body_h))
    
    # Anatomical Hands
    h_size = max(4, body_h // 6)
    r_h_x = x + (math.cos(rel_ang + math.pi/2) * (base_w/2))
    pygame.draw.circle(screen, R_HAND_COL, (int(r_h_x), int(y + body_h//2)), int(h_size))
    l_h_x = x + (math.cos(rel_ang - math.pi/2) * (base_w/2))
    pygame.draw.circle(screen, L_HAND_COL, (int(l_h_x), int(y + body_h//2)), int(h_size))

    # Visor/Tail light
    if abs(rel_ang) > math.pi/2:
        pygame.draw.rect(screen, (0, 0, 0), (x - (base_w-8)//2, y + 6, base_w-8, 4))
        pygame.draw.circle(screen, (255, 255, 200), (int(x), int(y + body_h - 4)), 5)
    else:
        pygame.draw.circle(screen, (220, 0, 0), (int(x), int(y + body_h - 4)), 4)

def draw_arena(screen, obs, target, grid, x_offset, clouds, cur_w, cur_h):
    view_w = cur_w // 2
    
    # 1. Sky & Ground
    pygame.draw.rect(screen, (20, 85, 20), (x_offset, cur_h // 2, view_w, cur_h // 2))
    for i in range(cur_h // 2):
        col = (25, 110 + i//5, 210) # Bright Morning Sky
        pygame.draw.line(screen, col, (x_offset, i), (x_offset + view_w, i))

    # 2. Clouds (Restored)
    for c in clouds:
        c.x = (c.x + c.speed) % view_w
        # Slightly off-white morning tint
        pygame.draw.ellipse(screen, (240, 242, 250), (x_offset + c.x, c.y, c.width, 22))

    # 3. Celestial Sun (10 AM Fixed Anchor)
    sun_rel_angle = SUN_AZIMUTH - obs.angle
    while sun_rel_angle > math.pi: sun_rel_angle -= 2*math.pi
    while sun_rel_angle < -math.pi: sun_rel_angle += 2*math.pi
    
    if abs(sun_rel_angle) < FOV:
        ssx = x_offset + (sun_rel_angle / FOV + 0.5) * view_w
        ssy = (cur_h // 2) - (SUN_ELEVATION * (cur_h // 2.5))
        if x_offset - 50 < ssx < x_offset + view_w + 50:
            pygame.draw.circle(screen, (255, 255, 210), (int(ssx), int(ssy)), 40)

    # 4. Gapless Raycasting
    z_buffer = [float('inf')] * NUM_RAYS
    ray_w = view_w / NUM_RAYS 

    for i in range(NUM_RAYS):
        ray_angle = obs.angle - FOV/2 + i * (FOV / NUM_RAYS)
        cos_a, sin_a = math.cos(ray_angle), math.sin(ray_angle)
        
        for depth in range(1, DRAW_DIST):
            tx, tz = obs.x + depth * 0.18 * cos_a, obs.z + depth * 0.18 * sin_a
            tile = grid[int(tx)][int(tz)] if (0 < tx < MAP_SIZE and 0 < tz < MAP_SIZE) else 3
            
            if tile >= 3:
                dist = depth * 0.18 * math.cos(obs.angle - ray_angle)
                z_buffer[i] = dist
                wall_h = (cur_h / (dist + 0.001)) * 2.0
                fog = max(0, min(1, 1 - (dist / (DRAW_DIST * 0.18))))
                col = (205, 175, 0) if tile==3 else (100, 100, 230)
                f_col = [int(c * fog) for c in col]
                
                # Render using calculated ray_w and x_offset with ceil for overlap
                rect_x = x_offset + (i * ray_w)
                pygame.draw.rect(screen, f_col, (rect_x, (cur_h - wall_h) // 2, math.ceil(ray_w), wall_h))
                break

    # 5. Laser & Rider
    dx, dz = target.x - obs.x, target.z - obs.z
    t_dist = math.sqrt(dx*dx + dz*dz)
    t_ang = math.atan2(dz, dx) - obs.angle
    while t_ang > math.pi: t_ang -= 2*math.pi
    while t_ang < -math.pi: t_ang += 2*math.pi

    if abs(t_ang) < FOV/2:
        tx_screen = x_offset + (t_ang / FOV + 0.5) * view_w
        if x_offset <= tx_screen <= x_offset + view_w:
            pygame.draw.line(screen, target.laser_color, (tx_screen, 0), (tx_screen, cur_h // 2), 2)
            idx = int((t_ang / FOV + 0.5) * NUM_RAYS)
            if 0 <= idx < NUM_RAYS and t_dist < z_buffer[idx] + 1:
                draw_custom_rider(screen, tx_screen, cur_h//2, cur_h/(t_dist+0.001), target, obs)

def main():
    pygame.init()
    screen = pygame.display.set_mode((res_w, res_h), pygame.RESIZABLE)
    clock = pygame.time.Clock()
    fullscreen = False
    
    with open("mega_arena.json", "r") as f: grid = json.load(f)['grid']
    
    # Independent cloud lists per viewport
    clouds_p1 = [Cloud(res_w//2) for _ in range(10)]
    clouds_p2 = [Cloud(res_w//2) for _ in range(10)]

    p1 = Player(20, 20, (0, 140, 255), [pygame.K_w, pygame.K_s, pygame.K_a, pygame.K_d], (0, 255, 255))
    p2 = Player(180, 180, (255, 40, 40), [pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT], (255, 0, 255))

    while True:
        cur_w, cur_h = screen.get_size()
        for event in pygame.event.get():
            if event.type == pygame.QUIT: return
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_f:
                    fullscreen = not fullscreen
                    screen = pygame.display.set_mode((0,0), pygame.FULLSCREEN) if fullscreen else pygame.display.set_mode((res_w, res_h), pygame.RESIZABLE)

        keys = pygame.key.get_pressed()
        p1.update(keys, grid); p2.update(keys, grid)
        
        screen.fill((0, 0, 0))
        draw_arena(screen, p1, p2, grid, 0, clouds_p1, cur_w, cur_h)
        draw_arena(screen, p2, p1, grid, cur_w//2, clouds_p2, cur_w, cur_h)
        
        # Center Divider
        pygame.draw.rect(screen, (255, 255, 255), (cur_w//2-2, 0, 4, cur_h))
        pygame.display.flip()
        clock.tick(FPS)

if __name__ == "__main__":
    main()