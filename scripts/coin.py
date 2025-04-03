import pygame
from random import random, randint
from math import sin, cos, pi

class EnergyCoin:
    def __init__(self, pos, r):
        self.pos = pos[0] + r, pos[1] + r
        self.r = r
        self.particles = [] # x, y, vx, vy, r, time of life
        self.rect = pygame.Rect(self.pos[0] - r, self.pos[1] - r, 2 * r, 2 * r)
        self.big_rect = pygame.Rect(self.pos[0] - 2 * r, self.pos[1] - 2 * r, 4 * r, 4 * r)
        
        self.circle_color = (52, 205, 252)
        self.particle_color = (10, 255, 248)

    def update(self, app):
        for p in self.particles.copy():
            p[0] += p[2]
            p[1] += p[3]            
            p[5] -= 1
            if p[5] < 0:
                self.particles.remove(p)
        if random() < .2:
            speed = 1
            angle = random() * 2 * pi
            vx = speed * cos(angle)
            vy = speed * sin(angle)
            r = randint(1, 3)
            t = randint(1, 60)
            self.particles.append([*self.pos, vx, vy, r, t])
        if self.rect.colliderect(app.main_player.get_rect()):
            self.effect(app)
            
    def effect(self, app):
        app.rigidbodies.remove(self)
        app.main_player.attack_energy = min(app.main_player.max_attack_energy, app.main_player.attack_energy + app.main_player.max_attack_energy // 2)

    def render(self, surf, camera):
        # delta = self.r * 2
        # if (-delta < self.pos[0] - camera[0] < surf.get_width() + delta) and (-delta < self.pos[1] - camera[1] < surf.get_height() + delta):
        for p in self.particles:
            pygame.draw.circle(surf, self.particle_color, (p[0] - camera[0], p[1] - camera[1]), p[4])
        pygame.draw.circle(surf, self.circle_color, (self.pos[0] - camera[0], self.pos[1] - camera[1]), self.r)

    def get_rect(self):
        return self.big_rect
        


class HealthCoin(EnergyCoin):
    def __init__(self, pos, r):
        super().__init__(pos, r)
        self.circle_color = (195, 17, 17)
        self.particle_color = (255, 7, 7)

    def effect(self, app):
        app.rigidbodies.remove(self)
        app.main_player.hp = min(app.main_player.hp + app.main_player.max_hp // 2, app.main_player.max_hp)
