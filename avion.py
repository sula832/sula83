import pygame
import sys
import random
import math
import numpy as np

# 1. INICIALIZIMI I AUDIO & PYGAME
pygame.mixer.pre_init(44100, -16, 1, 512)
pygame.init()
pygame.font.init()

SCREEN_WIDTH = 900
SCREEN_HEIGHT = 650
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Sky Strike - Deluxe Sound Edition")

# Ngjyrat Neon / Lux
BG_COLOR = (12, 10, 26)
CYAN_GLOW = (0, 245, 255)
PURPLE_GLOW = (180, 0, 255)
NEON_RED = (255, 30, 90)
NEON_YELLOW = (255, 220, 0)
WHITE = (255, 255, 255)

clock = pygame.time.Clock()
font_ui = pygame.font.SysFont("Trebuchet MS", 22, bold=True)
font_title = pygame.font.SysFont("Trebuchet MS", 48, bold=True)

# -------------------------------------------------------------
# GENERATORI I EFEKTEVE ZANORE (Procedural Sound Generator)
# -------------------------------------------------------------
def generate_sound(sound_type):
    sample_rate = 44100
    if sound_type == "laser":
        duration = 0.12
        n_samples = int(sample_rate * duration)
        t = np.linspace(0, duration, n_samples, False)
        # Laser sweep frequency: nga 900Hz zbren në 200Hz
        freq = np.linspace(900, 200, n_samples)
        wave = 0.3 * np.sin(2 * np.pi * freq * t)
        # Fade out për glissando të pastër
        envelope = np.linspace(1, 0, n_samples)
        audio = (wave * envelope * 32767).astype(np.int16)
        return pygame.sndarray.make_sound(audio)

    elif sound_type == "explosion":
        duration = 0.35
        n_samples = int(sample_rate * duration)
        # Shpërthim me noise (zhurmë e bardhë me frekuencë të ulët)
        noise = np.random.uniform(-1, 1, n_samples)
        envelope = np.exp(-12 * np.linspace(0, 1, n_samples))
        audio = (noise * envelope * 0.4 * 32767).astype(np.int16)
        return pygame.sndarray.make_sound(audio)

    elif sound_type == "hit":
        duration = 0.15
        n_samples = int(sample_rate * duration)
        t = np.linspace(0, duration, n_samples, False)
        freq = np.linspace(150, 60, n_samples)
        wave = 0.5 * np.sin(2 * np.pi * freq * t) + 0.3 * np.random.uniform(-1, 1, n_samples)
        envelope = np.linspace(1, 0, n_samples)
        audio = (wave * envelope * 32767).astype(np.int16)
        return pygame.sndarray.make_sound(audio)

# Krijimi i sound effects në memorie
try:
    snd_laser = generate_sound("laser")
    snd_explosion = generate_sound("explosion")
    snd_hit = generate_sound("hit")
except Exception:
    snd_laser = snd_explosion = snd_hit = None  # Fallback nëse numpy mungon

# -------------------------------------------------------------
# CLASSES (Background, Particles, Player, Enemies, Bullets)
# -------------------------------------------------------------
class Starfield:
    def __init__(self):
        self.stars = []
        for _ in range(120):
            x = random.randint(0, SCREEN_WIDTH)
            y = random.randint(0, SCREEN_HEIGHT)
            speed = random.uniform(0.5, 4.0)
            radius = int(speed * 0.8)
            color = CYAN_GLOW if speed > 2.5 else (100, 110, 150)
            self.stars.append([x, y, speed, radius, color])

    def update_and_draw(self, surface):
        for star in self.stars:
            star[0] -= star[2]
            if star[0] < 0:
                star[0] = SCREEN_WIDTH
                star[1] = random.randint(0, SCREEN_HEIGHT)
            pygame.draw.circle(surface, star[4], (int(star[0]), int(star[1])), star[3])

class ParticleSystem:
    def __init__(self):
        self.particles = []

    def emit(self, x, y, color, count=10, speed_range=(1, 5)):
        for _ in range(count):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(*speed_range)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            size = random.randint(2, 5)
            lifetime = random.randint(15, 30)
            self.particles.append([x, y, vx, vy, size, lifetime, color])

    def update_and_draw(self, surface):
        for p in self.particles[:]:
            p[0] += p[2]
            p[1] += p[3]
            p[5] -= 1
            p[4] = max(1, p[4] - 0.1)
            if p[5] <= 0:
                self.particles.remove(p)
            else:
                pygame.draw.circle(surface, p[6], (int(p[0]), int(p[1])), int(p[4]))

class JetPlayer:
    def __init__(self):
        self.x = 100
        self.y = SCREEN_HEIGHT // 2
        self.speed = 7
        self.width = 45
        self.height = 30
        self.health = 100

    def handle_movement(self):
        keys = pygame.key.get_pressed()
        if (keys[pygame.K_UP] or keys[pygame.K_w]) and self.y > 20:
            self.y -= self.speed
        if (keys[pygame.K_DOWN] or keys[pygame.K_s]) and self.y < SCREEN_HEIGHT - self.height - 20:
            self.y += self.speed
        if (keys[pygame.K_LEFT] or keys[pygame.K_a]) and self.x > 20:
            self.x -= self.speed
        if (keys[pygame.K_RIGHT] or keys[pygame.K_d]) and self.x < SCREEN_WIDTH // 2:
            self.x += self.speed

    def draw(self, surface, particles):
        particles.emit(self.x - 5, self.y + 15, NEON_YELLOW, count=2, speed_range=(2, 4))
        particles.emit(self.x - 5, self.y + 15, CYAN_GLOW, count=1, speed_range=(1, 3))

        pts = [
            (self.x + self.width, self.y + 15),
            (self.x, self.y),
            (self.x + 10, self.y + 15),
            (self.x, self.y + self.height)
        ]
        pygame.draw.polygon(surface, CYAN_GLOW, pts)
        pygame.draw.polygon(surface, WHITE, pts, 2)
        pygame.draw.ellipse(surface, PURPLE_GLOW, (self.x + 18, self.y + 10, 14, 10))

class Bullet:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 16, 4)
        self.speed = 14

    def update_and_draw(self, surface):
        self.rect.x += self.speed
        pygame.draw.rect(surface, CYAN_GLOW, self.rect, border_radius=2)
        pygame.draw.rect(surface, WHITE, self.rect.inflate(-4, -2), border_radius=2)

class Enemy:
    def __init__(self):
        self.rect = pygame.Rect(SCREEN_WIDTH + 30, random.randint(40, SCREEN_HEIGHT - 60), 35, 25)
        self.speed = random.randint(4, 8)
        self.hp = 2

    def update_and_draw(self, surface):
        self.rect.x -= self.speed
        pts = [
            (self.rect.x, self.rect.y + 12),
            (self.rect.x + self.rect.width, self.rect.y),
            (self.rect.x + self.rect.width - 8, self.rect.y + 12),
            (self.rect.x + self.rect.width, self.rect.y + self.rect.height)
        ]
        pygame.draw.polygon(surface, NEON_RED, pts)
        pygame.draw.polygon(surface, WHITE, pts, 1)

# -------------------------------------------------------------
# LOJA KRYESORE
# -------------------------------------------------------------
def run_game():
    starfield = Starfield()
    particles = ParticleSystem()
    player = JetPlayer()
    bullets, enemies = [], []
    score = 0
    shoot_cooldown = 0
    enemy_spawn_timer = 0
    game_over = False

    while True:
        screen.fill(BG_COLOR)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_r and game_over:
                run_game()

        if not game_over:
            player.handle_movement()

            # Qitja me zë
            keys = pygame.key.get_pressed()
            shoot_cooldown += 1
            if keys[pygame.K_SPACE] and shoot_cooldown > 10:
                bullets.append(Bullet(player.x + player.width, player.y + 13))
                shoot_cooldown = 0
                if snd_laser:
                    snd_laser.play()  # 🔊 Sound Effect: Laser Shot

            enemy_spawn_timer += 1
            if enemy_spawn_timer > 35:
                enemies.append(Enemy())
                enemy_spawn_timer = 0

            for b in bullets[:]:
                b.update_and_draw(screen)
                if b.rect.x > SCREEN_WIDTH:
                    bullets.remove(b)

            for e in enemies[:]:
                e.update_and_draw(screen)

                # Laser Hit
                for b in bullets[:]:
                    if e.rect.colliderect(b.rect):
                        e.hp -= 1
                        bullets.remove(b)
                        particles.emit(b.rect.x, b.rect.y, CYAN_GLOW, count=6)
                        
                        if e.hp <= 0:
                            particles.emit(e.rect.centerx, e.rect.centery, NEON_RED, count=25)
                            particles.emit(e.rect.centerx, e.rect.centery, NEON_YELLOW, count=15)
                            enemies.remove(e)
                            score += 100
                            if snd_explosion:
                                snd_explosion.play()  # 🔊 Sound Effect: Shpërthim
                            break

                # Përplasje me lojtarin
                player_rect = pygame.Rect(player.x, player.y, player.width, player.height)
                if player_rect.colliderect(e.rect):
                    particles.emit(e.rect.centerx, e.rect.centery, NEON_RED, count=20)
                    enemies.remove(e)
                    player.health -= 25
                    if snd_hit:
                        snd_hit.play()  # 🔊 Sound Effect: Dëmtim
                    if player.health <= 0:
                        game_over = True

                if e.rect.x < -40:
                    enemies.remove(e)

        starfield.update_and_draw(screen)
        particles.update_and_draw(screen)

        if not game_over:
            player.draw(screen, particles)

            # HUD
            score_txt = font_ui.render(f"SCORE: {score}", True, CYAN_GLOW)
            screen.blit(score_txt, (25, 20))

            # Health Bar
            pygame.draw.rect(screen, (50, 50, 70), (SCREEN_WIDTH - 220, 25, 180, 18), border_radius=5)
            health_width = int((player.health / 100) * 180)
            if health_width > 0:
                pygame.draw.rect(screen, NEON_RED if player.health < 30 else CYAN_GLOW, (SCREEN_WIDTH - 220, 25, health_width, 18), border_radius=5)
            pygame.draw.rect(screen, WHITE, (SCREEN_WIDTH - 220, 25, 180, 18), 2, border_radius=5)
        else:
            over_txt = font_title.render("MISSION FAILED", True, NEON_RED)
            score_final = font_ui.render(f"Final Score: {score}", True, WHITE)
            restart_txt = font_ui.render("Shtyp [ R ] për të luajtur përsëri", True, CYAN_GLOW)
            
            screen.blit(over_txt, (SCREEN_WIDTH//2 - over_txt.get_width()//2, SCREEN_HEIGHT//2 - 60))
            screen.blit(score_final, (SCREEN_WIDTH//2 - score_final.get_width()//2, SCREEN_HEIGHT//2 + 10))
            screen.blit(restart_txt, (SCREEN_WIDTH//2 - restart_txt.get_width()//2, SCREEN_HEIGHT//2 + 50))

        pygame.display.flip()
        clock.tick(60)

run_game()