import pygame
import math
import random

# Initialize Pygame and explicitly set up the display
pygame.init()
pygame.mixer.init()
pygame.font.init()

# Screen settings
WIDTH = 800
HEIGHT = 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("The Asteroid Field")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
ORANGE = (255, 165, 0)

# Sound effects with absolute paths
shoot_sound = pygame.mixer.Sound(r"C:\Users\garre\OneDrive\Desktop\Asteroids\Sounds\shot-friendly.mp3")
shoot_sound.set_volume(0.7)
explosion_sound = pygame.mixer.Sound(r"C:\Users\garre\OneDrive\Desktop\Asteroids\Sounds\explosion-asteroid.mp3")
enemy_shoot_sound = pygame.mixer.Sound(r"C:\Users\garre\OneDrive\Desktop\Asteroids\Sounds\shot-enemy.mp3")
ship_explosion_sound = pygame.mixer.Sound(r"C:\Users\garre\OneDrive\Desktop\Asteroids\Sounds\explosion-ship.mp3")

# Global font initialization
FONT = pygame.font.Font(None, 36)

class Vector2:
    def __init__(self, x=0, y=0):
        self.x = x
        self.y = y

    def __add__(self, other):
        return Vector2(self.x + other.x, self.y + other.y)

    def __sub__(self, other):
        return Vector2(self.x - other.x, self.y - other.y)

    def __mul__(self, scalar):
        return Vector2(self.x * scalar, self.y * scalar)

    def __truediv__(self, scalar):
        return Vector2(self.x / scalar, self.y / scalar)

    def magnitude(self):
        return math.sqrt(self.x**2 + self.y**2)

    def normalize(self):
        mag = self.magnitude()
        if mag > 0:
            return Vector2(self.x / mag, self.y / mag)
        return Vector2(0, 0)

    def dot(self, other):
        return self.x * other.x + self.y * other.y

class Player:
    def __init__(self):
        self.reset()

    def reset(self):
        self.x = WIDTH // 2
        self.y = HEIGHT // 2
        self.angle = 0
        self.vx = 0
        self.vy = 0
        self.max_speed = 10
        self.rotation_speed = 5
        self.radius = 15
        self.has_moved = False
        self.points = [(0, -self.radius), (-self.radius, self.radius), (self.radius, self.radius)]

    def rotate(self, direction):
        self.angle += self.rotation_speed * direction

    def move(self):
        self.x += self.vx
        self.y += self.vy
        self.x %= WIDTH
        self.y %= HEIGHT

    def accelerate(self):
        rad = math.radians(self.angle)
        thrust_x = math.sin(rad) * 0.2
        thrust_y = -math.cos(rad) * 0.2
        self.vx += thrust_x
        self.vy += thrust_y
        total_speed = math.sqrt(self.vx**2 + self.vy**2)
        if total_speed > self.max_speed:
            scale = self.max_speed / total_speed
            self.vx *= scale
            self.vy *= scale
        self.has_moved = True

    def draw(self):
        rotated_points = []
        for x, y in self.points:
            rad = math.radians(self.angle)
            new_x = x * math.cos(rad) - y * math.sin(rad)
            new_y = x * math.sin(rad) + y * math.cos(rad)
            rotated_points.append((new_x + self.x, new_y + self.y))
        if not self.has_moved:
            if (pygame.time.get_ticks() % 200) < 100:
                pygame.draw.polygon(screen, WHITE, rotated_points, 2)
        else:
            pygame.draw.polygon(screen, WHITE, rotated_points, 2)

class Bullet:
    def __init__(self, x, y, angle, ship_vx, ship_vy, is_enemy=False, is_destroyer=False):
        self.x = x
        self.y = y
        self.radius = 3
        self.life = 30 if is_enemy else 45
        self.is_enemy = is_enemy
        rad = math.radians(angle)
        bullet_speed = 10
        if is_destroyer:
            self.vx = ship_vx + math.cos(rad) * bullet_speed
            self.vy = ship_vy + math.sin(rad) * bullet_speed
        else:
            adjusted_rad = math.radians(angle - 90)
            self.vx = ship_vx + math.cos(adjusted_rad) * bullet_speed
            self.vy = ship_vy + math.sin(adjusted_rad) * bullet_speed

    def move(self):
        self.x += self.vx
        self.y += self.vy
        self.x %= WIDTH
        self.y %= HEIGHT
        self.life -= 1

    def draw(self):
        color = RED if self.is_enemy else WHITE
        positions = [(self.x, self.y)]
        if self.x < self.radius:
            positions.append((self.x + WIDTH, self.y))
        elif self.x > WIDTH - self.radius:
            positions.append((self.x - WIDTH, self.y))
        wrapped_positions = positions.copy()
        for px, py in wrapped_positions:
            if py < self.radius:
                positions.append((px, py + HEIGHT))
            elif py > HEIGHT - self.radius:
                positions.append((px, py - HEIGHT))
        for pos in positions:
            pygame.draw.circle(screen, color, (int(pos[0]), int(pos[1])), self.radius)

class Missile:
    def __init__(self, x, y, angle, ship_vx, ship_vy, player):
        self.x = x
        self.y = y
        self.angle = angle
        self.vx = ship_vx + math.sin(math.radians(angle)) * 4
        self.vy = ship_vy - math.cos(math.radians(angle)) * 4
        self.radius = 3
        self.life = 240
        self.player = player
        self.turn_speed = 2
        self.is_enemy = True

    def move(self):
        player_dx = self.player.x - self.x
        player_dy = self.player.y - self.y
        desired_angle = math.degrees(math.atan2(player_dy, player_dx))
        angle_diff = (desired_angle - self.angle + 180) % 360 - 180
        if angle_diff > self.turn_speed:
            self.angle += self.turn_speed
        elif angle_diff < -self.turn_speed:
            self.angle -= self.turn_speed
        else:
            self.angle = desired_angle
        rad = math.radians(self.angle)
        self.vx = math.sin(rad) * 4
        self.vy = -math.cos(rad) * 4
        self.x += self.vx
        self.y += self.vy
        self.x %= WIDTH
        self.y %= HEIGHT
        self.life -= 1

    def draw(self):
        pygame.draw.circle(screen, ORANGE, (int(self.x), int(self.y)), self.radius)

class Enemy:
    MIN_SPEED = 1
    MAX_DRIFT_SPEED = 2

    def __init__(self):
        self.radius = 15
        side = random.randint(0, 3)
        if side == 0:
            self.x = -self.radius
            self.y = random.randint(0, HEIGHT)
            self.vx = random.uniform(0.5, 1.5)
            self.vy = random.uniform(-1, 1)
        elif side == 1:
            self.x = WIDTH + self.radius
            self.y = random.randint(0, HEIGHT)
            self.vx = random.uniform(-1.5, -0.5)
            self.vy = random.uniform(-1, 1)
        elif side == 2:
            self.x = random.randint(0, WIDTH)
            self.y = -self.radius
            self.vx = random.uniform(-1, 1)
            self.vy = random.uniform(0.5, 1.5)
        else:
            self.x = random.randint(0, WIDTH)
            self.y = HEIGHT + self.radius
            self.vx = random.uniform(-1, 1)
            self.vy = random.uniform(-1.5, -0.5)
        self.angle = random.uniform(0, 360)
        self.max_speed = 10
        self.rotation_speed = 3
        self.shoot_cooldown = 0
        self.current_cooldown = 0
        self.points = [(0, -self.radius), (-self.radius, self.radius), (0, self.radius * 0.5), (self.radius, self.radius)]
        self.projectile_class = Bullet

    def move(self):
        self.x += self.vx
        self.y += self.vy
        self.x %= WIDTH
        self.y %= HEIGHT

    def create_projectile(self, player):
        if self.projectile_class == Bullet:
            return Bullet(self.x, self.y, self.angle, self.vx, self.vy, is_enemy=True)
        elif self.projectile_class == Missile:
            return Missile(self.x, self.y, self.angle, self.vx, self.vy, player)

    def time_to_collision(self, obj):
        p_rel = Vector2(obj.x - self.x, obj.y - self.y)
        if isinstance(obj, Asteroid):
            obj_vx = math.sin(math.radians(obj.angle)) * obj.speed
            obj_vy = -math.cos(math.radians(obj.angle)) * obj.speed
        else:
            obj_vx = obj.vx
            obj_vy = obj.vy
        v_rel = Vector2(obj_vx - self.vx, obj_vy - self.vy)
        if v_rel.magnitude() == 0:
            return float('inf')
        dot_product = p_rel.dot(v_rel)
        t = -dot_product / v_rel.dot(v_rel)
        if t < 0:
            return float('inf')
        closest_approach = (p_rel + v_rel * t).magnitude()
        if closest_approach < self.radius + obj.radius:
            return t
        return float('inf')

    def adjust_velocity(self):
        speed = math.sqrt(self.vx**2 + self.vy**2)
        if speed < self.MIN_SPEED and speed > 0:
            rad = math.radians(self.angle)
            thrust_x = math.sin(rad) * 0.05
            thrust_y = -math.cos(rad) * 0.05
            self.vx += thrust_x
            self.vy += thrust_y
        elif speed > self.MAX_DRIFT_SPEED:
            braking_force_x = -self.vx / speed * 0.05
            braking_force_y = -self.vy / speed * 0.05
            self.vx += braking_force_x
            self.vy += braking_force_y
        speed = math.sqrt(self.vx**2 + self.vy**2)
        if speed > self.max_speed:
            scale = self.max_speed / speed
            self.vx *= scale
            self.vy *= scale

    def update(self, asteroids, player, other_enemies, elapsed_time, game_mode):
        if self.current_cooldown > 0:
            self.current_cooldown -= 1

        separation_force = Vector2(0, 0)
        for other in other_enemies:
            if other != self:
                dx = self.x - other.x
                dy = self.y - other.y
                distance = math.sqrt(dx**2 + dy**2)
                if distance < 50:
                    separation_force += Vector2(dx, dy).normalize() / max(distance, 1)

        threats = asteroids + [player]
        min_t = float('inf')
        imminent_threat = None
        for threat in threats:
            t = self.time_to_collision(threat)
            if t < min_t:
                min_t = t
                imminent_threat = threat

        projectile = None
        if min_t < 120:
            if imminent_threat == player:
                threat_direction = Vector2(self.x - player.x, self.y - player.y).normalize()
                desired_direction = (threat_direction + separation_force).normalize()
                desired_angle = math.degrees(math.atan2(desired_direction.y, desired_direction.x))
                angle_diff = (desired_angle - self.angle + 180) % 360 - 180
                if angle_diff > self.rotation_speed:
                    self.angle += self.rotation_speed
                elif angle_diff < -self.rotation_speed:
                    self.angle -= self.rotation_speed
                else:
                    self.angle = desired_angle
                rad = math.radians(self.angle)
                thrust_x = math.sin(rad) * 0.2
                thrust_y = -math.cos(rad) * 0.2
                self.vx += thrust_x
                self.vy += thrust_y
            else:
                threat_direction = Vector2(imminent_threat.x - self.x, imminent_threat.y - self.y).normalize()
                desired_direction = (threat_direction + separation_force).normalize()
                desired_angle = math.degrees(math.atan2(desired_direction.y, desired_direction.x))
                angle_diff = (desired_angle - self.angle + 180) % 360 - 180
                if angle_diff > self.rotation_speed:
                    self.angle += self.rotation_speed
                elif angle_diff < -self.rotation_speed:
                    self.angle -= self.rotation_speed
                else:
                    self.angle = desired_angle
                angle_to_threat = math.degrees(math.atan2(imminent_threat.y - self.y, imminent_threat.x - self.x))
                angle_diff_threat = abs((angle_to_threat - self.angle + 180) % 360 - 180)
                if angle_diff_threat < 10 and self.current_cooldown <= 0:
                    self.current_cooldown = 15
                    enemy_shoot_sound.play()
                    projectile = self.create_projectile(player)
        else:
            player_direction = Vector2(player.x - self.x, player.y - self.y).normalize()
            desired_direction = (player_direction + separation_force).normalize()
            desired_angle = math.degrees(math.atan2(desired_direction.y, desired_direction.x))
            angle_diff = (desired_angle - self.angle + 180) % 360 - 180
            if angle_diff > self.rotation_speed:
                self.angle += self.rotation_speed
            elif angle_diff < -self.rotation_speed:
                self.angle -= self.rotation_speed
            else:
                self.angle = desired_angle
            self.adjust_velocity()
            angle_to_player = math.degrees(math.atan2(player.y - self.y, player.x - self.x))
            angle_diff_player = abs((angle_to_player - self.angle + 180) % 360 - 180)
            if angle_diff_player < 10 and self.current_cooldown <= 0:
                self.current_cooldown = 45
                enemy_shoot_sound.play()
                projectile = self.create_projectile(player)

        self.adjust_velocity()
        return (projectile, None)

    def draw(self):
        rotated_points = []
        for x, y in self.points:
            rad = math.radians(self.angle)
            new_x = x * math.cos(rad) - y * math.sin(rad)
            new_y = x * math.sin(rad) + y * math.cos(rad)
            rotated_points.append((new_x + self.x, new_y + self.y))
        pygame.draw.polygon(screen, RED, rotated_points, 2)

class Destroyer:
    def __init__(self):
        self.radius = 40
        self.spawn_side = random.randint(0, 3)
        if self.spawn_side == 0:
            self.x = -self.radius
            self.y = random.randint(self.radius, HEIGHT - self.radius)
            self.vx = 0.5
            self.vy = 0
            self.angle = 0
        elif self.spawn_side == 1:
            self.x = WIDTH + self.radius
            self.y = random.randint(self.radius, HEIGHT - self.radius)
            self.vx = -0.5
            self.vy = 0
            self.angle = 180
        elif self.spawn_side == 2:
            self.x = random.randint(self.radius, WIDTH - self.radius)
            self.y = -self.radius
            self.vx = 0
            self.vy = 0.5
            self.angle = 90
        else:
            self.x = random.randint(self.radius, WIDTH - self.radius)
            self.y = HEIGHT + self.radius
            self.vx = 0
            self.vy = -0.5
            self.angle = 270
        self.max_speed = 0.5
        self.rotation_speed = 0
        self.shoot_cooldown = 60
        self.fighter_cooldown = 300
        self.current_shoot_cooldowns = [0, 0, 0, 0, 0, 0]
        self.current_fighter_cooldown = 0
        self.spawn_cycle = 0
        self.points = [
            (self.radius * 1.5, 0),
            (-self.radius * 1.2, -self.radius * 1.2),
            (-self.radius * 1.2, self.radius * 1.2)
        ]
        self.projectile_class = Bullet

    def move(self):
        self.x += self.vx
        self.y += self.vy
        if (self.spawn_side == 0 and self.x > WIDTH + self.radius) or \
           (self.spawn_side == 1 and self.x < -self.radius) or \
           (self.spawn_side == 2 and self.y > HEIGHT + self.radius) or \
           (self.spawn_side == 3 and self.y < -self.radius):
            return False
        return True

    def create_projectile(self, player, asteroids):
        rad = math.radians(self.angle)
        bullets = []
        gun_offsets = [
            (20, -10), (20, 10),
            (-10, -30), (-20, -30),
            (-10, 30), (-20, 30)
        ]
        right_angle = (self.angle - 90) % 360
        left_angle = (self.angle + 90) % 360
        forward_angle = self.angle
        target_angle = None
        if player.has_moved:
            player_angle = math.degrees(math.atan2(player.y - self.y, player.x - self.x))
            angle_diff = (player_angle - self.angle + 180) % 360 - 180
            if -35 <= angle_diff <= 35:
                target_angle = player_angle
        if not target_angle:
            closest_dist = float('inf')
            closest_asteroid = None
            for asteroid in asteroids:
                asteroid_angle = math.degrees(math.atan2(asteroid.y - self.y, asteroid.x - self.x))
                angle_diff = (asteroid_angle - self.angle + 180) % 360 - 180
                if -35 <= angle_diff <= 35:
                    dist = math.hypot(asteroid.x - self.x, asteroid.y - self.y)
                    if dist < closest_dist:
                        closest_dist = dist
                        closest_asteroid = asteroid
            if closest_asteroid:
                target_angle = math.degrees(math.atan2(closest_asteroid.y - self.y, closest_asteroid.x - self.x))
        forward_angle = target_angle if target_angle is not None else self.angle
        for i, (offset_x, offset_y) in enumerate(gun_offsets):
            if self.current_shoot_cooldowns[i] <= 0:
                gun_x = self.x + offset_x * math.cos(rad) - offset_y * math.sin(rad)
                gun_y = self.y + offset_x * math.sin(rad) + offset_y * math.cos(rad)
                if i < 2:
                    bullet_angle = forward_angle
                elif i < 4:
                    bullet_angle = right_angle
                else:
                    bullet_angle = left_angle
                pygame.mixer.Channel(i).play(enemy_shoot_sound)
                self.current_shoot_cooldowns[i] = self.shoot_cooldown
                bullets.append(Bullet(gun_x, gun_y, bullet_angle, self.vx, self.vy, is_enemy=True, is_destroyer=True))
        return bullets

    def update(self, asteroids, player, other_enemies, elapsed_time, game_mode):
        for i in range(len(self.current_shoot_cooldowns)):
            if self.current_shoot_cooldowns[i] > 0:
                self.current_shoot_cooldowns[i] -= 1
        if self.current_fighter_cooldown > 0:
            self.current_fighter_cooldown -= 1

        new_fighter = None
        if game_mode != 4 and self.current_fighter_cooldown <= 0 and elapsed_time is not None:
            if elapsed_time < 120 or self.spawn_cycle % 3 != 0:
                new_fighter = Enemy()
            else:
                new_fighter = Interceptor()
            new_fighter.x = self.x
            new_fighter.y = self.y
            self.current_fighter_cooldown = self.fighter_cooldown
            self.spawn_cycle = (self.spawn_cycle + 1) % 3

        bullets = self.create_projectile(player, asteroids)
        return (bullets, new_fighter)

    def draw(self):
        rotated_points = []
        for x, y in self.points:
            rad = math.radians(self.angle)
            new_x = x * math.cos(rad) - y * math.sin(rad)
            new_y = x * math.sin(rad) + y * math.cos(rad)
            rotated_points.append((new_x + self.x, new_y + self.y))
        pygame.draw.polygon(screen, RED, rotated_points, 2)

class Interceptor(Enemy):
    def __init__(self):
        super().__init__()
        self.shoot_cooldown = 120
        self.points = [
            (0, -self.radius * 1.2),
            (-self.radius * 0.8, -self.radius * 0.2),
            (-self.radius * 1.1, self.radius * 0.8),
            (-self.radius * 0.5, self.radius * 1.0),
            (0, self.radius * 1.2),
            (self.radius * 0.5, self.radius * 1.0),
            (self.radius * 1.1, self.radius * 0.8),
            (self.radius * 0.8, -self.radius * 0.2)
        ]
        self.projectile_class = Missile

    def update(self, asteroids, player, other_enemies, elapsed_time, game_mode):
        if self.current_cooldown > 0:
            self.current_cooldown -= 1

        separation_force = Vector2(0, 0)
        for other in other_enemies:
            if other != self:
                dx = self.x - other.x
                dy = self.y - other.y
                distance = math.sqrt(dx**2 + dy**2)
                if distance < 50:
                    separation_force += Vector2(dx, dy).normalize() / max(distance, 1)

        threats = asteroids + [player]
        min_t = float('inf')
        imminent_threat = None
        for threat in threats:
            t = self.time_to_collision(threat)
            if t < min_t:
                min_t = t
                imminent_threat = threat

        projectile = None
        if min_t < 120:
            if imminent_threat == player:
                threat_direction = Vector2(self.x - player.x, self.y - player.y).normalize()
                desired_direction = (threat_direction + separation_force).normalize()
                desired_angle = math.degrees(math.atan2(desired_direction.y, desired_direction.x))
                angle_diff = (desired_angle - self.angle + 180) % 360 - 180
                if angle_diff > self.rotation_speed:
                    self.angle += self.rotation_speed
                elif angle_diff < -self.rotation_speed:
                    self.angle -= self.rotation_speed
                else:
                    self.angle = desired_angle
                rad = math.radians(self.angle)
                thrust_x = math.sin(rad) * 0.2
                thrust_y = -math.cos(rad) * 0.2
                self.vx += thrust_x
                self.vy += thrust_y
            else:
                threat_direction = Vector2(imminent_threat.x - self.x, imminent_threat.y - self.y).normalize()
                desired_direction = (threat_direction + separation_force).normalize()
                desired_angle = math.degrees(math.atan2(desired_direction.y, desired_direction.x))
                angle_diff = (desired_angle - self.angle + 180) % 360 - 180
                if angle_diff > self.rotation_speed:
                    self.angle += self.rotation_speed
                elif angle_diff < -self.rotation_speed:
                    self.angle -= self.rotation_speed
                else:
                    self.angle = desired_angle
                angle_to_threat = math.degrees(math.atan2(imminent_threat.y - self.y, imminent_threat.x - self.x))
                angle_diff_threat = abs((angle_to_threat - self.angle + 180) % 360 - 180)
                if angle_diff_threat < 10 and self.current_cooldown <= 0:
                    self.current_cooldown = 15
                    enemy_shoot_sound.play()
                    projectile = self.create_projectile(player)
        else:
            player_direction = Vector2(player.x - self.x, player.y - self.y).normalize()
            desired_direction = (player_direction + separation_force).normalize()
            desired_angle = math.degrees(math.atan2(desired_direction.y, desired_direction.x))
            angle_diff = (desired_angle - self.angle + 180) % 360 - 180
            if angle_diff > self.rotation_speed:
                self.angle += self.rotation_speed
            elif angle_diff < -self.rotation_speed:
                self.angle -= self.rotation_speed
            else:
                self.angle = desired_angle
            self.adjust_velocity()
            angle_to_player = math.degrees(math.atan2(player.y - self.y, player.x - self.x))
            angle_diff_player = abs((angle_to_player - self.angle + 180) % 360 - 180)
            if angle_diff_player < 10 and self.current_cooldown <= 0:
                self.current_cooldown = 45
                enemy_shoot_sound.play()
                projectile = self.create_projectile(player)

        self.adjust_velocity()
        return (projectile, None)

class Asteroid:
    def __init__(self, x=None, y=None, size=3):
        self.size = size
        self.radius = size * 10
        if x is None or y is None:
            side = random.randint(0, 3)
            if side == 0:
                self.x = -self.radius
                self.y = random.randint(0, HEIGHT)
                self.angle = random.uniform(0, 180)
            elif side == 1:
                self.x = WIDTH + self.radius
                self.y = random.randint(0, HEIGHT)
                self.angle = random.uniform(180, 360)
            elif side == 2:
                self.x = random.randint(0, WIDTH)
                self.y = -self.radius
                self.angle = random.uniform(90, 270)
            else:
                self.x = random.randint(0, WIDTH)
                self.y = HEIGHT + self.radius
                self.angle = random.uniform(-90, 90)
        else:
            self.x = x
            self.y = y
            self.angle = random.uniform(0, 360)
        self.speed = random.uniform(1, 3)
        self.rotation = random.uniform(-2, 2)

    def move(self):
        rad = math.radians(self.angle)
        self.x += math.sin(rad) * self.speed
        self.y -= math.cos(rad) * self.speed
        self.x %= WIDTH
        self.y %= HEIGHT

    def draw(self):
        relative_points = []
        for i in range(8):
            angle = i * 45 + self.rotation
            dist = self.radius * random.uniform(0.8, 1.2)
            x = math.cos(math.radians(angle)) * dist
            y = math.sin(math.radians(angle)) * dist
            relative_points.append((x, y))
        positions = []
        buffer = self.radius * 1.2
        for dx, dy in [(0, 0), (WIDTH, 0), (-WIDTH, 0), (0, HEIGHT), (0, -HEIGHT), (WIDTH, HEIGHT), (-WIDTH, HEIGHT), (WIDTH, -HEIGHT), (-WIDTH, -HEIGHT)]:
            if (self.x + dx >= -buffer and self.x + dx <= WIDTH + buffer) and (self.y + dy >= -buffer and self.y + dy <= HEIGHT + buffer):
                wrapped_points = [(self.x + x + dx, self.y + y + dy) for x, y in relative_points]
                positions.append(wrapped_points)
        for pos_set in positions:
            pygame.draw.polygon(screen, WHITE, pos_set, 2)

class Particle:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.speed = random.uniform(1, 3)
        self.angle = random.uniform(0, 360)
        self.life = random.randint(20, 40)
        self.radius = 2

    def move(self):
        rad = math.radians(self.angle)
        self.x += math.sin(rad) * self.speed
        self.y -= math.cos(rad) * self.speed
        if self.x < 0 or self.x > WIDTH or self.y < 0 or self.y > HEIGHT:
            self.life = 0
        self.life -= 1

    def draw(self):
        if self.life > 0:
            pygame.draw.circle(screen, WHITE, (int(self.x), int(self.y)), self.radius)

def show_menu():
    if not pygame.display.get_init():
        print("Video system not initialized. Exiting...")
        pygame.quit()
        exit()

    menu_running = True
    game_mode = None

    menu_lines = [
        "Asteroid Field",
        "Select a game mode:",
        "1: Standard",
        "2: Fighters Only",
        "3: Interceptors Only",
        "4: Destroyers Only",
        "5-9: Coming Soon..."
    ]

    while menu_running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.KEYDOWN:
                if event.key in [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5, pygame.K_6, pygame.K_7, pygame.K_8, pygame.K_9]:
                    game_mode = int(event.key - pygame.K_0)
                    menu_running = False

        screen.fill(BLACK)
        for i, line in enumerate(menu_lines):
            text = FONT.render(line, True, WHITE)
            screen.blit(text, (50, 50 + i * 60))
        pygame.display.flip()

    return game_mode

def game_loop(game_mode):
    clock = pygame.time.Clock()
    running = True

    while running:
        player = Player()
        enemies = []
        bullets = []
        asteroids = [Asteroid() for _ in range(5)] if game_mode == 1 else [Asteroid()]
        particles = []
        survival_start_time = None  # Single timer for everything
        enemy_destroyed_time = None
        space_pressed = False
        game_over = False
        asteroids_added = False
        large_asteroid_timer = 0
        medium_asteroid_timer = 0

        while running and not game_over:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return False

            keys = pygame.key.get_pressed()
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                player.rotate(1)
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                player.rotate(-1)
            if keys[pygame.K_UP] or keys[pygame.K_w]:
                player.accelerate()
                if survival_start_time is None:
                    survival_start_time = pygame.time.get_ticks()

            # Calculate elapsed_time only if survival_start_time is set
            elapsed_time = (pygame.time.get_ticks() - survival_start_time) / 1000 if survival_start_time is not None else 0
            
            can_shoot = game_mode != 1 or (elapsed_time >= 15)
            if keys[pygame.K_SPACE] and not space_pressed and can_shoot:
                shoot_sound.play()
                if survival_start_time is None:
                    survival_start_time = pygame.time.get_ticks()
                bullets.append(Bullet(player.x, player.y, player.angle, player.vx, player.vy))
            space_pressed = keys[pygame.K_SPACE]

            if game_mode == 1:
                if elapsed_time >= 75 and not asteroids_added:
                    asteroids.extend([Asteroid() for _ in range(3)])
                    asteroids_added = True
                if elapsed_time >= 115:
                    large_asteroid_timer += 1 / 60
                    medium_asteroid_timer += 1 / 60
                    if large_asteroid_timer >= 30:
                        asteroids.append(Asteroid(size=3))
                        large_asteroid_timer = 0
                    if medium_asteroid_timer >= 15:
                        asteroids.append(Asteroid(size=2))
                        medium_asteroid_timer = 0
            else:
                if elapsed_time >= 30:
                    large_asteroid_timer += 1 / 60
                    if large_asteroid_timer >= 30:
                        asteroids.append(Asteroid(size=3))
                        large_asteroid_timer = 0

            player.move()

            if game_mode == 1:
                wave_size = 1
                if elapsed_time >= 60 and elapsed_time < 90:
                    wave_size = 2
                if elapsed_time >= 90 and elapsed_time < 180:
                    wave_size = 1
                if elapsed_time >= 180:
                    wave_size = 0

                if elapsed_time >= 31 and not enemies and enemy_destroyed_time is None:
                    if elapsed_time < 90:
                        enemies.extend([Enemy() for _ in range(wave_size)])
                    elif elapsed_time >= 90 and elapsed_time < 180:
                        enemies.extend([Destroyer() for _ in range(wave_size)])

                if enemy_destroyed_time and (pygame.time.get_ticks() - enemy_destroyed_time) / 1000 >= 5 and not enemies:
                    if elapsed_time < 90:
                        enemies.extend([Enemy() for _ in range(wave_size)])
                    elif elapsed_time >= 90 and elapsed_time < 180:
                        enemies.extend([Destroyer() for _ in range(wave_size)])
                    enemy_destroyed_time = None

            elif game_mode == 2:
                wave_size = 1
                if elapsed_time >= 60:
                    wave_size = 2

                if elapsed_time >= 5 and not enemies and enemy_destroyed_time is None:
                    enemies.extend([Enemy() for _ in range(wave_size)])

                if enemy_destroyed_time and (pygame.time.get_ticks() - enemy_destroyed_time) / 1000 >= 5 and not enemies:
                    enemies.extend([Enemy() for _ in range(wave_size)])
                    enemy_destroyed_time = None

            elif game_mode == 3:
                wave_size = 1
                if elapsed_time >= 60:
                    wave_size = 2

                if elapsed_time >= 5 and not enemies and enemy_destroyed_time is None:
                    enemies.extend([Interceptor() for _ in range(wave_size)])

                if enemy_destroyed_time and (pygame.time.get_ticks() - enemy_destroyed_time) / 1000 >= 5 and not enemies:
                    enemies.extend([Interceptor() for _ in range(wave_size)])
                    enemy_destroyed_time = None

            elif game_mode == 4:
                wave_size = 1

                if elapsed_time >= 5 and not enemies and enemy_destroyed_time is None:
                    enemies.extend([Destroyer() for _ in range(wave_size)])

                if enemy_destroyed_time and (pygame.time.get_ticks() - enemy_destroyed_time) / 1000 >= 5 and not enemies:
                    enemies.extend([Destroyer() for _ in range(wave_size)])
                    enemy_destroyed_time = None

            elif game_mode in [5, 6, 7, 8, 9]:
                wave_size = 0

            for enemy in enemies[:]:
                other_enemies = [e for e in enemies if e != enemy]
                enemy.move()
                keep_alive = True
                if isinstance(enemy, Destroyer):
                    keep_alive = enemy.move()
                if not keep_alive:
                    enemies.remove(enemy)
                    if not enemies:
                        enemy_destroyed_time = pygame.time.get_ticks()
                    continue
                projectile, new_fighter = enemy.update(asteroids, player, other_enemies, elapsed_time, game_mode)
                if projectile:
                    if isinstance(projectile, list):
                        bullets.extend(projectile)
                    else:
                        bullets.append(projectile)
                if new_fighter:
                    enemies.append(new_fighter)

            bullets = [b for b in bullets if b.life > 0]
            for bullet in bullets:
                bullet.move()
            for asteroid in asteroids:
                asteroid.move()
            particles = [p for p in particles if p.life > 0]
            for particle in particles:
                particle.move()

            new_asteroids = []
            for asteroid in asteroids[:]:
                hit = False
                dist_player = math.hypot(player.x - asteroid.x, player.y - asteroid.y)
                if dist_player < player.radius + asteroid.radius and player.has_moved:
                    pygame.mixer.Channel(6).play(ship_explosion_sound)
                    game_over = True
                    break

                for enemy in enemies[:]:
                    dist_enemy = math.hypot(enemy.x - asteroid.x, enemy.y - asteroid.y)
                    if dist_enemy < enemy.radius + asteroid.radius:
                        if isinstance(enemy, Destroyer):
                            asteroids.remove(asteroid)
                            if asteroid.size > 1:
                                offset1 = random.uniform(-10, 10)
                                offset2 = random.uniform(-10, 10)
                                new_asteroids.append(Asteroid(asteroid.x + offset1, asteroid.y + offset2, asteroid.size - 1))
                                new_asteroids.append(Asteroid(asteroid.x - offset1, asteroid.y - offset2, asteroid.size - 1))
                            explosion_sound.play()
                        else:
                            asteroids.remove(asteroid)
                            enemies.remove(enemy)
                            pygame.mixer.Channel(6).play(ship_explosion_sound)
                            if not enemies:
                                enemy_destroyed_time = pygame.time.get_ticks()
                        hit = True
                        break
                if hit:
                    continue

                for bullet in bullets[:]:
                    dist_bullet = math.hypot(bullet.x - asteroid.x, bullet.y - asteroid.y)
                    if dist_bullet < asteroid.radius + bullet.radius:
                        bullets.remove(bullet)
                        asteroids.remove(asteroid)
                        if asteroid.size == 3:
                            explosion_sound.set_volume(1.0)
                        elif asteroid.size == 2:
                            explosion_sound.set_volume(0.8)
                        else:
                            explosion_sound.set_volume(0.6)
                        explosion_sound.play()
                        for _ in range(10):
                            particles.append(Particle(asteroid.x, asteroid.y))
                        if asteroid.size > 1:
                            offset1 = random.uniform(-10, 10)
                            offset2 = random.uniform(-10, 10)
                            new_asteroids.append(Asteroid(asteroid.x + offset1, asteroid.y + offset2, asteroid.size - 1))
                            new_asteroids.append(Asteroid(asteroid.x - offset1, asteroid.y - offset2, asteroid.size - 1))
                        hit = True
                        break
                if hit:
                    continue

                for enemy in enemies[:]:
                    dist_player_enemy = math.hypot(player.x - enemy.x, player.y - enemy.y)
                    if dist_player_enemy < player.radius + enemy.radius and player.has_moved:
                        pygame.mixer.Channel(6).play(ship_explosion_sound)
                        if not isinstance(enemy, Destroyer):
                            enemies.remove(enemy)
                            if not enemies:
                                enemy_destroyed_time = pygame.time.get_ticks()
                        game_over = True
                        break

                for enemy in enemies[:]:
                    for bullet in bullets[:]:
                        if not bullet.is_enemy and not isinstance(enemy, Destroyer):
                            dist = math.hypot(bullet.x - enemy.x, bullet.y - enemy.y)
                            if dist < enemy.radius + bullet.radius:
                                bullets.remove(bullet)
                                enemies.remove(enemy)
                                pygame.mixer.Channel(6).play(ship_explosion_sound)
                                if not enemies:
                                    enemy_destroyed_time = pygame.time.get_ticks()
                                break

                for bullet in bullets[:]:
                    if bullet.is_enemy or isinstance(bullet, Missile):
                        dist = math.hypot(player.x - bullet.x, player.y - bullet.y)
                        if dist < player.radius + bullet.radius and player.has_moved:
                            bullets.remove(bullet)
                            pygame.mixer.Channel(6).play(ship_explosion_sound)
                            game_over = True
                            break

            asteroids.extend(new_asteroids)
            if game_over:
                continue

            screen.fill(BLACK)
            player.draw()
            for enemy in enemies:
                enemy.draw()
            for bullet in bullets:
                bullet.draw()
            for asteroid in asteroids:
                asteroid.draw()
            for particle in particles:
                particle.draw()

            if game_mode == 1 and survival_start_time is not None:
                elapsed_time = (pygame.time.get_ticks() - survival_start_time) / 1000
                if elapsed_time < 5:
                    if elapsed_time < 2.5 and int(elapsed_time * 2) % 2 == 0:
                        avoid_text = FONT.render("Avoid asteroids", True, WHITE)
                        screen.blit(avoid_text, (10, 10))
                    elif elapsed_time >= 2.5:
                        avoid_text = FONT.render("Avoid asteroids", True, WHITE)
                        screen.blit(avoid_text, (10, 10))
                elif 10 <= elapsed_time < 15:
                    time_in_window = elapsed_time - 10
                    if time_in_window < 2.5 and int(time_in_window * 2) % 2 == 0:
                        loading_text = FONT.render("Loading weapons", True, WHITE)
                        screen.blit(loading_text, (10, 10))
                    elif time_in_window >= 2.5:
                        loading_text = FONT.render("Loading weapons", True, WHITE)
                        screen.blit(loading_text, (10, 10))
                elif 15 <= elapsed_time < 20:
                    time_in_window = elapsed_time - 15
                    if time_in_window < 2.5 and int(time_in_window * 2) % 2 == 0:
                        ready_text = FONT.render("Weapons ready", True, WHITE)
                        screen.blit(ready_text, (10, 10))
                    elif time_in_window >= 2.5:
                        ready_text = FONT.render("Weapons ready", True, WHITE)
                        screen.blit(ready_text, (10, 10))
                elif 27 <= elapsed_time < 32:
                    time_in_window = elapsed_time - 27
                    if time_in_window < 2.5 and int(time_in_window * 2) % 2 == 0:
                        approaching_text = FONT.render("Enemy fighters approaching", True, WHITE)
                        screen.blit(approaching_text, (10, 10))
                    elif time_in_window >= 2.5:
                        approaching_text = FONT.render("Enemy fighters approaching", True, WHITE)
                        screen.blit(approaching_text, (10, 10))

            pygame.display.flip()
            clock.tick(60)

        end_time = pygame.time.get_ticks()
        survival_time = 0 if survival_start_time is None else (end_time - survival_start_time) / 1000

        while running and game_over:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        game_over = False
                    elif event.key == pygame.K_m:
                        return True

            screen.fill(BLACK)
            for enemy in enemies:
                enemy.draw()
            for bullet in bullets:
                bullet.move()
                bullet.draw()
            for asteroid in asteroids:
                asteroid.draw()
            for particle in particles:
                particle.move()
                particle.draw()
            
            survival_text = FONT.render(f"Survived: {survival_time:.1f} seconds", True, WHITE)
            game_over_text = FONT.render("Game Over - R to Restart, M for Menu", True, WHITE)
            screen.blit(survival_text, (10, 10))
            screen.blit(game_over_text, (WIDTH//2 - 200, HEIGHT//2))
            
            pygame.display.flip()
            clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    game_mode = show_menu()
    while game_mode:
        result = game_loop(game_mode)
        if result is False:
            break
        elif result is True:
            game_mode = show_menu()
        else:
            game_mode = show_menu()
