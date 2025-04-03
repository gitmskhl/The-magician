import pygame
import sys
from random import random, randint
from math import sin, cos, pi
from .consts import window_size

class Particle:
    def __init__(self, center, distance):
        self.center = list(center)
        self.distance = distance
        self.r = random() * 4
        self.died = False
        self.t = 0
        self.dt = 1e-2

    def update(self):
        self.t += self.dt
        if self.t > 6.28:
            self.t = 0
        self.x = self.center[0] + self.distance * cos(self.t)
        self.y = self.center[1] + self.distance * sin(self.t)
        self.distance -= 1e-1
        if self.distance < 0:
            self.died = True
    
    def render(self, surf, camera):
        pygame.draw.circle(surf, (79, 14, 255), (self.x - camera[0], self.y - camera[1]), self.r)

class Portal:
    def __init__(self, center, r):
        self.center = list(center)
        self.r = r
        self.inside_r = self.r * .9
        self.r_max = self.r * 4
        self.particles = []

    def update(self):
        if random() < .1:
            particle = Particle(
                center=self.center, 
                distance=self.r + random() * (self.r_max - self.r)
            )
            self.particles.append(particle)
        for p in self.particles.copy():
            p.update()
            if p.died:
                self.particles.remove(p)
            
    def render(self, surf, camera):
        x_left = self.center[0] - self.r_max - camera[0]
        x_right = self.center[0] + self.r_max - camera[0]
        y_up = self.center[1] - self.r_max - camera[1]
        y_down = self.center[1] + self.r_max - camera[1]
        if x_right < 0 or x_left > window_size[0] or y_down < 0 or y_up > window_size[1]: return
        for p in self.particles:
            p.render(surf, camera)
        pos = (self.center[0] - camera[0], self.center[1] - camera[1])
        pygame.draw.circle(surf, (255, 0, 178), pos, self.r)
        pygame.draw.circle(surf, (0, 0, 0), pos, self.inside_r)
        