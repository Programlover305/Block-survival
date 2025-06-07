import pygame
import math
import time
import random
pygame.init()

# === Screen Setup ===
screen = pygame.display.set_mode((500, 500))
clock = pygame.time.Clock()

# === Classes ===
class Player():
    def __init__(self, x, y, speed, color, size):
        self.x = x
        self.y = y
        self.speed = speed
        self.color = color
        self.size = size
        self.alive = True
        self.last_direction = "right"
        self.health = 3

    def render(self):
        if self.alive:
            pygame.draw.rect(screen, self.color, (self.x, self.y, self.size, self.size))

    def get_hitbox(self):
        return pygame.Rect(self.x, self.y, self.size, self.size)

    def move(self, keys):
        moved = False
        if self.alive:
            if keys[pygame.K_w]: self.y -= self.speed; self.last_direction = "up"; moved = True
            if keys[pygame.K_s]: self.y += self.speed; self.last_direction = "down"; moved = True
            if keys[pygame.K_a]: self.x -= self.speed; self.last_direction = "left"; moved = True
            if keys[pygame.K_d]: self.x += self.speed; self.last_direction = "right"; moved = True

            # Boundaries
            self.x = max(0, min(self.x, 475))
            self.y = max(0, min(self.y, 475))

            if not moved:
                self.last_direction = "right"

    def push_back(self):
        push_distance = 50
        if self.last_direction == "up": self.y += push_distance
        elif self.last_direction == "down": self.y -= push_distance
        elif self.last_direction == "left": self.x += push_distance
        elif self.last_direction == "right": self.x -= push_distance

class Bullet():
    def __init__(self, x, y, speed, color, size, direction):
        self.x = x
        self.y = y
        self.speed = speed
        self.color = color
        self.size = size
        self.direction = direction

    def render(self):
        pygame.draw.rect(screen, self.color, (self.x, self.y, self.size, self.size))

    def move(self):
        if self.direction == "right": self.x += self.speed
        elif self.direction == "left": self.x -= self.speed
        elif self.direction == "up": self.y -= self.speed
        elif self.direction == "down": self.y += self.speed

    def get_hitbox(self):
        return pygame.Rect(self.x, self.y, self.size, self.size)

class Enemy():
    def __init__(self, x, y, speed, color, size):
        self.x = x
        self.y = y
        self.speed = speed
        self.color = color
        self.size = size
        self.alive = True
        self.health = 3
        self.angle = 0

    def render(self, player):
        if self.alive:
            dx, dy = player.x - self.x, player.y - self.y
            if dx != 0 or dy != 0:
                self.angle = math.atan2(dy, dx)
        start_pos = (self.x, self.y)
        end_pos = (self.x + self.size * math.cos(self.angle), self.y + self.size * math.sin(self.angle))
        pygame.draw.line(screen, self.color, start_pos, end_pos, 5)
        self.start_pos = start_pos
        self.end_pos = end_pos

    def move(self, player):
        if self.alive:
            dx, dy = player.x - self.x, player.y - self.y
            distance = math.hypot(dx, dy)
            if distance != 0:
                dx /= distance
                dy /= distance
            self.x += dx * self.speed
            self.y += dy * self.speed

    def get_hitbox(self):
        return pygame.Rect(self.start_pos[0], self.start_pos[1], abs(self.end_pos[0] - self.start_pos[0]), 5)

class Triangle():
    def __init__(self, x, y, speed, color, size):
        self.x = x
        self.y = y
        self.speed = speed
        self.color = color
        self.size = size
        self.alive = True
        self.last_shot_time = 0
        self.cooldown_time = 1000
        self.bullets = []
        self.health = 3

    def get_hitbox(self):
        return pygame.Rect(self.x - self.size, self.y - self.size, self.size * 2, self.size * 2)

    def render(self):
        if self.alive:
            points = [
                (self.x + self.size, self.y),
                (self.x - self.size, self.y - self.size),
                (self.x - self.size, self.y + self.size)
            ]
            pygame.draw.polygon(screen, self.color, points)

    def move(self):
        if self.alive:
            self.y += self.speed
            if self.y - self.size <= 0 or self.y + self.size >= 500:
                self.speed = -self.speed

    def shoot(self):
        if self.alive:
            current_time = pygame.time.get_ticks()
            if current_time - self.last_shot_time >= self.cooldown_time:
                self.bullets.append(Bullet(self.x, self.y, 3, (0, 255, 0), 5, "right"))
                self.last_shot_time = current_time

    def update_bullets(self):
        for b in self.bullets:
            b.move()
            b.render()
        self.bullets = [b for b in self.bullets if 0 <= b.x <= 500 and 0 <= b.y <= 500]

class Rect():
    def __init__(self, x, y, speed, color, size):
        self.x = x
        self.y = y
        self.speed = speed
        self.color = color
        self.size = size
        self.alive = True
        self.health = 5
        self.last_charge_time = 0
        self.charge_cooldown = 5000
        self.charge_direction = (1, 0)
        self.charge_delay = 2000
        self.stopped = False
        self.charging = False
        self.stop_time = 0

    def render(self):
        if self.alive:
            pygame.draw.rect(screen, self.color, (self.x, self.y, self.size * 5, self.size))

    def move(self, player):
        if not self.alive: return
        current_time = pygame.time.get_ticks()

        if self.charging:
            self.x += self.charge_direction[0] * self.speed
            self.y += self.charge_direction[1] * self.speed
            if self.x <= 0 or self.x + self.size * 5 >= 500 or self.y <= 0 or self.y + self.size >= 500:
                self.charging = False
                self.stopped = True
                self.speed = 0
                self.stop_time = current_time

        elif self.stopped:
            if current_time - self.stop_time >= self.charge_delay:
                self.turn_to_face(player)
                self.start_charge()

        else:
            self.x += self.speed
            if self.x <= 0 or self.x + self.size * 5 >= 500:
                self.speed = 0
                self.stopped = True
                self.stop_time = current_time
            if current_time - self.last_charge_time >= self.charge_cooldown:
                self.turn_to_face(player)

    def turn_to_face(self, player):
        dx, dy = player.x - self.x, player.y - self.y
        distance = math.hypot(dx, dy)
        if distance != 0:
            dx /= distance
            dy /= distance
        self.charge_direction = (dx, dy)

    def start_charge(self):
        self.speed = 7
        self.charging = True
        self.stopped = False
        self.last_charge_time = pygame.time.get_ticks()

    def get_hitbox(self):
        return pygame.Rect(self.x, self.y, self.size * 5, self.size)

# === Game Setup ===
player = Player(250, 250, 2, (0, 0, 0), 25)
bullets = []
enemies = [Enemy(random.randint(0, 450), random.randint(0, 450), 1, (0, 0, 0), 50)]
triangles = [Triangle(20, 200, 2, (0, 0, 255), 20)]
rectangles = [Rect(20, 200, 5, (0, 255, 0), 20)]

font = pygame.font.Font(None, 36)
score = 0
start_time = pygame.time.get_ticks()
last_duplicate_time = start_time
last_triangle_spawn = start_time
last_rectangle_spawn = start_time
cooldown_time = 500
last_shot = {k: 0 for k in ["up", "down", "left", "right"]}

# === Game Loop ===
running = True
while running:
    screen.fill((255, 255, 255))
    key_pressed = pygame.key.get_pressed()
    current_time = pygame.time.get_ticks()

    for event in pygame.event.get():
        if event.type == pygame.QUIT or key_pressed[pygame.K_ESCAPE]:
            running = False

    player.move(key_pressed)
    player.render()

    # === Player Shooting ===
    for direction in ["up", "down", "left", "right"]:
        key = getattr(pygame, f"K_{direction.upper()}")  # Fix: uppercase key constant
        if key_pressed[key] and current_time - last_shot[direction] >= cooldown_time:
            bullets.append(Bullet(player.x, player.y, 5, (255, 0, 0), 5, direction))
            last_shot[direction] = current_time

    # === Health Bar and Timer ===
    elapsed = (current_time - start_time) // 1000
    screen.blit(font.render(f"Time: {elapsed}s", True, (0, 0, 0)), (10, 10))
    pygame.draw.rect(screen, (255, 0, 0), (10, 40, 100, 15))
    pygame.draw.rect(screen, (0, 255, 0), (10, 40, int(100 * player.health / 3), 15))

    # === Spawning Logic ===
    if current_time - last_duplicate_time >= 5000:
        for e in enemies[:]:
            if e.alive:
                enemies.append(Enemy(random.randint(0, 450), random.randint(0, 450), 1, (0, 0, 0), 50))
        last_duplicate_time = current_time

    if current_time - last_triangle_spawn >= 10000:
        triangles.append(Triangle(20, random.randint(0, 400), 2, (0, 0, 255), 20))
        last_triangle_spawn = current_time

    if current_time - last_rectangle_spawn >= 20000:
        rectangles.append(Rect(20, random.randint(0, 400), 5, (0, 255, 0), 20))
        last_rectangle_spawn = current_time

    # === Enemy Movement and Rendering ===
    for e in enemies:
        if e.alive:
            e.move(player)
            e.render(player)
            if player.get_hitbox().colliderect(e.get_hitbox()):
                player.health -= 1
                player.push_back()

    for t in triangles:
        if t.alive:
            t.move()
            t.render()
            t.shoot()
            t.update_bullets()
            if player.get_hitbox().colliderect(t.get_hitbox()):
                player.health -= 1
                player.push_back()
            for b in t.bullets[:]:
                if player.get_hitbox().colliderect(b.get_hitbox()):
                    t.bullets.remove(b)
                    player.health -= 1

    for r in rectangles:
        if r.alive:
            r.move(player)
            r.render()
            if player.get_hitbox().colliderect(r.get_hitbox()):
                player.health -= 1
                player.push_back()

    # === Bullet Logic ===
    for bullet in bullets[:]:
        bullet.move()
        bullet.render()

        for group in [enemies, triangles, rectangles]:
            for obj in group:
                if obj.alive and bullet.get_hitbox().colliderect(obj.get_hitbox()):
                    obj.health -= 1
                    if obj.health <= 0:
                        obj.alive = False
                        score += 1
                    bullets.remove(bullet)
                    break

    if player.health <= 0:
        print("You died!")
        running = False

    if all(not e.alive for e in enemies + triangles + rectangles):
        print("You win!")
        print("Score:", score)
        running = False

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
