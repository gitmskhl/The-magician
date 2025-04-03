import pygame
from math import cos, sin, pi
from random import random, randint


class LightBall:
    def __init__(self, player):
        self.t = 0
        self.dt = .1
        self.x = self.y = 0
        self.ballr = player.get_rect().width // 6
        self.R = player.get_rect().height
        self.particles = []
        self.particle_color = (255, 147, 41)#(255, 255, 0)
        self.circle_color = (255, 147, 41)#(255, 255, 0)

    def reset(self):
        self.particles = []
        self.t = 0

    def update(self, player):
        self.t += self.dt
        if self.t > 6.28: self.t = 0
        rect = player.get_rect()
        self.x = rect.centerx + self.R * cos(self.t)
        self.y = rect.centery + self.R * sin(self.t)
        
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
            self.particles.append([self.x, self.y, vx, vy, r, t])
    
    def render(self, surf, camera):
        for p in self.particles:
            pygame.draw.circle(surf, self.particle_color, (p[0] - camera[0], p[1] - camera[1]), p[4])
        pygame.draw.circle(surf, self.circle_color, (self.x - camera[0], self.y - camera[1]), self.ballr)

