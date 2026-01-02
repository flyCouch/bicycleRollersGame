import pygame
import json
import math
import random
import serial
import threading
import array
import sys

# --- Config ---
res_w, res_h = 1200, 600
FPS = 60
FOV = math.pi / 3
NUM_RAYS = 240 
DRAW_DIST = 1000 
MAP_SIZE = 200
PROXIMITY_RANGE = 3.5 # Increased for better hit registration

# --- Wall Colors ---
WALL_COLORS = {
    3: (200, 160, 20),  # Gold
    4: (80, 180, 80),   # Green
    5: (80, 80, 200),   # Blue
    6: (180, 60, 60)    # Red
}

# --- SERIAL CONFIG ---
SERIAL_PORT_1 = 'COM4' 
SERIAL_PORT_2 = 'COM5' 
BAUD_RATE = 9600
SENSITIVITY = 0.05 

# --- 10:00 AM CELESTIALS ---
SUN_AZIMUTH = math.radians(45)
SUN_ELEVATION = 0.55 

def create_sound(freq_start, freq_end, duration, noise=False):
    sample_rate = 44100
    n_samples = int(sample_rate * duration)
    buf = array.array('h', [0] * n_samples)
    for i in range(n_samples):
        t = float(i) / sample_rate
        frac = i / n_samples
        freq = freq_start + (freq_end - freq_start) * frac
        val = random.uniform(-1, 1) if noise else math.sin(2 * math.pi * freq * t)
        fade = (1.0 - frac)
        buf[i] = int(val * 32767 * 0.3 * fade)
    return pygame.mixer.Sound(buf)

class Rocket:
    def __init__(self, x, z, angle, color):
        self.x, self.z = x, z
        self.angle = angle 
        self.speed = 2.8
        self.color = color

    def update(self, grid, target):
        self.x += math.cos(self.angle) * self.speed
        self.z += math.sin(self.angle) * self.speed
        if not (0 < self.x < MAP_SIZE and 0 < self.z < MAP_SIZE) or grid[int(self.x)][int(self.z)] >= 3:
            return "hit_wall"
        dist = math.sqrt((self.x - target.x)**2 + (self.z - target.z)**2)
        if dist < PROXIMITY_RANGE:
            return "hit_player"
        return None

class WorldCloud:
    def __init__(self):
        self.world_x, self.world_z = random.uniform(-1500, 1500), random.uniform(-1500, 1500)
        self.altitude, self.speed_x = random.uniform(750, 1100), 0.04
    def update(self):
        self.world_x += self.speed_x
        if self.world_x > 1500: self.world_x = -1500

class Player:
    def __init__(self, name, x, z, color, controls, laser_color, serial_port=None):
        self.name, self.x, self.z, self.color = name, float(x), float(z), color
        self.angle, self.laser_color, self.controls = 0.0, laser_color, controls 
        self.speed, self.pulses, self.rockets, self.fire_cooldown, self.score = 0.0, 0, [], 0, 0
        self.port_name = serial_port
        if self.port_name:
            threading.Thread(target=self.serial_thread, daemon=True).start()

    def serial_thread(self):
        try:
            ser = serial.Serial(self.port_name, BAUD_RATE, timeout=0.01)
            while True:
                line = ser.readline().decode('utf-8').strip()
                if line == "1": self.pulses += 1
        except: pass

    def update(self, keys, grid, sounds, opponent):
        if keys[self.controls[2]]: self.angle -= 0.08
        if keys[self.controls[3]]: self.angle += 0.08
        kb_boost = 4 if keys[self.controls[0]] else 0
        self.speed = (self.speed * 0.92) + ((self.pulses + kb_boost) * SENSITIVITY)
        self.pulses = 0 
        if keys[self.controls[1]] and self.fire_cooldown <= 0:
            spawn_x, spawn_z = self.x + math.cos(self.angle)*3, self.z + math.sin(self.angle)*3
            self.rockets.append(Rocket(spawn_x, spawn_z, self.angle, self.laser_color))
            sounds['whoosh'].play(); self.fire_cooldown = 20
        if self.fire_cooldown > 0: self.fire_cooldown -= 1
        nx, nz = self.x + math.cos(self.angle)*self.speed, self.z + math.sin(self.angle)*self.speed
        if 1 < nx < MAP_SIZE-1 and 1 < nz < MAP_SIZE-1:
            if grid[int(nx)][int(nz)] < 3: self.x, self.z = nx, nz
            else: self.speed *= -0.5
        for r in self.rockets[:]:
            res = r.update(grid, opponent)
            if res:
                sounds['hit'].play(); self.rockets.remove(r)
                if res == "hit_player": self.score += 1

def draw_custom_rider(screen, bx, by, sprite_h, target, obs):
    dx, dz = target.x - obs.x, target.z - obs.z
    angle_to_cam = math.atan2(dz, dx)
    rel_angle = target.angle - angle_to_cam
    aspect = abs(math.cos(rel_angle))
    base_w, body_h = max(20, int(45 * (0.5 + 0.5 * aspect))), max(18, sprite_h // 2.2)
    pygame.draw.ellipse(screen, target.color, (bx - base_w//2, by, base_w, body_h))
    h_size, radius = max(5, body_h // 6), base_w // 1.4
    rhx, rhy = bx + math.cos(rel_angle + 1.57)*radius, by + body_h/2 + math.sin(rel_angle + 1.57)*(radius/4)
    pygame.draw.circle(screen, (50, 255, 120), (int(rhx), int(rhy)), int(h_size))
    lhx, lhy = bx + math.cos(rel_angle - 1.57)*radius, by + body_h/2 + math.sin(rel_angle - 1.57)*(radius/4)
    pygame.draw.circle(screen, (50, 120, 255), (int(lhx), int(lhy)), int(h_size))

def draw_arena(screen, obs, target, grid, x_offset, clouds, cur_w, cur_h, all_rockets):
    view_w = cur_w // 2; screen.set_clip(pygame.Rect(x_offset, 0, view_w, cur_h))
    horizon = cur_h // 2
    # Environment
    pygame.draw.rect(screen, (20, 85, 20), (x_offset, horizon, view_w, horizon))
    for i in range(horizon):
        pygame.draw.line(screen, (25, 110 + (i*200//cur_h), 210), (x_offset, i), (x_offset + view_w, i))
    
    # Sun and Clouds
    sun_rel = math.atan2(math.sin(SUN_AZIMUTH - obs.angle), math.cos(SUN_AZIMUTH - obs.angle))
    if abs(sun_rel) < FOV:
        sx = x_offset + (sun_rel/FOV + 0.5) * view_w
        pygame.draw.circle(screen, (255, 255, 210), (int(sx), int(horizon - (SUN_ELEVATION*(cur_h//2.5)))), int(cur_h/15))
    for c in clouds:
        cdx, cdz = c.world_x - obs.x, c.world_z - obs.z
        c_dist = math.sqrt(cdx**2 + cdz**2)
        c_ang = math.atan2(cdz, cdx) - obs.angle
        c_ang = math.atan2(math.sin(c_ang), math.cos(c_ang))
        if abs(c_ang) < FOV * 1.5:
            cx, cy = x_offset + (c_ang/FOV + 0.5) * view_w, (cur_h // 2.5) - (c.altitude/(c_dist*0.02 + 1.2))
            pygame.draw.ellipse(screen, (245, 245, 250), (cx - cur_w//12, cy, cur_w//6, cur_h//12))

    # Raycasting (With Distance Floor to prevent Yellow Screen)
    z_buffer = [float('inf')] * NUM_RAYS
    ray_w = view_w / NUM_RAYS
    for i in range(NUM_RAYS):
        ray_angle = obs.angle - FOV/2 + i * (FOV / NUM_RAYS)
        cos_a, sin_a = math.cos(ray_angle), math.sin(ray_angle)
        for d in range(1, DRAW_DIST):
            tx, tz = obs.x + d * 0.2 * cos_a, obs.z + d * 0.2 * sin_a
            val = grid[int(tx)][int(tz)] if (0 < tx < MAP_SIZE and 0 < tz < MAP_SIZE) else 3
            if val >= 3:
                dist = d * 0.2 * math.cos(obs.angle - ray_angle)
                dist = max(0.5, dist) # Prevent infinitely tall walls
                z_buffer[i], wall_h = dist, (cur_h / (dist + 0.001)) * 1.8
                fog = max(0.1, min(1, 1 - (dist / 180)))
                pygame.draw.rect(screen, [int(c * fog) for c in WALL_COLORS.get(val, (200, 160, 20))], (x_offset + (i * ray_w), (cur_h - wall_h) // 2, math.ceil(ray_w), wall_h))
                break

    # Sprites
    for r in all_rockets:
        rdx, rdz = r.x - obs.x, r.z - obs.z
        rdist = math.sqrt(rdx**2 + rdz**2)
        rang = math.atan2(rdz, rdx) - obs.angle
        rang = math.atan2(math.sin(rang), math.cos(rang))
        if abs(rang) < FOV:
            idx = max(0, min(NUM_RAYS-1, int((rang/FOV + 0.5)*NUM_RAYS)))
            if rdist < z_buffer[idx]:
                rx = x_offset + (rang/FOV + 0.5) * view_w
                pygame.draw.circle(screen, r.color, (int(rx), horizon), max(4, int(cur_h/(rdist+0.001))//4))

    dx, dz = target.x - obs.x, target.z - obs.z
    t_dist, t_ang = math.sqrt(dx*dx + dz*dz), math.atan2(dz, dx) - obs.angle
    t_ang = math.atan2(math.sin(t_ang), math.cos(t_ang))
    if abs(t_ang) < FOV:
        tx_s = x_offset + (t_ang / FOV + 0.5) * view_w
        # Tracking Laser (Thick and Constant)
        pygame.draw.line(screen, target.laser_color, (int(tx_s), 0), (int(tx_s), horizon), 3)
        idx = max(0, min(NUM_RAYS - 1, int((t_ang / FOV + 0.5) * NUM_RAYS)))
        if t_dist < z_buffer[idx] + 8: 
            draw_custom_rider(screen, tx_s, horizon, cur_h/(t_dist+0.001), target, obs)
    screen.set_clip(None)

def main():
    pygame.init(); screen = pygame.display.set_mode((res_w, res_h), pygame.RESIZABLE)
    clock, font = pygame.time.Clock(), pygame.font.SysFont("Arial", 32, bold=True)
    sounds = {'whoosh': create_sound(400, 800, 0.15, True), 'hit': create_sound(120, 40, 0.4)}
    with open("mega_arena.json", "r") as f: grid = json.load(f)['grid']
    
    # Initialize and Clean Environment
    for r in range(len(grid)):
        for c in range(len(grid[0])):
            if grid[r][c] >= 3: grid[r][c] = random.choice([3, 4, 5, 6])
    
    # Explicitly clear 25x25 boxes at spawn points
    for r in range(5, 30):
        for c in range(5, 30): grid[r][c] = 0
    for r in range(170, 195):
        for c in range(170, 195): grid[r][c] = 0
        
    clouds = [WorldCloud() for _ in range(15)]
    p1 = Player("Blue", 15, 15, (0, 120, 255), [pygame.K_w, pygame.K_s, pygame.K_a, pygame.K_d], (0, 255, 255), SERIAL_PORT_1)
    p2 = Player("Red", 185, 185, (240, 30, 30), [pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT], (255, 0, 255), SERIAL_PORT_2)
    
    while True:
        cw, ch = screen.get_size()
        for event in pygame.event.get():
            if event.type == pygame.QUIT: sys.exit()
        keys = pygame.key.get_pressed(); [c.update() for c in clouds]
        p1.update(keys, grid, sounds, p2); p2.update(keys, grid, sounds, p1)
        screen.fill((0, 0, 0))
        draw_arena(screen, p1, p2, grid, 0, clouds, cw, ch, p1.rockets + p2.rockets)
        draw_arena(screen, p2, p1, grid, cw//2, clouds, cw, ch, p1.rockets + p2.rockets)
        pygame.draw.line(screen, (255, 255, 255), (cw//2, 0), (cw//2, ch), 4)
        score_surf = font.render(f"BLUE: {p1.score}      RED: {p2.score}", True, (255, 255, 255))
        screen.blit(score_surf, (cw//2 - score_surf.get_width()//2, 20))
        pygame.display.flip(); clock.tick(FPS)

if __name__ == "__main__": main()