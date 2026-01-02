import pygame
import json
import math
import random
import serial
import threading

# --- Config ---
res_w, res_h = 1200, 600
FPS = 60
FOV = math.pi / 3
NUM_RAYS = 240 
DRAW_DIST = 900 
MAP_SIZE = 200

# --- SERIAL CONFIG (From rollerGame54) ---
SERIAL_PORT_1 = 'COM4' 
SERIAL_PORT_2 = 'COM5' 
BAUD_RATE = 9600
SENSITIVITY = 0.05 

# --- 10:00 AM CELESTIALS ---
SUN_AZIMUTH = math.radians(45) 
SUN_ELEVATION = 0.55 

class WorldCloud:
    def __init__(self):
        self.world_x = random.uniform(-1500, 1500)
        self.world_z = random.uniform(-1500, 1500)
        self.altitude = random.uniform(750, 1100) 
        self.speed_x = 0.03
        self.width = random.randint(350, 650)

    def update(self):
        self.world_x += self.speed_x
        if self.world_x > 1500: self.world_x = -1500

class Player:
    def __init__(self, x, z, color, controls, laser_color, serial_port=None):
        self.x, self.z = float(x), float(z)
        self.angle = 0.0 
        self.color = color
        self.laser_color = laser_color
        self.controls = controls 
        self.speed = 0.0
        self.pulses = 0 
        
        if serial_port:
            threading.Thread(target=self.serial_thread, args=(serial_port,), daemon=True).start()

    def serial_thread(self, port):
        try:
            ser = serial.Serial(port, BAUD_RATE, timeout=0.001)
            while True:
                line = ser.readline().decode('utf-8').strip()
                if line == "1": self.pulses += 1
        except: pass

    def update(self, keys, grid):
        if keys[self.controls[2]]: self.angle -= 0.09
        if keys[self.controls[3]]: self.angle += 0.09
        
        # Hardware + Keyboard input (W/Up)
        kb_boost = 4 if keys[self.controls[0]] else 0
        self.speed = (self.speed * 0.92) + ((self.pulses + kb_boost) * SENSITIVITY)
        self.pulses = 0

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
    sh_len = (1.0 - SUN_ELEVATION) * 45
    sh_dx = math.cos(SUN_AZIMUTH + math.pi) * sh_len
    pygame.draw.ellipse(screen, (5, 20, 5), (x - base_w//2 + sh_dx, y + body_h - 2, base_w, 8))
    pygame.draw.ellipse(screen, target.color, (x - base_w//2, y, base_w, body_h))
    h_size = max(4, body_h // 6)
    pygame.draw.circle(screen, (50, 255, 120), (int(x + (math.cos(rel_ang + math.pi/2) * (base_w/2))), int(y + body_h//2)), int(h_size))
    pygame.draw.circle(screen, (50, 120, 255), (int(x + (math.cos(rel_ang - math.pi/2) * (base_w/2))), int(y + body_h//2)), int(h_size))

def draw_arena(screen, obs, target, grid, x_offset, clouds, cur_w, cur_h):
    view_w = cur_w // 2
    screen.set_clip(pygame.Rect(x_offset, 0, view_w, cur_h))
    
    # 1. Sky & Ground
    pygame.draw.rect(screen, (20, 85, 20), (x_offset, cur_h // 2, view_w, cur_h // 2))
    for i in range(cur_h // 2):
        col = (25, 110 + i//5, 210) 
        pygame.draw.line(screen, col, (x_offset, i), (x_offset + view_w, i))

    # 2. 3D Positioned Clouds
    for c in clouds:
        dx, dz = c.world_x - obs.x, c.world_z - obs.z
        c_dist = math.sqrt(dx*dx + dz*dz)
        c_ang = math.atan2(dz, dx) - obs.angle
        while c_ang > math.pi: c_ang -= 2*math.pi
        while c_ang < -math.pi: c_ang += 2*math.pi
        if abs(c_ang) < FOV:
            cx = x_offset + (c_ang / FOV + 0.5) * view_w
            cy = (cur_h // 2.5) - (c.altitude / (c_dist * 0.02 + 1.2))
            c_sz = c.width / (c_dist * 0.005 + 1)
            pygame.draw.ellipse(screen, (245, 245, 250), (cx - c_sz//2, cy, c_sz, c_sz/4))

    # 3. Raycasting (The 10% fix is here: DRAW_DIST is high and covers the right side)
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
                pygame.draw.rect(screen, f_col, (x_offset + (i * ray_w), (cur_h - wall_h) // 2, math.ceil(ray_w), wall_h))
                break

    # 4. Laser & Rider (Drawn last = visible through walls like v41)
    dx, dz = target.x - obs.x, target.z - obs.z
    t_dist = math.sqrt(dx*dx + dz*dz)
    t_ang = math.atan2(dz, dx) - obs.angle
    while t_ang > math.pi: t_ang -= 2*math.pi
    while t_ang < -math.pi: t_ang += 2*math.pi
    
    if abs(t_ang) < FOV: # Wider check for laser visibility
        tx_screen = x_offset + (t_ang / FOV + 0.5) * view_w
        # Always draw laser beam
        pygame.draw.line(screen, target.laser_color, (tx_screen, 0), (tx_screen, cur_h // 2), 2)
        # Only draw rider body if not behind a wall (optional - can also be always on if you prefer)
        idx = int((t_ang / FOV + 0.5) * NUM_RAYS)
        if 0 <= idx < NUM_RAYS and t_dist < z_buffer[idx] + 5:
            draw_custom_rider(screen, tx_screen, cur_h//2, cur_h/(t_dist+0.001), target, obs)

    screen.set_clip(None)

def main():
    pygame.init()
    screen = pygame.display.set_mode((res_w, res_h), pygame.RESIZABLE)
    clock = pygame.time.Clock()
    with open("mega_arena.json", "r") as f: grid = json.load(f)['grid']
    global_clouds = [WorldCloud() for _ in range(15)]
    
    # Motion threads start automatically
    p1 = Player(20, 20, (0, 140, 255), [pygame.K_w, pygame.K_s, pygame.K_a, pygame.K_d], (0, 255, 255), SERIAL_PORT_1)
    p2 = Player(180, 180, (255, 40, 40), [pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT], (255, 0, 255), SERIAL_PORT_2)

    while True:
        cur_w, cur_h = screen.get_size()
        for event in pygame.event.get():
            if event.type == pygame.QUIT: return
            if event.type == pygame.KEYDOWN and event.key == pygame.K_f:
                pygame.display.set_mode((0,0), pygame.FULLSCREEN)
        
        for c in global_clouds: c.update()
        keys = pygame.key.get_pressed()
        p1.update(keys, grid); p2.update(keys, grid)
        
        screen.fill((0, 0, 0))
        draw_arena(screen, p1, p2, grid, 0, global_clouds, cur_w, cur_h)
        draw_arena(screen, p2, p1, grid, cur_w//2, global_clouds, cur_w, cur_h)
        
        pygame.draw.rect(screen, (255, 255, 255), (cur_w//2-2, 0, 4, cur_h))
        pygame.display.flip()
        clock.tick(FPS)

if __name__ == "__main__":
    main()