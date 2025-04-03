import pygame
from .consts import window_size

class IrisTransition:
    def __init__(self, period, expand=True):
        self.period = self.timer = period
        self.epxand = expand
        self.finished = False
        self.R_max = max(window_size) // 2 + 10
        self.R = 0 if self.epxand else self.R_max
        self.surf = pygame.Surface(window_size, pygame.SRCALPHA)

    def update(self):
        self.timer = max(0, self.timer - 1)
        if self.timer == 0: 
            self.finished = True
            return
        if self.epxand:
            self.R = self.R_max * (1 - self.timer / self.period)
        else:
            self.R = self.R_max * self.timer / self.period
        
    def render(self, surf):
        if self.finished: return
        self.surf.fill((0, 0, 0))
        pygame.draw.circle(self.surf, (0, 0, 0, 0), (window_size[0] // 2, window_size[1] // 2), self.R)
        surf.blit(self.surf, (0, 0))

    def reset(self):
        self.timer = self.period
        self.finished = False